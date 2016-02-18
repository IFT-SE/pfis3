from algorithmCodeStructure import CodeStructure
from pfisGraph import EdgeType

class CallDepth(CodeStructure):
    
    def __init__(self, langHelper, name, fileName, includeTop = False):
        CodeStructure.__init__(self, langHelper, name, fileName, [EdgeType.CALLS], includeTop)