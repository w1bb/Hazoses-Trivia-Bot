from bs4 import BeautifulSoup
import re
import nltk
from enum import Enum

_LOG = True

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

        if _LOG == True:
            print("Question type: ", self.question_type)
            print("Question_W type: ", self.question_w)
            print("Question_Cateory is: ", self.category)
            print("The words are: ", self.words)
            print("The word tags are: ", tagged)
            print("The good word are: ", self.useful_words)

    def answer_question():
        return

def main():
    # nltk.download('averaged_perceptron_tagger')
    q = Question("When did the Fall of Constantinopole take place?",
                 "direct_answer",
                 "History",
                 [],
                 "numeric")

if __name__ == "__main__":
    main()