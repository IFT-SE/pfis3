from xml.etree.ElementTree import ElementTree
from algorithmFactory import AlgorithmFactory
from graphFactory import GraphFactory

class XMLOptionsParser(object):
    
    def __init__(self, optionsFilePath, langHelper, tempDbPath, projSrcPath, variantTopology, stopWords, goalWords):
        self.optionsFilePath = optionsFilePath
        self.algorithmFactory = AlgorithmFactory(langHelper, tempDbPath)
        self.graphFactory = GraphFactory(langHelper, tempDbPath, projSrcPath, variantTopology, stopWords, goalWords)

    def getAlgorithms(self, navPathType):
        tree = ElementTree(file=self.optionsFilePath)
        root = tree.getroot()
        graphAlgorithmsMap = {}

        for child in root:
            if child.tag == 'algorithms' and self.__isNavPathType(child, navPathType):
                graph = self.__getGraph(child)
                algorithms = self.__getAlgorithms(child)
                graphAlgorithmsMap[graph] = algorithms
        return graphAlgorithmsMap

    def __isNavPathType(self, algorithmsNode, navPathType):
        navPathTypeStr = None

        if 'navPathType' in algorithmsNode.attrib:
            navPathTypeAttrib = algorithmsNode.attrib['navPathType']
            navPathTypeStr = str(navPathTypeAttrib)
        else:
            navPathTypeStr = 'Default'

        if navPathTypeStr.lower() == navPathType.lower():
            return True

        else:
            return False


    def __getGraph(self, algorithmsNode):
        return self.graphFactory.getGraph(algorithmsNode)

    def __getAlgorithms(self, algorithmsNode):
        algorithms = []
        suffix = None
        if "suffix" in algorithmsNode.attrib:
            suffix = algorithmsNode.attrib["suffix"]
        for child in algorithmsNode:
            if child.tag == 'algorithm':
                algorithm = self.algorithmFactory.getAlgorithm(child, suffix)
                if algorithm is not None:
                    algorithms.append(algorithm)
        return algorithms