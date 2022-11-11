import os

import spacy
from flask import Flask, render_template, jsonify, request

from components import QueryProcessor, DocumentRetrieval, PassageRetrieval, AnswerExtractor, Question, Question_Type, Question_W_T, Question_Categories

SPACY_MODEL = os.environ.get('SPACY_MODEL', 'en_core_web_sm')
QA_MODEL = os.environ.get('QA_MODEL', 'distilbert-base-cased-distilled-squad')
nlp = spacy.load(SPACY_MODEL, disable=['ner', 'parser', 'textcat'])
query_processor = QueryProcessor(nlp)
document_retriever = DocumentRetrieval()
passage_retriever = PassageRetrieval(nlp)
answer_extractor = AnswerExtractor(QA_MODEL, QA_MODEL)

def main():
    q = Question("When did Abraham Lincoln die?",
	         "direct_answer", "History", [], "numeric")
    query = query_processor.generate_query(q.question)
    print("Ended query")
    string_total = document_retriever.search(query, q)
    print("Ended docs")
    passage_retriever.fit(string_total)
    print("Ended passage_retriever")
    passages = passage_retriever.most_similar(q.question)
    print("Ended passages with result: ", passages)
    answers = answer_extractor.extract(q.question, passages)
    print("Ended answers", answers)
    # print(jsonify(answers))

if __name__ == '__main__':
    main()