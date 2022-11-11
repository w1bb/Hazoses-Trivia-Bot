 import concurrent.futures
import itertools
import operator
import re
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import PorterStemmer
from nltk.stem.wordnet import WordNetLemmatizer

import requests
import wikipedia
import spacy
from gensim.summarization.bm25 import BM25
from transformers import AutoTokenizer, AutoModelForQuestionAnswering, QuestionAnsweringPipeline

import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import nltk
from enum import Enum

# tokenizer = PunktSentenceTokenizer()
tokenizer = Tokenizer()

nlp = spacy.load("en_core_web_sm")

try:
    from googlesearch import search
except ImportError:
    print("No module named 'google' found")

headers = {}
headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"

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


class QueryProcessor:

    def __init__(self, nlp, keep=None):
        self.nlp = nlp
        self.keep = keep or {'PROPN', 'NUM', 'VERB', 'NOUN', 'ADJ'}

    def generate_query(self, text):
        doc = self.nlp(text)
        query = ' '.join(token.text for token in doc if token.pos_ in self.keep)
        return query


class DocumentRetrieval:

    def __init__(self, url='https://en.wikipedia.org/w/api.php'):
        self.url = url

    def search(self, query, question):
        # TODO - Aici trebuie sa fie un string lung si intortocheat cu toate paginile concatenate
        # Si nimic altceva nu ar trebui returnat
        all_articles = []
        for url in search(question.question, tld="co.in", num=10, stop=1, pause=2):
            print(url)
            try:
                req = urllib.request.Request(url, headers = headers)
                page = urllib.request.urlopen(req)
                html = page.read().decode("utf-8")
                soup = BeautifulSoup(html, 'html.parser')
                # aux_str = ' '.join([x for x in soup.get_text().split('\n') if x != ''])
                aux_str = soup.get_text().encode("ascii", "ignore").decode()
                aux_str = ' '.join([x for x in aux_str.split('\t') if x != ''])
                all_articles.append(aux_str)
            except:
                print("Some problem in search, ignore!")
        print("This is the total string\n=============\n\n\n\n", all_articles)
        return all_articles
        

    def post_process(self, doc):
        pattern = '|'.join([
            '== References ==',
            '== Further reading ==',
            '== External links',
            '== See also ==',
            '== Sources ==',
            '== Notes ==',
            '== Further references ==',
            '== Footnotes ==',
            '=== Notes ===',
            '=== Sources ===',
            '=== Citations ===',
        ])
        p = re.compile(pattern)
        indices = [m.start() for m in p.finditer(doc)]
        min_idx = min(*indices, len(doc))
        return doc[:min_idx]


class PassageRetrieval:

    def __init__(self, nlp):
        self.tokenize = lambda text: [token.lemma_ for token in nlp(text)]
        self.bm25 = None
        self.passages = None

    def preprocess(self, doc):
        passages = [p for p in doc.split('\n') if p and not p.startswith('=')]
        return passages

    def fit(self, string_total):
        result = [p for p in ''.join(string_total).split('\n') if p]
        var = []
        for line in result:
        	var.extend(line.strip())
        lemma = WordNetLemmatizer()
        passages = map(lemma.lemmatize, var)
        print("step 1")
        corpus = [self.tokenize(p) for p in passages]
        print("step 2")
        self.bm25 = BM25(corpus)
        self.passages = [p for p in passages]

    def most_similar(self, question, topn=10):
        tokens = question.split()
        result = []
        for line in tokens:
        	result.extend([x + ' ' for x in line.strip()])
        lemma = WordNetLemmatizer()
        lem = map(lemma.lemmatize, result)
        scores = self.bm25.get_scores(tokens)
        pairs = [(s, i) for i, se)
        passages = [self.pa in enumerate(scores)]
        pairs.sort(reverse=Trussages[i] for _, i in pairs[:topn]]
        return passages


class AnswerExtractor:

    def __init__(self, tokenizer, model):
        tokenizer = AutoTokenizer.from_pretrained(tokenizer)
        model = AutoModelForQuestionAnswering.from_pretrained(model)
        self.nlp = QuestionAnsweringPipeline(model=model, tokenizer=tokenizer)

    def eimport concurrent.futures
import itertools
import operator
import re
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import PorterStemmer
from nltk.stem.wordnet import WordNetLemmatizer

import requests
import wikipedia
import spacy
from gensim.summarization.bm25 import BM25
from transformers import AutoTokenizer, AutoModelForQuestionAnswering, QuestionAnsweringPipeline

import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import nltk
from enum import Enum

lemma = WordNetLemmatizer()

nlp = spacy.load("en_core_web_sm")

try:
    from googlesearch import search
except ImportError:
    print("No module named 'google' found")

headers = {}
headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"

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


class QueryProcessor:

    def __init__(self, nlp, keep=None):
        self.nlp = nlp
        self.keep = keep or {'PROPN', 'NUM', 'VERB', 'NOUN', 'ADJ'}

    def generate_query(self, text):
        doc = self.nlp(text)
        query = ' '.join(token.text for token in doc if token.pos_ in self.keep)
        return query


class DocumentRetrieval:

    def __init__(self, url='https://en.wikipedia.org/w/api.php'):
        self.url = url

    def search(self, query, question):
        # TODO - Aici trebuie sa fie un string lung si intortocheat cu toate paginile concatenate
        # Si nimic altceva nu ar trebui returnat
        all_articles = []
        for url in search(question.question, tld="co.in", num=10, stop=1, pause=2):
            print(url)
            try:
                req = urllib.request.Request(url, headers = headers)
                page = urllib.request.urlopen(req)
                html = page.read().decode("utf-8")
                soup = BeautifulSoup(html, 'html.parser')
                # aux_str = ' '.join([x for x in soup.get_text().split('\n') if x != ''])
                aux_str = soup.get_text().encode("ascii", "ignore").decode()
                aux_str = ' '.join([x for x in aux_str.split('\t') if x != ''])
                all_articles.append(aux_str)
            except:
                print("Some problem in search, ignore!")
        print("This is the total string\n=============\n\n\n\n", all_articles)
        return all_articles
        

    def post_process(self, doc):
        pattern = '|'.join([
            '== References ==',
            '== Further reading ==',
            '== External links',
            '== See also ==',
            '== Sources ==',
            '== Notes ==',
            '== Further references ==',
            '== Footnotes ==',
            '=== Notes ===',
            '=== Sources ===',
            '=== Citations ===',
        ])
        p = re.compile(pattern)
        indices = [m.start() for m in p.finditer(doc)]
        min_idx = min(*indices, len(doc))
        return doc[:min_idx]


class PassageRetrieval:

    def __init__(self, nlp):
        self.tokenize = lambda text: [token.lemma_ for token in nlp(text)]
        self.bm25 = None
        self.passages = None

    def preprocess(self, doc):
        passages = [p for p in doc.split('\n') if p and not p.startswith('=')]
        return passages

    def fit(self, string_total):
        result = ' '.join(string_total).split('\n')
        # var = []
        passages = []
        for line in result:
        	aux = nltk.word_tokenize(line)
        	passages.append(' '.join([lemma.lemmatize(words, 'v') for words in aux]))
        #	var.extend(line.strip())
        # 
        # passages = map(lemma.lemmatize, var)
        
        print("step 1")
        corpus = [tokanizer.tokenize(p) for p in passages]
        print("step 2")
        self.bm25 = BM25(corpus)
        self.passages = [p for p in passages]

    def most_similar(self, question, topn=10):
        tokens = question.split()
        tokens = [lemma.lemmatize(token, 'v') for token in tokens]
        scores = self.bm25.get_scores(tokens)
        pairs = [(s, i) for i, s in enumerate(scores)]
        pairs.sort(reverse=True)
        passages = [self.passages[i] for _, i in pairs[:topn]]
        return passages


class AnswerExtractor:

    def __init__(self, tokenizer, model):
    self.nlp = QuestionAnsweringPipeline(model=model, tokenizer=tokenizer)

    def extract(self, question, passages):
        answers = []
        tokens = question.split()
        tokens = [lemma.lemmatize(token, 'v') for token in tokens]
        for passage in passages:
            print("Currently new passage")
            try:
                # passage = "".join(ch for ch in passage if ch.isalnum() or ch == ' ')
                # doc = npl(passage)
                print("CURRENT PASSAGE: ", passage)
                answer = self.nlp(question=tokens, context=passage)
                print("After 1")
                answer['text'] = passage
                print("After 2")
                answers.append(answer)
                print("After 3")
            except KeyError:
                pass
        answers.sort(key=operator.itemgetter('score'), reverse=True)
        return answersxtract(self, question, passages):
        answers = []
        for passage in passages:
            print("Currently new passage")