from pfisGraph import PfisGraph
from graphAttributes import EdgeType

class PfisGraphWithVariants(PfisGraph):
	def updateTopology(self, action, target, referrer, targetNodeType, referrerNodeType):
		PfisGraph.updateTopology(self, action, target, referrer, targetNodeType, referrerNodeType)

		if action == 'Method declaration' and self.isVariantTopology:
			self.__addEdgesToOtherVariants(referrer, referrerNodeType)
			self.__addEdgesToOtherVariants(target, targetNodeType)

	def __addEdgesToOtherVariants(self, node1, node1Type):
		nodes = self.graph.nodes()
		for node2 in nodes:
			if node1 != node2 and self.graph.node[node2]['type'] == node1Type:
				if self.langHelper.isVariantOf(node1, node2):
					print node1, " | ", node2
					self.__addEdge(node1, node2, node1Type, self.graph.node[node2]['type'], EdgeType.VARIANT_OF)