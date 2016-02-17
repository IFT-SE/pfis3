from algorithmCodeStructure import CodeStructure
from pfisGraph import EdgeType

class CallDepth(CodeStructure):
    
    def __init__(self, langHelper, name):
        CodeStructure.__init__(self, langHelper, name, [EdgeType.CALLS])