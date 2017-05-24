import sqlite3

from predictiveAlgorithm import PredictiveAlgorithm
from gensim import similarities
from gensim.corpora.dictionary import Dictionary
from gensim.corpora.textcorpus import TextCorpus
from predictions import Prediction

class LexicalBase(PredictiveAlgorithm):
    def __init__(self, langHelper, name, fileName, dbFilePath, includeTop = False, numTopPredictions=0):
        PredictiveAlgorithm.__init__(self, langHelper, name, fileName, includeTop, numTopPredictions)
        self.lexicalHelper = LexicalHelper(dbFilePath, langHelper)
        
    def makePrediction(self, pfisGraph, navPath, navNumber):
        if navNumber < 1 or navNumber >= navPath.getLength():
            raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath')
        
        navToPredict = navPath.getNavigation(navNumber)
        sortedMethods = []
        
        if not navToPredict.isToUnknown():
            startTimestamp = 0
            endTimestamp = navToPredict.toFileNav.timestamp
            fromMethodFqn = navToPredict.fromFileNav.methodFqn
            methodToPredict = navToPredict.toFileNav.methodFqn
            
            # The reason we do the query from one extra backwards is because of
            # the duplication nonsense in PFIG
            # TODO: David to double check if this approach is feasible, do not
            # delete the below yet
#             if navPath.navigations[navNumber - 1].fromFileNav is not None:
#                 startTimestamp = navPath.navigations[navNumber - 1].fromFileNav.timestamp
            
            self.lexicalHelper.addDocumentsToCorpus(startTimestamp, endTimestamp, pfisGraph)
            model = self.getModel()
            fromMethodFqnEquivalent = pfisGraph.getFqnOfEquivalentNode(fromMethodFqn)
            sorted_sims = self.lexicalHelper.getSimilarityMatrix(model, fromMethodFqnEquivalent, True)
            
            mapMethodsToScore = {}
            
            for i in range(0, len(sorted_sims)):
                _, score = sorted_sims[i]
                sortedMethods.append(self.lexicalHelper.corpus.methodFqns[i])
                mapMethodsToScore[self.lexicalHelper.corpus.methodFqns[i]] = score

            patchToPredictEquivalent = pfisGraph.getFqnOfEquivalentNode(methodToPredict)
            if patchToPredictEquivalent not in mapMethodsToScore.keys():
                print "Warning: Cannot predict using TF-IDF: ", navNumber, methodToPredict
                return Prediction(navNumber, 999999, len(sortedMethods), 0,
                                    str(navToPredict.fromFileNav),
                                   str(navToPredict.toFileNav),
                                   navToPredict.toFileNav.timestamp)

            value = mapMethodsToScore[patchToPredictEquivalent]
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
            
    def getModel(self):
        return NotImplemented('getModel is not implemented.')
    
class LexicalHelper(object):    
    METHOD_DECLARATION_SCENT_QUERY = "SELECT action, target, referrer " \
        "FROM logger_log WHERE action in ('Method declaration scent', 'Changelog declaration scent') " \
        "AND timestamp >= ? AND timestamp < ? ORDER BY timestamp"
    
    def __init__(self, dbFilePath, langHelper):
        self.corpus = CorpusOfMethodContents()
        self.dbFilePath = dbFilePath
        self.langHelper = langHelper
    
    def addDocumentsToCorpus(self, startTimestamp, endTimestamp, pfisGraph):
        conn = sqlite3.connect(self.dbFilePath)
        conn.row_factory = sqlite3.Row
        
        c = conn.cursor()
        c.execute(self.METHOD_DECLARATION_SCENT_QUERY, [startTimestamp, endTimestamp])
        for row in c:
            target, referrer = \
                    self.langHelper.fixSlashes(row['target']), \
                    self.langHelper.fixSlashes(row['referrer'])
                    
            words = pfisGraph.getWordNodes_splitCamelAndStem(referrer)
            targetEquivalent = pfisGraph.getFqnOfEquivalentNode(target)
            self.corpus.addDocument(targetEquivalent, words)
            
        c.close()
        conn.close()
        
    def getSimilarityMatrix(self, model, queryMethodFqn, sort=False):

        # Build the index of documents we want to compare against. In this
        # case, it is the complete set of method declarations that the
        # programmer knows about so far
        corpus_model = model[self.corpus]
        index = similarities.SparseMatrixSimilarity(corpus_model, num_features = len(self.corpus.dictionary))

        # Build the query and covert it to the model space
        vec_bow = self.corpus.dictionary.doc2bow(self.corpus.getMethodContentsForFqn(queryMethodFqn))
        vec_model = model[vec_bow]

        # Perform the query and sort the results
        sims = index[vec_model]

        if sort:
            return sorted(enumerate(sims), key = lambda item: item[1], reverse = True)
        else:
            return list(enumerate(sims))

    def getSimilarityBetween(self, model, patchFqn1, patchFqn2):
        similarities = self.getSimilarityMatrix(model, patchFqn1)
        index = self.corpus.getPosition(patchFqn2)
        return similarities[index][1]


    
class CorpusOfMethodContents(TextCorpus):
    # TODO: Get rid of unnecessary indexing. Just keep a dictionary.
    def __init__(self):
        self.mapMethodFQNtoIndex = {}
        self.methodFqns = []
        self.methodContents = []
        TextCorpus.__init__(self)

    def getPosition(self, fqn):
        if fqn not in self.mapMethodFQNtoIndex.keys():
            raise Exception("Can't find FQN in corpus: ", fqn)
        return self.mapMethodFQNtoIndex[fqn]
        
    def addDocument(self, methodFqn, words):
        if methodFqn not in self.mapMethodFQNtoIndex:
            self.methodFqns.append(methodFqn)
            self.mapMethodFQNtoIndex[methodFqn] = len(self.methodFqns) - 1
            self.methodContents.append(words)
            self.dictionary.doc2bow(words, allow_update = True)
        else:
            self.methodContents[self.mapMethodFQNtoIndex[methodFqn]] = words
            self.dictionary = Dictionary()
            self.dictionary.add_documents(self.get_texts())
    
    def getMethodContentsForFqn(self, fqn):
        if fqn in self.mapMethodFQNtoIndex.keys():
            return self.methodContents[self.mapMethodFQNtoIndex[fqn]]
        return None
    
    def get_texts(self):
        for content in self.methodContents:
            yield content
        
        
