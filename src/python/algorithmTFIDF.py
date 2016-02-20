import sqlite3

from predictiveAlgorithm import PredictiveAlgorithm
from gensim import models, similarities
from gensim.corpora.dictionary import Dictionary
from gensim.corpora.textcorpus import TextCorpus
from predictions import Prediction

class TFIDF(PredictiveAlgorithm):
    
    METHOD_DECLARATION_SCENT_QUERY = "SELECT action, target, referrer " \
        "FROM logger_log WHERE action = 'Method declaration scent' " \
        "AND timestamp >= ? AND timestamp < ? ORDER BY timestamp DESC"

    def __init__(self, langHelper, name, fileName, dbFilePath, includeTop = False):
        PredictiveAlgorithm.__init__(self, langHelper, name, fileName, includeTop)
        self.dbFilePath = dbFilePath
        self.corpus = TFIDFCorpus()
        
    def makePrediction(self, pfisGraph, navPath, navNumber):
        if navNumber < 1 or navNumber >= navPath.getLength():
            raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath')
        
        navToPredict = navPath.navigations[navNumber]
        sortedMethods = []
        
        if not navToPredict.isToUnknown():
            startTimestamp = 0
            endTimestamp = navToPredict.toFileNav.timestamp
            fromMethodFqn = navToPredict.fromFileNav.methodFqn
            methodToPredict = navToPredict.toFileNav.methodFqn
            
            # The reason we do the query from one extra backwards is because of
            # the duplication nonsense in PFIG
#             if navPath.navigations[navNumber - 1].fromFileNav is not None:
#                 startTimestamp = navPath.navigations[navNumber - 1].fromFileNav.timestamp
            
            conn = sqlite3.connect(self.dbFilePath)
            conn.row_factory = sqlite3.Row
            
            c = conn.cursor()
            c.execute(self.METHOD_DECLARATION_SCENT_QUERY, [startTimestamp, endTimestamp])
            for row in c:
                target, referrer = \
                        self.langHelper.fixSlashes(row['target']), \
                        self.langHelper.fixSlashes(row['referrer'])
                        
                words = pfisGraph.getWordNodes_splitCamelAndStem(referrer)
                self.corpus.addDocument(target, words)
                
            c.close()
            conn.close()
            
            # Initialize the model using the corpus
            tfidfModel = models.TfidfModel(self.corpus)
            
            # Build the query and covert it to the tf-idf space
            vec_bow = self.corpus.dictionary.doc2bow(self.corpus.getMethodContentsForFqn(fromMethodFqn))
            vec_tfidf = tfidfModel[vec_bow]
            
            # Build the index of documents we want to compare against. In this
            # case, it is the complete set of method declarations that the 
            # programmer knows about so far
            corpus_tfidf = tfidfModel[self.corpus]
            index = similarities.SparseMatrixSimilarity(corpus_tfidf, num_features = len(self.corpus.dictionary))
            
            # Perform the query and sort the results
            sims = index[vec_tfidf]
            sorted_sims = sorted(enumerate(sims), key = lambda item: item[1], reverse = True)
            
            mapMethodsToScore = {}
            
            for i in range(0, len(sorted_sims)):
                _, score = sorted_sims[i]
                sortedMethods.append(self.corpus.methodFqns[i])
                mapMethodsToScore[self.corpus.methodFqns[i]] = score
                
            value = mapMethodsToScore[methodToPredict]
            firstIndex = self.getFirstIndex(sortedMethods, mapMethodsToScore, value)
            lastIndex = self.getLastIndex(sortedMethods, mapMethodsToScore, value)
            numTies = lastIndex - firstIndex + 1
            rankWithTies =  self.getRankConsideringTies(firstIndex + 1, numTies)
            
            topPredictions = []
            if self.includeTop:
                topPredictions = self.getTopPredictions(sortedMethods, mapMethodsToScore)
                
            return Prediction(navNumber, rankWithTies, len(sortedMethods), numTies,
                       str(navToPredict.fromFileNav), 
                       str(navToPredict.toFileNav),
                       navToPredict.toFileNav.timestamp,
                       topPredictions)
            
        return Prediction(navNumber, 999999, len(sortedMethods), 0,
               str(navToPredict.fromFileNav), 
               str(navToPredict.toFileNav),
               navToPredict.toFileNav.timestamp)
        
class TFIDFCorpus(TextCorpus):
    
    def __init__(self):
        self.mapMethodFQNtoIndex = {}
        self.methodFqns = []
        self.methodContents = []
        TextCorpus.__init__(self)
        
    def addDocument(self, methodFqn, words):
        if methodFqn not in self.mapMethodFQNtoIndex:
            self.methodFqns.append(methodFqn)
            self.mapMethodFQNtoIndex[methodFqn] = len(self.mapMethodFQNtoIndex) - 1
            self.methodContents.append(words)
            self.dictionary.doc2bow(words, allow_update = True)
        else:
            self.methodContents[self.mapMethodFQNtoIndex[methodFqn]] = words
            self.dictionary = Dictionary()
            self.dictionary.add_documents(self.get_texts())
    
    def getMethodContentsForFqn(self, fqn):
        return self.methodContents[self.mapMethodFQNtoIndex[fqn]]
    
    def get_texts(self):
        for content in self.methodContents:
            yield content
        
        
        