import concurrent.futures
import itertools
import operator
import re

import requests
import wikipedia
from gensim.summarization.bm25 import BM25
from transformers import AutoTokenizer, AutoModelForQuestionAnswering, QuestionAnsweringPipeline

import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import nltk
from enum import Enum

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
			self.category = Question_Categories.UNSPECIFIED
		
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

    def search_pages(self, query):
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': query,
            'format': 'json'
        }
        res = requests.get(self.url, params=params)
        return res.json()

    def search_page(self, page_id):
        res = wikipedia.page(pageid=page_id)
        return res.content

    def search_page_based_on_title(self, title):
        res = wikipedia.page(title=title)
        return res.content

    def search(self, query, question):
        # TODO - Aici trebuie sa fie un string lung si intortocheat cu toate paginile concatenate
        # Si nimic altceva nu ar trebui returnat
        with concurrent.futures.ThreadPoolExecutor() as executor:
            process_list = []
            all_urls = search(question.question, tld="co.in", num=10, stop=5, pause=2)
            all_urls = [url for url in all_urls if 'en.wikipedia.' in url]
            if not all_urls:
                all_urls.append('https://en.wikipedia.org/wiki/Wikipedia:Unusual_articles')
            for url in all_urls:
                # TODO - no matches
                print(url)
                try:
                    req = urllib.request.Request(url, headers = headers)
                    page = urllib.request.urlopen(req)
                    fulltxt = str(page.read().decode('utf8'))
                    title = fulltxt.split('<title>')[1].split('</title>')[0]
                    # title = ''.join(url.split('wiki/')[1:]).split('#')[0]
                    print("Found title:", title)
                    process_list.append(executor.submit(self.search_page_based_on_title, title.encode('utf8')))
                    print("Appended!")
                except:
                    print('Something went very very wrong')
            docs = []
            for p in process_list:
                try:
                    docs_aux = self.post_process(p.result())
                    docs.append(docs_aux)
                except:
                    print("Stopped just in time!")
        return docs
        
        
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
        passages = list(itertools.chain(*map(self.preprocess, string_total)))
        print("step 1")
        corpus = [self.tokenize(p) for p in passages]
        print("step 2")
        self.bm25 = BM25(corpus)
        self.passages = [p for p in passages]

    def most_similar(self, question, topn=10):
        tokens = self.tokenize(question)
        scores = self.bm25.get_scores(tokens)
        pairs = [(s, i) for i, s in enumerate(scores)]
        pairs.sort(reverse=True)
        passages = [self.passages[i] for _, i in pairs[:topn]]
        return passages


class AnswerExtractor:

    def __init__(self, tokenizer, model):
        tokenizer = AutoTokenizer.from_pretrained(tokenizer)
        model = AutoModelForQuestionAnswering.from_pretrained(model)
        self.nlp = QuestionAnsweringPipeline(model=model, tokenizer=tokenizer)

    def extract(self, question, passages):
        answers = []
        for passage in passages:
            try:
                # passage = "".join(ch for ch in passage if ch.isalnum() or ch == ' ')
                answer = self.nlp(question=question, context=passage)
                answer['text'] = passage
                answers.append(answer)
            except KeyError:
                pass
        answers.sort(key=operator.itemgetter('score'), reverse=True)
        return answers