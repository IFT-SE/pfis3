from algorithmAdjacency import Adjacency
from algorithmCallDepth import CallDepth
from algorithmFrequency import Frequency
from algorithmPFISTouchOnce import PFISTouchOnce
from algorithmRecency import Recency
from algorithmSourceTopology import SourceTopology
from algorithmTFIDF import TFIDF
from algorithmLSI import LSI
from algorithmWorkingSet import WorkingSet
from algorithmVariantOfLinks import VariantOf
from algorithmGoalWordSimilarity import GoalWordSimilarity
from spreadingTrials import *
from algorithmPFISHierarchy import PFISHierarchy

class AlgorithmFactory:
	def __init__(self, langHelper, dbPath):
		self.langHelper = langHelper
		self.tempDbPath = dbPath

	def getAlgorithm(self, node, suffix):

		if 'class' not in node.attrib or 'name' not in node.attrib \
			or 'fileName' not in node.attrib or 'enabled' not in node.attrib:
			raise RuntimeError('parseAlgorithm: Missing required attributes in algorithm elements')

		print "Parsing algorithm: " + node.attrib['name'] + node.attrib['enabled']
		if node.attrib['enabled'].lower() == 'true':
			algClass = node.attrib['class']

			if 'PFIS'.lower() in algClass.lower():
				return self.__parsePFIS(node, suffix, algClass)
			elif algClass in ['Adjacency', 'CallDepth', "Frequency", "Recency", "SourceTopology", "VariantOf"]:
				return self.__parseSingleFactors(node, suffix, algClass)
			elif algClass in ['TFIDF', "GoalWordSimilarity"]:
				return self.__parseTextSimilaritySingleFactorModels(node, suffix, algClass)
			elif algClass == 'LSI' : return self.__parseLSI(node, suffix)
			elif algClass == 'WorkingSet' : return self.__parseWorkingSet(node, suffix)
			else:
				raise RuntimeError('parseAlgorithm: Unknown algorithm class: ' + algClass)

	def getSuffixedNames(self, node, graphTypeSuffix):
		extensionIndex = node.attrib['fileName'].find('.txt')
		fileName = node.attrib['fileName'][0:extensionIndex]
		algoName = node.attrib['name']
		if graphTypeSuffix is not None or graphTypeSuffix != '':
			fileName = fileName + "__" + graphTypeSuffix
			algoName = algoName + "__" + graphTypeSuffix
		return (fileName + ".txt", algoName)

	def __parseSingleFactors(self, node, graphTypeSuffix, className):
		nameClassMap = {
			"VariantOf": VariantOf,
			"Adjacency": Adjacency,
			"CallDepth": CallDepth,
			"Frequency": Frequency,
			"Recency": Recency,
			"SourceTopology": SourceTopology
		}

		topPredictionsOptions = self.getTopPredictionsAttributes(node)
		fileName, algoName = self.getSuffixedNames(node, graphTypeSuffix)
		return nameClassMap[className](self.langHelper, algoName,
						 fileName, includeTop=topPredictionsOptions[0], numTopPredictions=topPredictionsOptions[1])

	def __parsePFIS(self, node, graphTypeSuffix, className):

		nameClassMap = {
			"PFIS": PFIS,
			"PFIS3": PFIS3,
			"PFISHierarchy": PFISHierarchy
		}

		history = False
		goal = False
		changelogGoalActivation = False
		decayFactor = 0.85
		decayHistory = 0.9
		decaySimilarity = 0.85
		decayVariant = 0.85

		topPredictionsOptions = self.getTopPredictionsAttributes(node)
		if 'history' in node.attrib and node.attrib['history'] == 'true': history = True
		if 'goal' in node.attrib and node.attrib['goal'].lower() == 'true': goal = True
		if 'decayFactor' in node.attrib: decayFactor = float(node.attrib['decayFactor'])
		if 'decaySimilarity' in node.attrib: decaySimilarity = float(node.attrib['decaySimilarity'])
		if 'decayVariant' in node.attrib: decayVariant = float(node.attrib['decayVariant'])
		if 'decayHistory' in node.attrib: decayHistory = float(node.attrib['decayHistory'])
		if 'changelogGoalActivation' in node.attrib and node.attrib['changelogGoalActivation'].lower() == 'true': changelogGoalActivation = True
		fileName, algoName = self.getSuffixedNames(node, graphTypeSuffix)

		if algoName == "PFISTouchOnce":
			return PFISTouchOnce(self.langHelper, algoName,
				fileName, history=history, goal=goal,
				decayFactor=decayFactor, decayHistory=decayHistory, decaySimilarity=decaySimilarity, decayVariant=decayVariant, changelogGoalActivation=changelogGoalActivation,
				includeTop=topPredictionsOptions[0], numTopPredictions=topPredictionsOptions[1])
		else:
			numSpread = 2
			if 'numSpread' in node.attrib: numSpread = int(node.attrib['numSpread'])

			return nameClassMap[className](self.langHelper, algoName,
		            fileName, history=history, goal=goal,
		            decayFactor=decayFactor, decaySimilarity=decaySimilarity, decayHistory=decayHistory,
		            numSpread=numSpread, decayVariant=decayVariant, changelogGoalActivation = changelogGoalActivation,
		            includeTop=topPredictionsOptions[0], numTopPredictions=topPredictionsOptions[1])

	def __parseTextSimilaritySingleFactorModels(self, node, graphTypeSuffix, className):
		algoClassMap = {
			"TFIDF": TFIDF,
			"GoalWordSimilarity": GoalWordSimilarity
		}

		topPredictionsOptions = self.getTopPredictionsAttributes(node)
		fileName, algoName = self.getSuffixedNames(node, graphTypeSuffix)

		return algoClassMap[className](self.langHelper, algoName,
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