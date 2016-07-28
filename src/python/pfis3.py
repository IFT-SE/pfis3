import sys
import shutil
import getopt

from languageHelperFactory import LanguageHelperFactory
from xmlAlgorithmOptions import XMLOptionsParser
from predictor import Predictor
from navpath import NavigationPath

def print_usage():
	print "python pfis3.py -d <path to PFIG database> -s <path to stop words file>"
	print "                -l <language> -p <path to project source folder> "
	print "                -o <path to output folder> -x <xml options file>"
	print "                -v <variants db for functions: optional>"
	print "for language : say JAVA or JS"

def parseArgs():

	arguments = {
		"outputPath" : None,
		"stopWordsPath" : True,
		"tempDbPath" : None,
		"dbPath" : None,
		"projectSrcFolderPath": None,
		"language": None,
		"xml" : None,
		"topPredictionsFolderPath": None
	}

	def assign_argument_value(argsMap, option, value):
		optionKeyMap = {
			"-s" : "stopWordsPath",
			"-d" : "dbPath",
			"-l" : "language",
			"-p" : "projectSrcFolderPath",
			"-o" : "outputPath",
			"-x" : "xml",
			"-n" : "topPredictionsFolderPath"
		}

		key = optionKeyMap[option]
		arguments[key] = value

	def setConventionBasedArguments(argsMap):
		argsMap["tempDbPath"] = argsMap["dbPath"] + "_temp"

	try:
		opts, _ = getopt.getopt(sys.argv[1:], "d:s:l:p:o:x:n:")
	except getopt.GetoptError as err:
		print str(err)
		print("Invalid args passed to PFIS")
		print_usage()
		sys.exit(2)
	for option, value in opts:
		assign_argument_value(arguments, option, value)

	#TODO: currently, these are conventions, to avoid too many configurations. needs review.
	setConventionBasedArguments(arguments)

	return arguments

def main():

	args = parseArgs()
	projSrc = args['projectSrcFolderPath']

	#Initialize the processor with the appropriate language specific processor
	langHelper = LanguageHelperFactory.getLanguageHelper(args['language'])

	# Start by making a working copy of the database
	workingDbCopy = args['tempDbPath']
	copyDatabase(args['dbPath'], workingDbCopy)
	# Load the stop words file
	stopWords = loadStopWords(args['stopWordsPath'])

	langHelper.performDBPostProcessing(workingDbCopy)

	# Determine the algorithms to use
	xmlParser = XMLOptionsParser(args['xml'], langHelper, workingDbCopy, projSrc, stopWords)

	navPath = NavigationPath(workingDbCopy, langHelper, projSrc)
	#graphAlgorithmsMapWithDefaultNavPath = xmlParser.getAlgorithms(navPathType = "Default")
	#runAlgorithms(args, graphAlgorithmsMapWithDefaultNavPath, navPath)

	graphAlgorithmsMap = xmlParser.getAlgorithms(navPathType="VariantAware")
	if len(graphAlgorithmsMap.keys()) != 0:
		variantAwareNavPath = navPath.getVariantAwarePath()
		runAlgorithms(args, graphAlgorithmsMap, variantAwareNavPath)

	# Exit gracefully
	sys.exit(0)


def runAlgorithms(args, graphAlgorithmsMap, navPath):
	# Create the PFIS graph (which also determines the navigations)
	for graph in graphAlgorithmsMap.keys():
		# Create a predictor instance for each graph type
		predictor = Predictor(graph, navPath)

		algorithms = graphAlgorithmsMap[graph]
		# Make all predictions for the graph for all algorithms
		results = predictor.makeAllPredictions(algorithms, args['outputPath'], args['topPredictionsFolderPath'])

		# Save each algorithms predictions to the a separate file in the output folder
		savePredictionsToFiles(results)


def savePredictionsToFiles(results):
	for algorithm in results:
		results[algorithm].saveToFile()

def loadStopWords(path):
	# Load the stop words from a file. The file is expected to have one stop
	# word per line. Stop words are ignored and not loaded into the PFIS graph.
	words = []
	f = open(path)
	for word in f:
		words.append(word.lower().strip())
	return words

def copyDatabase(dbpath, newdbpath):
	print "Making a working copy of the database..."
	shutil.copyfile(dbpath, newdbpath)
	print "Done."

if __name__ == "__main__":
	main()
