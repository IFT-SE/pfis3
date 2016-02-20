from xml.etree.ElementTree import ElementTree
from algorithmAdjacency import Adjacency
from algorithmCallDepth import CallDepth
from algorithmFrequency import Frequency
from algorithmPFIS import PFIS
from algorithmPFISTouchOnce import PFISTouchOnce
from algorithmRecency import Recency
from algorithmSourceTopology import SourceTopology
from algorithmTFIDF import TFIDF
from algorithmWorkingSet import WorkingSet

class XMLOptionsParser(object):
    
    def __init__(self, optionsFilePath, langHelper, tempDbPath):
        self.optionsFilePath = optionsFilePath
        self.langHelper = langHelper
        self.tempDbPath = tempDbPath
        self.algorithms = []
        
    def getAlgorithms(self):
        if len(self.algorithms) == 0:
            self.__parseOptions()
        
        return self.algorithms
    
    def __parseOptions(self):
        tree = ElementTree(file=self.optionsFilePath)
        root = tree.getroot()
        for child in root:
            if child.tag == 'algorithms':
                self.__parseAlgorithms(child)
                
    def __parseAlgorithms(self, node):
        for child in node:
            if child.tag == 'algorithm':
                self.__parseAlgorithm(child)
                
    def __parseAlgorithm(self, node):
        if 'class' not in node.attrib or 'name' not in node.attrib \
            or 'fileName' not in node.attrib or 'enabled' not in node.attrib:
            raise RuntimeError('parseAlgorithm: Missing required attributes in algorithm elements')
        
        print "Parsing algorithm: " + node.attrib['name']
        if node.attrib['enabled'] == 'true':
            algClass = node.attrib['class']
            
            if algClass == 'Adjacency' : self.__parseAdjacency(node)
            elif algClass == 'CallDepth' : self.__parseCallDepth(node)
            elif algClass == 'Frequency' : self.__parseFrequency(node)
            elif algClass == 'PFIS' : self.__parsePFIS(node)
            elif algClass == 'PFISTouchOnce' : self.__parsePFISTouchOnce(node)
            elif algClass == 'Recency' : self.__parseRecency(node)
            elif algClass == 'SourceTopology' : self.__parseSourceTopology(node)
            elif algClass == 'TFIDF' : self.__parseTFIDF(node)
            elif algClass == 'WorkingSet' : self.__parseWorkingSet(node)
            else:
                raise RuntimeError('parseAlgorithm: Unknown algorithm class: ' + algClass)
            
    def __parseAdjacency(self, node):
        includeTop = False
        if 'includeTop' in node.attrib and node.attrib['includeTop'] == 'true': includeTop = True
        
        self.algorithms.append(Adjacency(self.langHelper, node.attrib['name'],
            node.attrib['fileName'], includeTop=includeTop))
        
    def __parseCallDepth(self, node):
        includeTop = False
        if 'includeTop' in node.attrib and node.attrib['includeTop'] == 'true': includeTop = True
        
        self.algorithms.append(CallDepth(self.langHelper, node.attrib['name'],
            node.attrib['fileName'], includeTop=includeTop))
        
    def __parseFrequency(self, node):
        includeTop = False
        if 'includeTop' in node.attrib and node.attrib['includeTop'] == 'true': includeTop = True
        
        self.algorithms.append(Frequency(self.langHelper, node.attrib['name'],
            node.attrib['fileName'], includeTop=includeTop))
        
    def __parsePFIS(self, node):
        # TODO: Implement goal words array, maybe as a child tag labeled 'goal' 
        # with CDATA as the content. Then feed it into the split and parse...
        
        # TODO: Figure out a better way to deal with default values. If they are
        # not in the XML, we shoudln't have to create variables for them
        
        history = False
        goal = []
        decayFactor = 0.85
        decayHistory = 0.9
        numSpread = 2
        includeTop = False
        
        if 'history' in node.attrib and node.attrib['history'] == 'true': history = True
        if 'decayFactor' in node.attrib: decayFactor = float(node.attrib['decayFactor'])
        if 'decayHistory' in node.attrib: decayHistory = float(node.attrib['decayHistory'])
        if 'numSpread' in node.attrib: numSpread = int(node.attrib['numSpread'])
        if 'includeTop' in node.attrib and node.attrib['includeTop'] == 'true': includeTop = True
        
        self.algorithms.append(PFIS(self.langHelper, node.attrib['name'],
            node.attrib['fileName'], history=history, goal=goal, 
            decayFactor=decayFactor, decayHistory=decayHistory, 
            numSpread=numSpread, includeTop=includeTop))
        
    def __parsePFISTouchOnce(self, node):
        # TODO: Implement goal words array, maybe as a child tag labeled 'goal' 
        # with CDATA as the content. Then feed it into the split and parse...
        
        history = False
        goal = []
        decayFactor = 0.85
        decayHistory = 0.9
        includeTop = False
        
        if 'history' in node.attrib and node.attrib['history'] == 'true': history = True
        if 'decayFactor' in node.attrib: decayFactor = float(node.attrib['decayFactor'])
        if 'decayHistory' in node.attrib: decayHistory = float(node.attrib['decayHistory'])
        if 'includeTop' in node.attrib and node.attrib['includeTop'] == 'true': includeTop = True
        
        self.algorithms.append(PFISTouchOnce(self.langHelper, node.attrib['name'],
            node.attrib['fileName'], history=history, goal=goal, 
            decayFactor=decayFactor, decayHistory=decayHistory, 
            includeTop=includeTop))
        
    def __parseRecency(self, node):
        includeTop = False
        if 'includeTop' in node.attrib and node.attrib['includeTop'] == 'true': includeTop = True
        
        self.algorithms.append(Recency(self.langHelper, node.attrib['name'],
            node.attrib['fileName'], includeTop=includeTop))
        
    def __parseSourceTopology(self, node):
        includeTop = False
        if 'includeTop' in node.attrib and node.attrib['includeTop'] == 'true': includeTop = True
        
        self.algorithms.append(SourceTopology(self.langHelper, node.attrib['name'],
            node.attrib['fileName'], includeTop=includeTop))
        
    def __parseTFIDF(self, node):
        includeTop = False
        if 'includeTop' in node.attrib and node.attrib['includeTop'] == 'true': includeTop = True
        
        self.algorithms.append(TFIDF(self.langHelper, node.attrib['name'],
            node.attrib['fileName'], dbFilePath=self.tempDbPath, includeTop=includeTop))
        
    def __parseWorkingSet(self, node):
        workingSetSize = 10
        includeTop = False
        
        if 'workingSetSize' in node.attrib: workingSetSize = int(node.attrib['workingSetSize'])
        if 'includeTop' in node and node.attrib['includeTop'] == 'true': includeTop = True
        
        self.algorithms.append(WorkingSet(self.langHelper, node.attrib['name'],
            node.attrib['fileName'], workingSetSize=workingSetSize, includeTop=includeTop))
        
