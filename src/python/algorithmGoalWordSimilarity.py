import sqlite3
import gensim
from algorithmTFIDF import TFIDF
from predictions import Prediction

class GoalWordSimilarity(TFIDF):
    SCENT_QUERY = "SELECT referrer FROM logger_log WHERE action LIKE '% declaration scent' " \
                  "AND target = ? LIMIT 1"

    def __init__(self, langHelper, name, fileName, dbFilePath, includeTop=False, numTopPredictions=0):
        TFIDF.__init__(self, langHelper, name, fileName, dbFilePath, includeTop, numTopPredictions)
        self.dbFilePath = dbFilePath


    def makePrediction(self, pfisGraph, navPath, navNumber):
        if navNumber < 1 or navNumber >= navPath.getLength():
            raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath')

        navToPredict = navPath.getNavigation(navNumber)
        sortedMethods = []

        if not navToPredict.isToUnknown():
            fromMethodFqn = navToPredict.fromFileNav.methodFqn

            conn = sqlite3.connect(self.dbFilePath)
            conn.row_factory = sqlite3.Row

            referrer = None

            c = conn.cursor()
            c.execute(self.SCENT_QUERY, [fromMethodFqn])
            for row in c:
                referrer = self.langHelper.fixSlashes(row['referrer'])
            c.close()
            conn.close()

            if referrer is None:
                raise Exception("Method body should not be none: ", fromMethodFqn)

            self.lexicalHelper.corpus.addDocument("goal", pfisGraph.getGoalWords())
            self.lexicalHelper.corpus.addDocument(fromMethodFqn, pfisGraph.getWordNodes_splitCamelAndStem(referrer))
            model = self.getModel()
            similarities = self.lexicalHelper.getSimilarityMatrix(model, fromMethodFqn)
            similarityScore = similarities[0][1]

            topPredictions = []
            if self.includeTop:
                topPredictions = self.getTopPredictions(sortedMethods, {})

            if similarityScore > 0.0:
                rank = 1
                print self.lexicalHelper.corpus.getMethodContentsForFqn(fromMethodFqn), similarityScore
            else:
                rank = 888888
            numTies = 1
            return Prediction(navNumber, rank, len(sortedMethods), numTies,
                              str(navToPredict.fromFileNav),
                              str(navToPredict.toFileNav),
                              navToPredict.toFileNav.timestamp,
                              topPredictions)


        return Prediction(navNumber, 999999, len(sortedMethods), 0,
                          str(navToPredict.fromFileNav),
                          str(navToPredict.toFileNav),
                          navToPredict.toFileNav.timestamp)





