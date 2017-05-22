class NodeType(object):
    PACKAGE = 0
    FILE = 1
    CLASS = 2
    METHOD = 3
    VARIABLE = 4
    PRIMITIVE = 5
    PROJECT = 6
    WORD = 7
    SPECIAL = 8 #Some Java packages weirdness!
    CHANGELOG = 9
    OUTPUT = 10

    __targetNodes = {}
    __targetNodes["Extends"] = CLASS
    __targetNodes["Implements"] = CLASS
    __targetNodes["Imports"] = FILE
    __targetNodes["Method declaration"] = CLASS
    __targetNodes["Method declaration scent"] = METHOD
    __targetNodes["Method invocation"] = METHOD
    __targetNodes["Method invocation scent"] = METHOD
    __targetNodes["New file header"] = METHOD
    __targetNodes["Package"] = FILE
    __targetNodes["Variable type"] = VARIABLE
    __targetNodes["Changelog declaration scent"] = CHANGELOG
    __targetNodes["Changelog declaration"] = CHANGELOG
    __targetNodes["Output declaration"] = OUTPUT

    __referrerNodes = {}
    __referrerNodes["Extends"] = CLASS
    __referrerNodes["Implements"] = CLASS
    __referrerNodes["Imports"] = CLASS
    __referrerNodes["Method declaration"] = METHOD
    __referrerNodes["Method invocation"] = METHOD
    __referrerNodes["Package"] = PACKAGE
    __referrerNodes["Variable declaration"] = VARIABLE
    __referrerNodes["Changelog declaration"] = CHANGELOG
    __referrerNodes["Output declaration"] = OUTPUT

    @staticmethod
    def getTargetNodeType(action, target):
        if action == 'Variable declaration' or action == 'Method invocation':
            if target.find(';.') == -1:
                return NodeType.CLASS
            else:
                return NodeType.METHOD

        if action in NodeType.__targetNodes:
            return NodeType.__targetNodes[action]

        return None

    @staticmethod
    def getReferrerNodeType(action, referrer, langHelper):
        if action == 'Variable type':
            if len(referrer) == 1:
                return NodeType.PRIMITIVE
            return NodeType.CLASS

        if action == 'Package Explorer tree':
            if langHelper.hasLanguageExtension(referrer):
                return NodeType.FILE
            return NodeType.PACKAGE

        if action in NodeType.__referrerNodes:
            return NodeType.__referrerNodes[action]

        return None


class EdgeType(object):
    #TODO: Find a smarter way that this duplicate
    CONTAINS = 0
    IMPORTS = 1
    EXTENDS = 2
    IMPLEMENTS = 3
    CALLS = 4
    ADJACENT = 5
    TYPE = 6
    VARIANT_OF = 7

    @staticmethod
    def getAll():
        return [
            EdgeType.CONTAINS,
            EdgeType.IMPORTS,
            EdgeType.EXTENDS,
            EdgeType.IMPLEMENTS,
            EdgeType.CALLS,
            EdgeType.ADJACENT,
            EdgeType.TYPE,
            EdgeType.VARIANT_OF
        ]

    @staticmethod
    def getStandardEdgeTypes():
        edges = EdgeType.getAll()
        edges.remove(EdgeType.VARIANT_OF)
        return edges
