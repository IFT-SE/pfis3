from knownPatches import KnownPatches
from variantAwarePfisGraph import VariantAwarePfisGraph

class VariantAndEquivalenceAwarePfisGraph(VariantAwarePfisGraph):
	def __init__(self, dbFilePath, langHelper, projSrc, variantsDb, stopWords=[], goalWords=[], verbose=False):
		VariantAwarePfisGraph.__init__(self, dbFilePath, langHelper, projSrc, stopWords, goalWords, verbose)
		self.variantsDb = variantsDb
		self.knownMethodPatches = KnownPatches(langHelper, variantsDb)

	def _addEdge(self, node1, node2, node1Type, node2Type, edgeType):

		self._updateEquivalenceInformationIfNeeded(node1)
		self._updateEquivalenceInformationIfNeeded(node2)

		node1Equivalent = self.getFqnOfEquivalentNode(node1)
		node2Equivalent = self.getFqnOfEquivalentNode(node2)

		VariantAwarePfisGraph._addEdge(self, node1Equivalent, node2Equivalent, node1Type, node2Type, edgeType)

	def _updateEquivalenceInformationIfNeeded(self, node):
		if (self.langHelper.isMethodFqn(node) or self.langHelper.isChangelogFqn(node)) \
				and not self.langHelper.isLibMethodWithoutSource(node):
			self.knownMethodPatches.addFilePatch(node)

	def getFqnOfEquivalentNode(self, node):
		if (self.langHelper.isMethodFqn(node) or self.langHelper.isChangelogFqn(node)) \
				and not self.langHelper.isLibMethodWithoutSource(node):
			equivalentPatch = self.knownMethodPatches.findMethodByFqn(node)
			return equivalentPatch.fqn
		else:
			return node

	def containsNode(self, node):
		equivalentNode = self.getFqnOfEquivalentNode(node)
		return equivalentNode in self.graph.nodes()

	def getNode(self, nodeName):
		equivalentNode = self.getFqnOfEquivalentNode(nodeName)
		return self.graph.node[equivalentNode]