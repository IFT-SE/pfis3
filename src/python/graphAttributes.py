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
    VARIANT = 11
    OUTPUT_INFO_FEATURE = 12

    Levels = {
        METHOD: 5,
        CLASS: 4,
        FILE: 3,
        PACKAGE: 2,
        CHANGELOG: 2,
        OUTPUT: 2,
        VARIANT: 1,
        PROJECT: 0
    }

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
    __targetNodes["Output declaration scent"] = OUTPUT

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
    __referrerNodes["Output declaration scent"] = OUTPUT_INFO_FEATURE


    __targetNodeOverrides = {"JS": {}}
    __targetNodeOverrides["JS"]["Method declaration"] = FILE
    __referrerNodeOverrides = {}

    @staticmethod
    def getLevel(nodeType):
        if nodeType in NodeType.Levels:
            return NodeType.Levels[nodeType]
        else:
            return None

    @staticmethod
    def getLanguageOverride(overrides, language, action):
        if language in overrides.keys():
            langOverrides = overrides[language]
            if action in langOverrides.keys():
                return langOverrides[action]
        return None

    @staticmethod
    def getTargetNodeType(action, target, langHelper):
        if action == 'Variable declaration' or action == 'Method invocation':
            if target.find(';.') == -1:
                return NodeType.CLASS
            else:
                return NodeType.METHOD

        if action in NodeType.__targetNodes:
            targetNodeType = NodeType.getLanguageOverride(NodeType.__targetNodeOverrides, langHelper.Language, action)
            if targetNodeType is None:
                targetNodeType = NodeType.__targetNodes[action]
            return targetNodeType
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

    @staticmethod
    def getAll():
        return [
            NodeType.PACKAGE,
            NodeType.FILE,
            NodeType.CLASS,
            NodeType.METHOD,
            NodeType.VARIABLE,
            NodeType.PRIMITIVE,
            NodeType.PROJECT,
            NodeType.WORD,
            NodeType.SPECIAL,
            NodeType.CHANGELOG,
            NodeType.OUTPUT,
            NodeType.VARIANT
        ]

    @staticmethod
    def predictable():
        return [NodeType.METHOD, NodeType.CHANGELOG, NodeType.OUTPUT]

    @staticmethod
    def getDeclarationAction(nodeType):
        return {
            NodeType.METHOD: "Method declaration",
            NodeType.OUTPUT: "Output declaration",
            NodeType.CHANGELOG: "Changelog declaration"
        }[nodeType]

    @staticmethod
    def getNodeTypesToClone():
        nodeTypes = NodeType.predictable()
        nodeTypes.extend([NodeType.WORD, NodeType.OUTPUT_INFO_FEATURE])
        return nodeTypes

class EdgeType(object):
    #TODO: Find a smarter way that this duplicate
    CONTAINS = 0
    IMPORTS = 1
    EXTENDS = 2
    IMPLEMENTS = 3
    CALLS = 4
    ADJACENT = 5
    TYPE = 6
    SIMILAR = 7
    CONTAINS_WORD = 8
    IN_VARIANT = 9

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
            EdgeType.SIMILAR,
            EdgeType.CONTAINS_WORD
        ]
