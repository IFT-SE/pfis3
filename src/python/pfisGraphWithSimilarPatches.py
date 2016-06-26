from knownPatches import KnownPatches
from pfisGraphWithVariants import PfisGraphWithVariants
from graphAttributes import NodeType

class PfisGraphWithSimilarPatches(PfisGraphWithVariants):
	def __init__(self, dbFilePath, langHelper, projSrc, variantsDb, stopWords=[], verbose=False):
		PfisGraphWithVariants.__init__(self, dbFilePath, langHelper, projSrc, stopWords, verbose)
		self.variantsDb = variantsDb
		self.knownMethodPatches = KnownPatches(langHelper, variantsDb)

	def _addEdge(self, node1, node2, node1Type, node2Type, edgeType):
		if node1Type != NodeType.METHOD and node2Type != NodeType.METHOD:
			PfisGraphWithVariants._addEdge(self, node1, node2, node1Type, node2Type, edgeType)

		node1Equivalent = self._getEquivalentNode(node1, node1Type)
		node2Equivalent = self._getEquivalentNode(node2, node2Type)

		PfisGraphWithVariants._addEdge(self, node1Equivalent, node2Equivalent, node1Type, node2Type, edgeType)


	def _getEquivalentNode(self, node, nodeType):
		if nodeType != NodeType.METHOD:
			return node

		elif self.langHelper.excludeMethod(node):
			return node

		else:
			nodeEquivalent = self.getEquivalentGraphNode(node)
			return nodeEquivalent

	def getEquivalentGraphNode(self, node):
		#TODO: See why there are TWO different methods
		self.knownMethodPatches.addFilePatch(node)
		method = self.knownMethodPatches.findMethodByFqn(node)
		return method.fqn

	def getFqnOfEquivalentNode(self, fqn):
		equivalentPatch = self.knownMethodPatches.findMethodByFqn(fqn)
		return equivalentPatch.fqn
