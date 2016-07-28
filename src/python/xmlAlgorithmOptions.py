from xml.etree.ElementTree import ElementTree
from algorithmFactory import AlgorithmFactory
from graphFactory import GraphFactory

class XMLOptionsParser(object):
    
    def __init__(self, optionsFilePath, langHelper, tempDbPath, projSrcPath, stopWords):
        self.optionsFilePath = optionsFilePath
        self.algorithmFactory = AlgorithmFactory(langHelper, tempDbPath)
        self.graphFactory = GraphFactory(langHelper, tempDbPath, projSrcPath, stopWords)

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
        navPathTypeStr = "default"
        if 'navPathType' in algorithmsNode.attrib:
            navPathTypeAttrib = algorithmsNode.attrib['navPathType']
            navPathTypeStr = str(navPathTypeAttrib).lower()

        if navPathTypeStr == str(navPathType).lower():
            return True
        else:
            return False


    def __getGraph(self, algorithmsNode):
        graphType = None
        variantsDb = None
        if 'graphType' in algorithmsNode.attrib:
            graphType = algorithmsNode.attrib["graphType"]
        if 'variantsDb' in algorithmsNode.attrib:
            variantsDb = algorithmsNode.attrib["variantsDb"]

        return self.graphFactory.getGraph(graphType, variantsDb)

    def __getAlgorithms(self, algorithmsNode):
        algorithms = []
        suffix = None
        if "suffix" in algorithmsNode.attrib:
            suffix = algorithmsNode.attrib["suffix"]
        for child in algorithmsNode:
            if child.tag == 'algorithm':
                algorithm = self.algorithmFactory.getAlgorithm(child, suffix)
                if algorithm != None:
                    algorithms.append(algorithm)
        return algorithms