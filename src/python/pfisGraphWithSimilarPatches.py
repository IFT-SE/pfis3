from knownPatches import KnownPatches
from pfisGraphWithVariants import PfisGraphWithVariants
from graphAttributes import NodeType

class PfisGraphWithSimilarPatches(PfisGraphWithVariants):
	def __init__(self, dbFilePath, langHelper, projSrc, variantsDb, stopWords=[], verbose=False):
		PfisGraphWithVariants.__init__(self, dbFilePath, langHelper, projSrc, stopWords, verbose)
		self.variantsDb = variantsDb
		self.knownMethodPatches = KnownPatches(langHelper, variantsDb)

	def _addEdge(self, node1, node2, node1Type, node2Type, edgeType):

		self._updateKnownPatches(node1, node1Type)
		self._updateKnownPatches(node2, node2Type)

		#TODO: Get rid of DRY code : checking [NodeType.METHOD, NodeType.CHANGELOG]
		#      move as a static to NodeType class
		if node1Type in [NodeType.METHOD, NodeType.CHANGELOG] and node2Type in [NodeType.METHOD, NodeType.CHANGELOG]:
			PfisGraphWithVariants._addEdge(self, node1, node2, node1Type, node2Type, edgeType)

		else:
			node1Equivalent = self._getEquivalentNode(node1, node1Type)
			node2Equivalent = self._getEquivalentNode(node2, node2Type)
			PfisGraphWithVariants._addEdge(self, node1Equivalent, node2Equivalent, node1Type, node2Type, edgeType)

	def _updateKnownPatches(self, node, nodeType):
		if nodeType in [NodeType.METHOD, NodeType.CHANGELOG] and not self.langHelper.isLibMethodWithoutSource(node):
			self.knownMethodPatches.addFilePatch(node)

	def _getEquivalentNode(self, node, nodeType):
		if nodeType not in [NodeType.METHOD, NodeType.CHANGELOG] or self.langHelper.isLibMethodWithoutSource(node):
			return node

		else:
			nodeEquivalent = self.getEquivalentGraphNode(node)
			return nodeEquivalent

	def getEquivalentGraphNode(self, node):
		#TODO: See why there are TWO different methods

		method = self.knownMethodPatches.findMethodByFqn(node)
		return method.fqn

	def getFqnOfEquivalentNode(self, fqn):
		equivalentPatch = self.knownMethodPatches.findMethodByFqn(fqn)
		return equivalentPatch.fqn

	def containsNode(self, node):
		if self.langHelper.isMethodFqn(node) or self.langHelper.isChangelogFqn(node):
			equivalentNode = self.getFqnOfEquivalentNode(node)
			return equivalentNode in self.graph.nodes()
		return node in self.graph.nodes()

	def getNode(self, nodeName):
		equivalentNode = nodeName
		if self.langHelper.isMethodFqn(nodeName) or self.langHelper.isChangelogFqn(nodeName):
			equivalentNode = self.getFqnOfEquivalentNode(nodeName)
		return self.graph.node[equivalentNode]