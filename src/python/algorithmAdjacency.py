from algorithmCodeStructure import CodeStructure
from pfisGraph import EdgeType

class Adjacency(CodeStructure):
    
    def __init__(self, langHelper, name, fileName, includeTop = False, numTopPredictions=0):
        CodeStructure.__init__(self, langHelper, name, fileName, [EdgeType.ADJACENT], includeTop, numTopPredictions)
        