from algorithmCodeStructure import CodeStructure
from pfisGraph import EdgeType

class SourceTopology(CodeStructure):
    
    def __init__(self, langHelper, name, fileName, includeTop = False, numTopPredictions=0):
        CodeStructure.__init__(self, langHelper, name, fileName,
                               [EdgeType.CONTAINS, EdgeType.IMPORTS, EdgeType.EXTENDS, EdgeType.IMPLEMENTS, EdgeType.CALLS, EdgeType.ADJACENT],
                               includeTop, numTopPredictions=numTopPredictions)