import sys
import shutil
import getopt

from languageHelperFactory import LanguageHelperFactory
from xmlAlgorithmOptions import XMLOptionsParser
from predictor import Predictor
from navpath import NavigationPath
from PFISVNavPath import PFIS_V_NavPath

def print_usage():
	print "python pfis3.py -d <path to PFIG database> -s <path to stop words file>"
	print "                -l <language> -p <path to project source folder> "
	print "                -o <path to output folder> -x <xml options file>"
	print "					-v <set if variants topology: optional, false by default>"
	print "for language : say JAVA or JS"

def parseArgs():

	arguments = {
		"outputPath" : None,
		"stopWordsPath" : True,
		"tempDbPath" : None,
		"dbPath" : None,
		"variantTopology": False,
		"projectSrcFolderPath": None,
		"language": None,
		"xml" : None,
		"topPredictionsFolderPath": None
	}

	def assign_argument_value(argsMap, option, value):
		if option=='-v':
			arguments['variantTopology'] = True
			return

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
		opts, _ = getopt.getopt(sys.argv[1:], "vd:s:l:p:o:x:n:")
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

	variantTopology = args['variantTopology']
	# Load the stop words file
	stopWords = loadStopWords(args['stopWordsPath'])

	#TODO: Extract list to file and read later
	goalWords = ['score', 'indicator', 'hexagon,', 'exception',
				'text', 'color', 'changed', 'black', 'score',
				'calculated', 'differently', 'stay', 'Users',
				'back', 'bonus', 'multiplier', 'parentheses']

	langHelper.performDBPostProcessing(workingDbCopy)

	# Determine the algorithms to use
	xmlParser = XMLOptionsParser(args['xml'], langHelper, workingDbCopy, projSrc, variantTopology, stopWords, goalWords)

	configsList = xmlParser.getAlgorithms()
	for config in configsList:
		print "**************************************************"
		runAlgorithms(args, config[0], config[1], config[2])

	# Exit gracefully
	sys.exit(0)

def runAlgorithms(args, navPath, graph, algorithms):
	if len(algorithms) > 0:
		print "Running algorithms for: ", navPath._name, graph.name
		# Create a predictor instance for each graph type
		predictor = Predictor(graph, navPath, args['outputPath'], args['topPredictionsFolderPath'])

		# Make all predictions for the graph for all algorithms
		results = predictor.makeAllPredictions(algorithms)

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
