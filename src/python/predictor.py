from predictions import Predictions

class Predictor(object):
	def __init__(self, graph, navPath):
		self.graph = graph
		self.navPath = navPath
		self.navNumber = -1
		self.endTimeStamp = '0'

	def makeAllPredictions(self, algorithms, outputFolder, topPredictionsFolder=None):

		self.updateGraphByOneNavigation()

		if len(self.navPath.navigations) < 2:
			raise RuntimeError('makeAllPredictions: Not enough navigations to run predictive algorithms')

		# Build the output data structure
		results = {}
		for algorithm in algorithms:
			results[algorithm.name] = Predictions(algorithm.name, outputFolder, algorithm.fileName, algorithm.includeTop, topPredictionsFolder)

		totalPredictions = len(self.navPath.navigations) - 1

		for _ in range(1, totalPredictions + 1):
			self.updateGraphByOneNavigation()
			print 'Making predictions for navigation #' + str(self.navNumber) + ' of ' + str(totalPredictions)
			for algorithm in algorithms:
				results[algorithm.name].addPrediction(self.__makePrediction(algorithm))

		print 'Done making predictions.'
		print self.graph.printEntireGraphStats()
		return results

	def __makePrediction(self, predictiveAlgorithm):
		print '\tMaking predictions for ' + predictiveAlgorithm.name + '...'
		return predictiveAlgorithm.makePrediction(self.graph, self.navPath, self.navNumber)

	def updateGraphByOneNavigation(self):
		newEndTimestamp = 0

		if self.navNumber < self.navPath.getLength() - 1:
			self.navNumber += 1
			newEndTimestamp = self.navPath.navigations[self.navNumber].toFileNav.timestamp

		self.graph.updateGraphByOneNavigation(self.endTimeStamp, newEndTimestamp)

		self.endTimeStamp = newEndTimestamp