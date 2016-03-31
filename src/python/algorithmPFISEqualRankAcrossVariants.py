from algorithmPFIS import PFIS;

class PFISEqualRankAcrossVariants(PFIS):
    def __init(self, langHelper, name, fileName, history=False, goal = [],
                 decayFactor = 0.85, decayHistory = 0.9, numSpread = 2, includeTop= False, numTopPredictions=0):
        PFIS.__init__(langHelper, name, fileName, history, goal, decayFactor, decayHistory, includeTop, numTopPredictions)

    def computeTargetScores(self, mapNodesToActivation):
        mapNodesToFinalScores = {}
        targets = mapNodesToActivation.keys()

        for target in targets:
            if target not in mapNodesToFinalScores:
                equivalentTargets = self.__getEquivalentTargets(targets, target, lambda a,b: a == b)
                maxScore = -1
                for tgt in equivalentTargets:
                    if mapNodesToActivation[tgt] > maxScore:
                        maxScore = mapNodesToActivation[tgt]

                for item in equivalentTargets:
                    mapNodesToFinalScores[item] = maxScore

        return mapNodesToFinalScores


    def __getEquivalentTargets(self, collection, value, match):
        return [item for item in collection if match(item, value)]