from algorithmAdjacency import Adjacency
from algorithmCallDepth import CallDepth
from algorithmFrequency import Frequency
from algorithmPFIS import PFIS
from algorithmPFISTouchOnce import PFISTouchOnce
from algorithmRecency import Recency
from algorithmSourceTopology import SourceTopology
from algorithmTFIDF import TFIDF
from algorithmLSI import LSI
from algorithmWorkingSet import WorkingSet


class AlgorithmFactory:
	def __init__(self, langHelper, dbPath):
		self.langHelper = langHelper
		self.tempDbPath = dbPath

	def getAlgorithm(self, node, suffix):

		if 'class' not in node.attrib or 'name' not in node.attrib \
			or 'fileName' not in node.attrib or 'enabled' not in node.attrib:
			raise RuntimeError('parseAlgorithm: Missing required attributes in algorithm elements')

		print "Parsing algorithm: " + node.attrib['name']
		if node.attrib['enabled'] == 'true':
			algClass = node.attrib['class']

			if algClass == 'Adjacency' : return self.__parseAdjacency(node, suffix)
			elif algClass == 'CallDepth' : return self.__parseCallDepth(node, suffix)
			elif algClass == 'Frequency' : return self.__parseFrequency(node, suffix)
			elif algClass == 'PFIS' : return self.__parsePFIS(node, suffix)
			elif algClass == 'PFISTouchOnce' : return self.__parsePFISTouchOnce(node, suffix)
			elif algClass == 'Recency' : return self.__parseRecency(node, suffix)
			elif algClass == 'SourceTopology' : return self.__parseSourceTopology(node, suffix)
			elif algClass == 'TFIDF' : return self.__parseTFIDF(node, suffix)
			elif algClass == 'LSI' : return self.__parseLSI(node, suffix)
			elif algClass == 'WorkingSet' : return self.__parseWorkingSet(node, suffix)
			else:
				raise RuntimeError('parseAlgorithm: Unknown algorithm class: ' + algClass)

	def getSuffixedNames(self, node, graphTypeSuffix):
		extensionIndex = node.attrib['fileName'].find('.txt')
		fileName = node.attrib['fileName'][0:extensionIndex]
		algoName = node.attrib['name']
		if graphTypeSuffix is not None:
			fileName = fileName + "__" + graphTypeSuffix
			algoName = algoName + "__" + graphTypeSuffix
		return (fileName + ".txt", algoName)

	def __parseAdjacency(self, node, graphTypeSuffix):
		topPredictionsOptions = self.getTopPredictionsAttributes(node)
		fileName, algoName = self.getSuffixedNames(node, graphTypeSuffix)
		return Adjacency(self.langHelper, algoName,
			fileName, includeTop=topPredictionsOptions[0], numTopPredictions=topPredictionsOptions[1])

	def __parseCallDepth(self, node, graphTypeSuffix):
		topPredictionsOptions = self.getTopPredictionsAttributes(node)
		fileName, algoName = self.getSuffixedNames(node, graphTypeSuffix)
		return CallDepth(self.langHelper, algoName,
			fileName, includeTop=topPredictionsOptions[0], numTopPredictions=topPredictionsOptions[1])

	def __parseFrequency(self, node, graphTypeSuffix):
		topPredictionsOptions = self.getTopPredictionsAttributes(node)
		fileName, algoName = self.getSuffixedNames(node, graphTypeSuffix)

		return Frequency(self.langHelper, algoName,
			fileName, includeTop=topPredictionsOptions[0], numTopPredictions=topPredictionsOptions[1])

	def __parsePFIS(self, node, graphTypeSuffix):
		# TODO: Implement goal words array, maybe as a child tag labeled 'goal'
		# with CDATA as the content. Then feed it into the split and parse...

		# TODO: Figure out a better way to deal with default values. If they are
		# not in the XML, we shoudln't have to create variables for them

		history = False
		goal = []
		decayFactor = 0.85
		decayHistory = 0.9
		numSpread = 2

		topPredictionsOptions = self.getTopPredictionsAttributes(node)
		if 'history' in node.attrib and node.attrib['history'] == 'true': history = True
		if 'decayFactor' in node.attrib: decayFactor = float(node.attrib['decayFactor'])
		if 'decayHistory' in node.attrib: decayHistory = float(node.attrib['decayHistory'])
		if 'numSpread' in node.attrib: numSpread = int(node.attrib['numSpread'])
		fileName, algoName = self.getSuffixedNames(node, graphTypeSuffix)

		return PFIS(self.langHelper, algoName,
			fileName, history=history, goal=goal,
			decayFactor=decayFactor, decayHistory=decayHistory,
			numSpread=numSpread,
			includeTop=topPredictionsOptions[0], numTopPredictions=topPredictionsOptions[1])

	def __parsePFISTouchOnce(self, node, graphTypeSuffix):
		# TODO: Implement goal words array, maybe as a child tag labeled 'goal'
		# with CDATA as the content. Then feed it into the split and parse...

		history = False
		goal = []
		decayFactor = 0.85
		decayHistory = 0.9

		if 'history' in node.attrib and node.attrib['history'] == 'true': history = True
		if 'decayFactor' in node.attrib: decayFactor = float(node.attrib['decayFactor'])
		if 'decayHistory' in node.attrib: decayHistory = float(node.attrib['decayHistory'])

		topPredictionsOptions = self.getTopPredictionsAttributes(node)
		fileName, algoName = self.getSuffixedNames(node, graphTypeSuffix)

		return PFISTouchOnce(self.langHelper, algoName,
			fileName, history=history, goal=goal,
			decayFactor=decayFactor, decayHistory=decayHistory,
			includeTop=topPredictionsOptions[0], numTopPredictions=topPredictionsOptions[1])

	def __parseRecency(self, node, graphTypeSuffix):
		topPredictionsOptions = self.getTopPredictionsAttributes(node)

		fileName, algoName = self.getSuffixedNames(node, graphTypeSuffix)

		return Recency(self.langHelper, algoName, fileName,
			includeTop=topPredictionsOptions[0], numTopPredictions=topPredictionsOptions[1])

	def __parseSourceTopology(self, node, graphTypeSuffix):
		topPredictionsOptions = self.getTopPredictionsAttributes(node)
		fileName, algoName = self.getSuffixedNames(node, graphTypeSuffix)

		return SourceTopology(self.langHelper, algoName,
			fileName, includeTop=topPredictionsOptions[0],
			numTopPredictions=topPredictionsOptions[1])

	def __parseTFIDF(self, node, graphTypeSuffix):
		topPredictionsOptions = self.getTopPredictionsAttributes(node)
		fileName, algoName = self.getSuffixedNames(node, graphTypeSuffix)

		return TFIDF(self.langHelper, algoName,
			fileName, dbFilePath=self.tempDbPath,
			includeTop=topPredictionsOptions[0], numTopPredictions=topPredictionsOptions[1])

	def __parseLSI(self, node, graphTypeSuffix):
		numTopics = 200

		topPredictionsOptions = self.getTopPredictionsAttributes(node)
		if 'numTopics' in node.attrib: numTopics = float(node.attrib['numTopics'])

		fileName, algoName = self.getSuffixedNames(node, graphTypeSuffix)

		return LSI(self.langHelper, algoName,
			fileName, dbFilePath=self.tempDbPath, numTopics=numTopics,
			includeTop=topPredictionsOptions[0], numTopPredictions=topPredictionsOptions[1])

	def __parseWorkingSet(self, node, graphTypeSuffix):
		workingSetSize = 10

		if 'workingSetSize' in node.attrib: workingSetSize = int(node.attrib['workingSetSize'])
		topPredictionsOptions = self.getTopPredictionsAttributes(node)
		fileName, algoName = self.getSuffixedNames(node, graphTypeSuffix)

		return WorkingSet(self.langHelper, algoName,
			fileName, workingSetSize=workingSetSize,
			includeTop=topPredictionsOptions[0], numTopPredictions=topPredictionsOptions[1])

	def getTopPredictionsAttributes(self, node):
		includeTop = False
		numTopPredictions = 0

		if 'includeTop' in node.attrib and node.attrib['includeTop'] == 'true': includeTop = True
		if includeTop and 'numTopPredictions' in node.attrib: numTopPredictions=int(node.attrib['numTopPredictions'])

		return (includeTop, numTopPredictions)
