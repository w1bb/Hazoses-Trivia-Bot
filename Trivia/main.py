from bs4 import BeautifulSoup
from enum import Enum
import re
import nltk
import requests
from asyncio.events import BaseDefaultEventLoopPolicy
import urllib.request
import urllib.parse
import codecs
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import PorterStemmer
from nltk.stem.wordnet import WordNetLemmatizer
import math

try:
    from googlesearch import search
except ImportError:
    print("No module named 'google' found")

# nltk.download('omw-1.4')

lem = WordNetLemmatizer()
_LOG = True

def get_urls_for_question(question):
	result = search(question.question, tld="co.in", num=10, stop=10, pause=2)
	if _LOG == True:
		print("These are the found links: ", result)
	return result

def open_url(url_str):
	headers = {}
	headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
	req = urllib.request.Request(url_str, headers = headers)
	page = urllib.request.urlopen(req)
	soup = BeautifulSoup(page, 'html.parser')
	return soup

def eval_word(sentence, word, word_weight):
	split_sentence = [x for x in re.split("[ ,.!?;\"' / ]", sentence) if x]
	count_words = 0
	for ws in split_sentence:
		if ws == word:
			count_words += 1
	if count_words <= 0.1:
		return 0
	return math.log(1.7634 * count_words + 0.95487) * word_weight

def eval_all_words(sentence, wordlist):
	total = 0
	print("The sentence is: ", sentence)
	for [word, word_weight] in wordlist:
		aux = eval_word(sentence, word, word_weight)
		total += aux
	return total

class Question_W_T(Enum):
	WHAT = 1
	WHERE = 2
	WHO = 3
	WHEN = 4
	WHICH = 5

class Question_Type(Enum):
	direct_answer = 1
	multiple_choice = 2

class Question_Categories(Enum):
	HISTORY = 1
	GEOGRAPHY = 2
	MUSIC = 3
	GAMING = 4
	MOVIES = 5
	UNSPECIFIED = 6

class Question:
	def __init__(self):
		# Interpretarea intrebarii
		return
	
	def __init__(self, question, question_type, category, choices, answer_type):
		self.question = question
		self.words = [x for x in re.split("[ ,.!?;\"']", self.question) if x]
		tagged = nltk.pos_tag(self.words)
		self.useful_words = [x[0] for x in tagged if x[1] != "DT" and x[1] != "IN" and x[1] != "AT"]
		self.useful_words = [lem.lemmatize(x, "v") for x in self.useful_words]

		self.weighted_words = []
		for word in self.useful_words[1:]:
			self.weighted_words.append([lem.lemmatize(word, "v"), 1])

		if question_type == "direct_answer":
			self.question_type = Question_Type.direct_answer
		else:
			self.question_type = Question_Type.multiple_choice
		
		self.useful_words[0] = self.useful_words[0].lower()
		if self.useful_words[0] == "what":
			self.question_w = Question_W_T.WHAT
		elif self.useful_words[0] == "where":
			self.question_w = Question_W_T.WHERE
		elif self.useful_words[0] == "who":
			self.question_w = Question_W_T.WHO
		elif self.useful_words[0] == "when":
			self.question_w = Question_W_T.WHEN
		else:
			self.question_w = Question_W_T.WHICH

		category = category.lower()
		if category == "history":
			self.category = Question_Categories.HISTORY
		elif category == "geography":
			self.category = Question_Categories.GEOGRAPHY
		elif category == "music":
			self.category = Question_Categories.MUSIC
		elif category == "gaming":
			self.category = Question_Categories.GAMING
		elif category == "movies":
			self.category = Question_Categories.MOVIES
		else:
			self.category = Question_Categories.UNDEFINED
		
		self.choices = choices
		self.answer_type = answer_type

		if _LOG == True:
			print("Question type: ", self.question_type)
			print("Question_W type: ", self.question_w)
			print("Question_Cateory is: ", self.category)
			print("The words are: ", self.words)
			print("The word tags are: ", tagged)
			print("The good word are: ", self.useful_words)
			print("The weighted words are: ", self.weighted_words)

	def lookup_link(self, link):
		if _LOG == True:
			all_text = open_url(link).text.replace(".", " ")
			all_props = sent_tokenize(all_text.replace("\n", ". "))
			correct_props = []
			for prop in all_props:
				words_in_prop = [x.encode("ascii", "ignore").decode() for x in re.split("[ ,.!?;\"' / ]", prop) if x]
				words_in_prop = [lem.lemmatize(x, "v") for x in words_in_prop if x]
				prop = ' '.join(words_in_prop)
				if prop:
					correct_props.append([prop, eval_all_words(prop, self.weighted_words)])
			correct_props.sort(key = lambda x : x[1])
			with codecs.open("au.txt", "w", "utf-8") as fout:
				print(correct_props)
				# prop = "The Fall of Constantinople was the capture of the capital of the Byzantine Empire by the Ottoman Empire"
				# words_in_prop = [x.encode("ascii", "ignore").decode() for x in re.split("[ ,.!?;\"' / ]", prop) if x]
				# words_in_prop = [lem.lemmatize(x, "v") for x in words_in_prop if x]
				# prop = ' '.join(words_in_prop)
				# print(eval_all_words(prop, self.weighted_words))
		return

	def answer_question():
		return

def main():
	# nltk.download('averaged_perceptron_tagger')
	q = Question("When did the Fall of Constantinople take place?",
				 "direct_answer",
				 "History",
				 [],
				 "numeric")
	print(get_urls_for_question(q))
	q.lookup_link("https://en.wikipedia.org/wiki/Fall_of_Constantinople")

if __name__ == "__main__":
	main()