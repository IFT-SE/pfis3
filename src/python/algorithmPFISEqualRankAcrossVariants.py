from algorithmPFIS import PFIS;

class PFISEqualRankAcrossVariants(PFIS):
    def __init(self, langHelper, name, fileName, history=False, goal = [],
                 decayFactor = 0.85, decayHistory = 0.9, numSpread = 2, includeTop= False, numTopPredictions=0):
        PFIS.__init__(langHelper, name, fileName, history, goal, decayFactor, decayHistory, includeTop, numTopPredictions)

    def computeTargetScores(self, graph, mapNodesToActivation):
        mapNodesToFinalScores = {}
        targets = mapNodesToActivation.keys()

        for target in targets:
            if target not in mapNodesToFinalScores:
                equivalentTargets = graph.getVariantNodes(target)
                equivalentTargets.append(target)

                maxScore = mapNodesToActivation[target]
                for tgt in equivalentTargets:
                    if mapNodesToActivation[tgt] > maxScore:
                        maxScore = mapNodesToActivation[tgt]

                for item in equivalentTargets:
                    mapNodesToFinalScores[item] = maxScore

                if len(equivalentTargets) > 1:
                    for item in equivalentTargets:
                        print item, " ", mapNodesToActivation[item], " ", mapNodesToFinalScores[item]

        return mapNodesToFinalScores