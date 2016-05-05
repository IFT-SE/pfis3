from xml.etree.ElementTree import ElementTree
from algorithmFactory import AlgorithmFactory
from graphFactory import GraphFactory

class XMLOptionsParser(object):
    
    def __init__(self, optionsFilePath, langHelper, tempDbPath, projSrcPath, stopWords):
        self.optionsFilePath = optionsFilePath
        self.algorithmFactory = AlgorithmFactory(langHelper, tempDbPath)
        self.graphFactory = GraphFactory(langHelper, tempDbPath, projSrcPath, stopWords)

    def getAlgorithms(self):
        tree = ElementTree(file=self.optionsFilePath)
        root = tree.getroot()
        graphAlgorithmsMap = {}

        for child in root:
            if child.tag == 'algorithms':
                graph = self.__getGraph(child)
                algorithms = self.__getAlgorithms(child)
                graphAlgorithmsMap[graph] = algorithms

        return graphAlgorithmsMap
                
    def __getGraph(self, algorithmsNode):
        graphType = None
        if 'graphType' in algorithmsNode.attrib:
            graphType = algorithmsNode.attrib["graphType"]

        return self.graphFactory.getGraph(graphType)

    def __getAlgorithms(self, algorithmsNode):
        algorithms = []
        for child in algorithmsNode:
            if child.tag == 'algorithm':
                algorithm = self.algorithmFactory.getAlgorithm(child)
                if algorithm != None:
                    algorithms.append(algorithm)

        return algorithms