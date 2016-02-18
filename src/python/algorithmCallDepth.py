from algorithmCodeStructure import CodeStructure
from pfisGraph import EdgeType

class CallDepth(CodeStructure):
    
    def __init__(self, langHelper, name, fileName):
        CodeStructure.__init__(self, langHelper, name, fileName, [EdgeType.CALLS])