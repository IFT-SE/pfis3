from algorithmsLexicalBase import LexicalBase
from gensim import models

class TFIDF(LexicalBase):
    def __init__(self, langHelper, name, fileName, dbFilePath, includeTop = False):
        LexicalBase.__init__(self, langHelper, name, fileName, dbFilePath, includeTop)
            
    def getModel(self):
        # Initialize the model using the corpus
        return models.TfidfModel(self.corpus)
        