from algorithmLexicalBase import LexicalBase
from gensim import models

class TFIDF(LexicalBase):
    def __init__(self, langHelper, name, fileName, dbFilePath, includeTop = False, numTopPredictions=0):
        LexicalBase.__init__(self, langHelper, name, fileName, dbFilePath,
                             includeTop, numTopPredictions=numTopPredictions)
            
    def getModel(self):
        # Initialize the model using the corpus
        return models.TfidfModel(self.lexicalHelper.corpus)
        