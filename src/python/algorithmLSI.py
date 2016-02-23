from algorithmLexicalBase import LexicalBase
from gensim import models

class LSI(LexicalBase):
    def __init__(self, langHelper, name, fileName, dbFilePath, numTopics = 200, includeTop=False):
        LexicalBase.__init__(self, langHelper, name, fileName, dbFilePath, includeTop=includeTop)
        self.numTopics = numTopics
        
    def getModel(self):
        # Initialize the model using the corpus
        return models.LsiModel(self.lexicalHelper.corpus, num_topics=self.numTopics)