from algorithmCodeStructure import CodeStructure
from pfisGraph import EdgeType

class SourceTopology(CodeStructure):
    
    def __init__(self, langHelper, name):
        CodeStructure.__init__(self, langHelper, name, [EdgeType.CONTAINS, EdgeType.IMPORTS, EdgeType.EXTENDS, EdgeType.IMPLEMENTS, EdgeType.CALLS, EdgeType.ADJACENT])