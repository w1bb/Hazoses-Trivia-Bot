import os

import spacy
from flask import Flask, render_template, jsonify, request

from src.components import QueryProcessor, DocumentRetrieval, PassageRetrieval, AnswerExtractor, Question, Question_Type, Question_W_T, Question_Categories

import json

app = Flask(__name__)
app.config["DEBUG"] = True

SPACY_MODEL = os.environ.get('SPACY_MODEL', 'en_core_web_sm')
QA_MODEL = os.environ.get('QA_MODEL', 'distilbert-base-cased-distilled-squad')
nlp = spacy.load(SPACY_MODEL, disable=['ner', 'parser', 'textcat'])
query_processor = QueryProcessor(nlp)
document_retriever = DocumentRetrieval()
passage_retriever = PassageRetrieval(nlp)
answer_extractor = AnswerExtractor(QA_MODEL, QA_MODEL)

@app.route('/sanity', methods=['GET'])
def check_sanity():
    response = jsonify({
        "status": "ok"
    })
    response.status_code = 200
    return response

@app.route('/question', methods=['POST'])
def question():
    print("CUTE ENTERED QUEST")
    question_contents = request.get_json()
    print("YEAH THAT WOULD BE FINE THX")
    json_l = question_contents
    print("json_l LOADED WITH VALUE", json_l)
    q = Question(json_l['question_text'] + " wikipedia", json_l['question_type'], json_l['question_category'], json_l['answer_choices'], json_l['answer_type'])
    query = query_processor.generate_query(q.question)
    string_total = document_retriever.search(query, q)
    passage_retriever.fit(string_total)
    passages = passage_retriever.most_similar(q.question)
    answers = answer_extractor.extract(q.question, passages) 
    accepted_ans = ""
    try:
        if q.question_type == Question_Type.direct_answer:
            accepted_ans = answers[0]['answer']
        else:
            found = False
            for ans in answers:
                for choice in q.choices:
                    if choice in ans['answers']:
                        accepted_ans = choice
                        found = True
                        break
                if found:
                    break
            if not found:
                print("NONE of the choices was correct, so choosing 1st")
                accepted_ans = q.choices[0]       
        
        print("These are the answers that were found: ")
        for ans in answers:
            print(ans['answer'], "with score", ans['score'])
    except:
        accepted_ans = 'Never gonna give you up!'
    answer= jsonify({
        "answer": accepted_ans
    })
    print("Accepted answer:",accepted_ans)
    answer.status_code=200
    return answer
