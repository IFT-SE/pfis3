from pfisGraph import PfisGraph
from graphAttributes import EdgeType
import re

class PfisGraphWithVariants(PfisGraph):
	def __init__(self, dbFilePath, langHelper, projSrc, stopWords=[], verbose=False):
		PfisGraph.__init__(self, dbFilePath, langHelper, projSrc, stopWords, verbose)

	def updateTopology(self, action, target, referrer, targetNodeType, referrerNodeType):
		PfisGraph.updateTopology(self, action, target, referrer, targetNodeType, referrerNodeType)

		if action == 'Method declaration':
			self._addEdgesToOtherVariants(referrer, referrerNodeType)
			self._addEdgesToOtherVariants(target, targetNodeType)

	def _addEdgesToOtherVariants(self, node1, node1Type):
		nodes = self.graph.nodes()
		for node2 in nodes:
			if node1 != node2 and self.graph.node[node2]['type'] == node1Type:
				if self._isVariantOf(node1, node2):
					self._addEdge(node1, node2, node1Type, self.graph.node[node2]['type'], EdgeType.VARIANT_OF)

	def getAllNeighbors(self, node):
		edges = EdgeType.getAll()
		return self.getNeighborsOfDesiredEdgeTypes(node, edges)

	#TODO: Move to lang helper
	def _isVariantOf(self, fqn1, fqn2):
		#L/hexcom/2014-05-26-10:18:35/js/view.js;.renderText(x"," y"," fontSize"," color"," text)
		#L/hexcom/Current/js_v9/Hex.js/Hex(sideLength);.rotate() -- nested methods

		#FILE_TARGET_REGEX = re.compile(r'L/hexcom/(.*?)/(.*)') - matches entire path to method
		FILE_TARGET_REGEX = re.compile(r'L/hexcom/(.*?)/(.*);.(.*)\(')

		#They are not FQNs of non-std methods in the topology
		if FILE_TARGET_REGEX.match(fqn1) == None or FILE_TARGET_REGEX.match(fqn2) == None:
			return False

		match1 = FILE_TARGET_REGEX.match(fqn1).groups()
		match2 = FILE_TARGET_REGEX.match(fqn2).groups()

		# Return false if both are in same variant
		if match1[0] == match2[0]:
			return False

		else:
			#Right now it is just FQN
			#TODO: Queer case of headers!!!
			#return match1[1] == match2[1] # Match for entire path
			return match1[2] == match2[2] #Match just method name
