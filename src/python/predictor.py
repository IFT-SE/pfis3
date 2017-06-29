from predictions import Predictions
from navpath import NavigationPath

class Predictor(object):
	def __init__(self, graph, navPath, outputFolderPath, topPredictionsPath=None):
		self.graph = graph
		self.navPath = navPath
		self.outputFolder = outputFolderPath
		self.topPredictionsFolder = topPredictionsPath
		self.navNumber = 0
		self.endTimeStamp = '0'

	def makeAllPredictions(self, algorithms):
		self.updateGraphByOneNavigation()
		if self.navPath.getLength() < 2:
			raise RuntimeError('makeAllPredictions: Not enough navigations to run predictive algorithms')

		# Build the output data structure
		results = {}
		for algorithm in algorithms:
			results[algorithm.name] = Predictions(algorithm.name, self.outputFolder, algorithm.fileName,
			                                      algorithm.includeTop, self.topPredictionsFolder)

		for _ in range(0, self.navPath.getLength()-1):
			self.navNumber += 1
			print 'Making predictions for navigation #' + str(self.navNumber) + ' of ' + str(self.navPath.getLength())
			self.updateGraphByOneNavigation()
			self.__addUnseenButKnownPatchIfAny(self.navNumber)
			for algorithm in algorithms:
				prediction = algorithm.makePrediction(self.graph, self.navPath, self.navNumber)
				results[algorithm.name].addPrediction(prediction)
			self.__removeTemporarilyAddedNodeIfAny(self.navNumber)
			print "-----------------------------------------------"

		print 'Done making predictions.'
		print self.graph.printEntireGraphStats()
		return results

	def updateGraphByOneNavigation(self):
		newEndTimestamp = self.navPath.getNavigation(self.navNumber).toFileNav.timestamp
		self.graph.updateGraphByOneNavigation(self.endTimeStamp, newEndTimestamp)
		self.endTimeStamp = newEndTimestamp

	def __addUnseenButKnownPatchIfAny(self, navNumber):
		# If patch is not seen before by a programmer, he/she might still know about it based on previous variants. This is what PFIS-V models.
		# So, we add that "unseen, yet known" patch to graph temporarily, for the sake of still predicting it.
		# Such temp nodes are then removed after prediction is made.
		# The update graph after the nav takes care of putting the actual node back into the graph.
		if self.navPath.getNavPathType() == NavigationPath.PFIS_V and self.navPath.ifNavToUnseenPatch(navNumber):
			actualNavigation = self.navPath.getNavigation(navNumber).toFileNav
			if self.graph.containsNode(actualNavigation.methodFqn):
				print "Warning: Unseen method already exists in graph: ", actualNavigation.methodFqn, navNumber
			else:
				mostRecentSimilarNav = self.navPath.getPriorNavToSimilarPatchIfAny(navNumber)
				if mostRecentSimilarNav is not None:
					self.graph.setTemporaryMode(value=True)
					print "Add temporary node {}: similar to {}".format(actualNavigation.methodFqn, mostRecentSimilarNav.methodFqn)
					self.graph.cloneNode(actualNavigation.methodFqn, mostRecentSimilarNav.methodFqn)

	def __removeTemporarilyAddedNodeIfAny(self, navNumber):
		if self.navPath.getNavPathType() == NavigationPath.PFIS_V \
				and self.navPath.ifNavToUnseenPatch(navNumber):
			# If graph contains unseen patch, it was because it was known from other variant.
			# Remove this temporary unseen but known patch.
			if self.graph.temporaryMode:
				self.graph.setTemporaryMode(value=False)



