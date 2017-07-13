from xml.etree.ElementTree import ElementTree
from algorithmFactory import AlgorithmFactory
from graphFactory import GraphFactory
from navpath import NavigationPath
from PFISVNavPath import PFIS_V_NavPath

class XMLOptionsParser(object):
    
    def __init__(self, optionsFilePath, langHelper, tempDbPath, projSrcPath, variantTopology, stopWords, goalWords):
        self.workingDbCopy= tempDbPath
        self.langHelper = langHelper
        self.projSrc = projSrcPath
        self.optionsFilePath = optionsFilePath
        self.algorithmFactory = AlgorithmFactory(langHelper, tempDbPath)
        self.graphFactory = GraphFactory(langHelper, tempDbPath, projSrcPath, variantTopology, stopWords, goalWords)

    def getAlgorithms(self):
        tree = ElementTree(file=self.optionsFilePath)
        root = tree.getroot()
        configsToRun = []

        for child in root:
            if child.tag == 'algorithms':
                navpath = self.__getNavPath(child)
                graph = self.__getGraph(child)
                algorithms = self.__getAlgorithms(child)
                configsToRun.append((navpath, graph, algorithms))
        return configsToRun

    def __getNavPath(self, algorithmsNode):
        overrides = {}
        overrideKeys = NavigationPath.variantOptions.keys()
        for key in overrideKeys:
            if key in algorithmsNode.attrib.keys():
                val = str(algorithmsNode.attrib[key])
                if val.lower() == "true":
                    overrides[key] = True
                else:
                    overrides[key] = False

        navPath = None
        if 'navPathType' in algorithmsNode.attrib and algorithmsNode.attrib['navPathType'] == NavigationPath.PFIS_V:
            navPath = PFIS_V_NavPath(self.workingDbCopy, self.langHelper, self.projSrc, overrides)
        else:
            navPath = NavigationPath(self.workingDbCopy, self.langHelper, self.projSrc, variantOverrides=overrides)

        return navPath


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
        suffix = ''
        if "suffix" in algorithmsNode.attrib:
            suffix = algorithmsNode.attrib["suffix"]
        for child in algorithmsNode:
            if child.tag == 'algorithm':
                algorithm = self.algorithmFactory.getAlgorithm(child, suffix)
                if algorithm is not None:
                    algorithms.append(algorithm)
        return algorithms