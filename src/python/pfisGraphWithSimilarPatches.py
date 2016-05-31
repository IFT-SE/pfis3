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

		node1Equivalent = node1
		node2Equivalent = node2
		if node1Type == NodeType.METHOD:
			node1Equivalent = self.getEquivalentGraphNode(node1)
		if node2Type == NodeType.METHOD:
			node2Equivalent =self.getEquivalentGraphNode(node2)

		PfisGraphWithVariants._addEdge(self, node1Equivalent, node2Equivalent, node1Type, node2Type, edgeType)


	def getEquivalentGraphNode(self, node):
		return node