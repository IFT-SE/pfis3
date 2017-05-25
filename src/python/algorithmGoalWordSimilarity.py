import sqlite3
from algorithmTFIDF import TFIDF
from predictions import Prediction

class GoalWordSimilarity(TFIDF):
    SCENT_QUERY = "SELECT referrer FROM logger_log WHERE action LIKE '% declaration scent' " \
                  "AND target = ? LIMIT 1"
    GOAL_WORDS_FQN_KEY = "GOAL"

    def __init__(self, langHelper, name, fileName, dbFilePath, includeTop=False, numTopPredictions=0):
        TFIDF.__init__(self, langHelper, name, fileName, dbFilePath, includeTop, numTopPredictions)
        self.dbFilePath = dbFilePath


    def makePrediction(self, pfisGraph, navPath, navNumber):
        if navNumber < 1 or navNumber >= navPath.getLength():
            raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath')

        navToPredict = navPath.getNavigation(navNumber)
        sortedMethods = []

        if not navToPredict.isToUnknown():
            navToPatchFqn = navToPredict.toFileNav.methodFqn

            if self.langHelper.isOutputFqn(navToPatchFqn):
                return Prediction(navNumber, 999999, len(sortedMethods), 0,
                                  str(navToPredict.fromFileNav),
                                  str(navToPredict.toFileNav),
                                  navToPredict.toFileNav.timestamp)


            conn = sqlite3.connect(self.dbFilePath)
            conn.row_factory = sqlite3.Row

            referrer = None

            c = conn.cursor()
            c.execute(self.SCENT_QUERY, [navToPatchFqn])
            for row in c:
                referrer = self.langHelper.fixSlashes(row['referrer'])
            c.close()
            conn.close()

            if referrer is None:
                raise Exception("Method body should not be none: ", navToPatchFqn)

            self.lexicalHelper.corpus.addDocument(self.GOAL_WORDS_FQN_KEY, pfisGraph.getGoalWords())
            self.lexicalHelper.corpus.addDocument(navToPatchFqn, pfisGraph.getWordNodes_splitCamelAndStem(referrer))
            model = self.getModel()
            similarityScore = self.lexicalHelper.getSimilarityBetween(model, navToPatchFqn, self.GOAL_WORDS_FQN_KEY)


            topPredictions = []
            if self.includeTop:
                topPredictions = self.getTopPredictions(sortedMethods, {})

            if similarityScore > 0.0:
                return Prediction(navNumber, 1, 1, 1,
                              str(navToPredict.fromFileNav),
                              str(navToPredict.toFileNav),
                              navToPredict.toFileNav.timestamp,
                              topPredictions)

        return Prediction(navNumber, 999999, len(sortedMethods), 0,
                          str(navToPredict.fromFileNav),
                          str(navToPredict.toFileNav),
                          navToPredict.toFileNav.timestamp)





