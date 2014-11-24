from collections import defaultdict, Counter
import argparse
import math
import os
import re
import collections
import pickle
import sys
import string
import parse_compress #code to parse sentences and delete based on 


class TfIdf:


	def __init__(self):
		"""Open and load pickl files containing dictionary"""
		all_corpora = open('pickl/allCorpora')

		all_pos_corpora = open('pickl/allPoSCorpora')

		all_phrases = open('pickl/allPhrases')

		self.all_corpora = pickle.load(all_corpora) #will be a dictionary pointing to the corpus file, each of which is a dictionary of the all the word counts.
		#self.all_pos_corpora = pickle.load(all_pos_corpora)
		self.all_phrases = pickle.load(all_phrases)

		all_corpora.close()
		#all_pos_corpora.close()
		all_phrases.close()

		#store url, if any
		self.url = ''

	def has_url(self):
		return self.url != ''
	
	def get_input_text(self, filename):
		"""Return the text within a file for summarizing."""
		try:
			my_file = open(filename, 'r')
			text = ''
			for line in my_file:
				text = text + line
			return text
		except IOError:
			print 'ERROR: Invalid filename'
			return False

	def read_input_text(self, input_text):
		"""preprocesses the input_text. removes and stores the url, and also fixes any ascii character bugs"""
		#first search for a url, store it and remove it from the input text
		m = re.search('http[s]?://(?:[a-zA-Z]|[0-9]|[~$-_@.&#+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', input_text) #we are assuming only 1 url per input - makes sense in the context of twitter
		if m: #if there is a url
			self.url = str(m.group(0))
			#print self.url
			input_text = input_text.replace(self.url, '')
		tree_tags = parse_compress.tag(input_text) #maybe move somewhere else in the end

		###for orestis for ascii characters

		return input_text

	def tf_idf(self, input_text):
		"""returns a tf-idf dictionary for each term in input_text"""

		tfidf_dict = {}
		#create a word Dictionary for the input text
		input_word_dictionary = defaultdict(int)
		# input_text = re.sub('([.,!?()])', r' \1 ', input_text) #regex code to add a space between punctuation
		input_text = input_text.split()
		for w in input_text:
			word = w.strip("'.,!?;:'*()")
			input_word_dictionary[string.lower(word)] +=1

		# term frequency * log (# files total / # files with term)
		for w in input_text:
			#print "\n",word
			word = w.strip("'.,!?;:'*()")

			tf = input_word_dictionary[string.lower(word)]
			#print "tf", tf

			num_files = 0
			for corpus in self.all_corpora:
				if word in self.all_corpora[corpus]:
					num_files +=1
			if num_files ==0: #if the word isn't in any of the corpora
				num_files = .1 #assume it is important
			idf = math.log((len(self.all_corpora)/(num_files)))

			TfIdf = tf * idf
			#print 'tf', tf, "| idf", idf

			tfidf_dict[string.lower(word)] = TfIdf
		return tfidf_dict

	def total_sent_score(self, input_text, scores):
		"""Compute the total tf-idf score of a sentence by summing the scores of each word in each sentence"""
		# input_text = re.sub('([.,!?()])', r' \1 ', input_text) #I took these two lines from top_sentences

		#print "\nThe input text is:\n", input_text, "\n"

		sentences = re.split('(?<=[.!?-]) +', input_text)

		#top_sentences = Counter()
		top_sentences = []

		for index, sentence in enumerate(sentences):
			words = sentence.split()
			total_score = 0.0
			num_words = 0.0
			word_list = []
			if len(sentence) > 1: #to avoid single punctuation marks or one-word sentences.
				for word in words:
					num_words += 1
					score = scores[string.lower(word.strip("'.,!?;:'*()"))]
					total_score += score
					word_list.append((word, score))

				#if num_words != 0: top_sentences[sentence] = (total_score / num_words, index)
				#if num_words != 0: top_sentences.append((sentence, total_score / num_words, index))
				if num_words != 0: top_sentences.append((word_list, total_score / num_words, index))
				# top_sentences[sentence] = total_score

		"""returns all the sentences with a score and index"""

		return top_sentences 
		#return top_sentences.most_common(num_sentences)

		
	def delete_phrases(self, sentences_in_lists, input_text,scores):
		"""Delete words and (like total_sent_score) returns sentences with score and index."""
		#sentences_in_lists = parse_compress.drop_phrases(sentences_in_lists)
		#print "before: {0}".format(sentences_in_lists)
		parse_compress.simple_drop(sentences_in_lists, input_text, scores)
		#print "after: {0}".format(sentences_in_lists)

	def get_dictionary_paraphrase(self, unigram): 
		"""short method just to keep punctuation and capitalization uniform after searching through dictionary"""
		r_punc = ''
		l_punc = ''
		if unigram.rstrip(".'.,!?;:'*)]") != unigram: #if there exists a punctuation on the right
			r_punc = unigram[-1]
		if unigram.lstrip(".'.,!?;:'*([") != unigram: #if there exists a punctuation on the left
			l_punc = unigram[-1]
		new_unigram = self.all_phrases[unigram.strip(".'.,!?;:'*()[]").lower()] #gets the unigram from dictionary

		if unigram[0].lower() != unigram[0]: #check if capitalized
			new_unigram = new_unigram.capitalize() #then also capitalize the new unigram
		new_unigram = l_punc + new_unigram + r_punc
		return new_unigram

	def compress_sentences(self, sentences_in_lists, out_length):
		"""Compress and return the sentences within our desired length."""
		sentences = []

		"""unigram compression"""
		for sent_list in sentences_in_lists:
			max_changes = len(sent_list[0])/2 #the greatest number of changes we want to make in each sentence
			unigrams = []
			changes = 0
			new_sent = []

			for index, word in enumerate(sent_list[0]):
				if word[0] == '': continue
				unigrams.append((word[0], word[1], index))
			unigrams.sort(key = lambda x:x[1]) #sort based on score
			for unigram in unigrams:
				#print unigram

				if changes > max_changes: break
				unigram_uniform = unigram[0].strip(".'.,!?;:'*()[]").lower() #stripped and lowercased to check in the dictionary
				if unigram_uniform in self.all_phrases:
					print "changing:", unigram[0], ">>>", self.get_dictionary_paraphrase(unigram[0])
					unigram = (self.get_dictionary_paraphrase(unigram[0]), unigram[1], unigram[2])
					changes += 1
				new_sent.append(unigram)

			new_sent.sort(key = lambda x:x[2])
			sentence = ''
			for ind,i in enumerate(new_sent):
				word = i[0]
				sentence += word
				if ind < len(new_sent):
					sentence += ' '

			sentences.append((sentence, sent_list[1], sent_list[2]))

		# Ordering and printing to correct length.
		output = []
		total_length = 0
		sentences.sort(key = lambda x:x[1], reverse = True)

		for sentence in sentences:
			length = len(sentence[0]) + 1 #+1 for space before sentences
			if total_length + length > out_length: continue
			total_length += length

			# Insert sentences in the correct order.
			counter = 0
			for i in range(len(output)): 
				if output[i][2] < sentence[2]: 
					counter += 1
			output.insert(counter, sentence)

		# Create the output string, append url

		out_string = ''
		for i in output: 
			out_string += i[0]
		out_string += self.url

		return out_string

if __name__=='__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-text', type=str, help='input text', required=False)
	parser.add_argument('-textfile', type=str, help='boolean if given input file', required=False)
	parser.add_argument('-length', type=str, help='length of final compression', required=False, default=134) #140 for twitter, -6 for #CS73 hashtag+space
	args = parser.parse_args()

	if args.text is None and args.textfile is None:
		print "Either command line text or a text file is required!"
		sys.exit() 

	print "Parsing Corpus..."
	program = TfIdf()
	if args.textfile != None:
		print 'Opening Input Text File...'
		text = program.get_input_text(args.textfile)
		args.text = text
		if text == False:
			sys.exit() 
	print "Calculating Score..."

	# args.text = args.text.lower() #added to make lowercase

	processed_text = program.read_input_text(args.text)
	scores = program.tf_idf(processed_text)
	# print scores

	summary2 = program.total_sent_score(processed_text, scores)
	program.delete_phrases(summary2, processed_text, scores)
	#print summary2
	if program.has_url(): length = args.length - 23 #-23 for link+space(twitter condenses all links to max 22 characters)
	else: length = args.length
	output = program.compress_sentences(summary2, length)

	print "\nurl:"
	print program.url
	print 'The output text is:'
	print output
