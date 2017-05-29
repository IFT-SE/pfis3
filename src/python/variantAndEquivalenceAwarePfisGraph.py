from variantAwarePfisGraph import VariantAwarePfisGraph
from patches import *
import os
import sqlite3
import re

class VariantAndEquivalenceAwarePfisGraph(VariantAwarePfisGraph):

	GET_VARIANT_POSITION_QUERY = 'select * from VARIANTS where NAME= ?'
	FETCH_PATCH_FOR_FQN_QUERY = 'select vf.method, v1.name, v2.name, vf.body, vf.uuid from variants_to_functions as vf ' \
                            'join variants as v1 on vf.start = v1.num ' \
                            'join variants as v2 on vf.end=v2.num ' \
                            'where vf.method = ? and start <= ? and end >=?'


	def __init__(self, dbFilePath, langHelper, projSrc, variantsDb, stopWords=[], goalWords=[], verbose=False):
		VariantAwarePfisGraph.__init__(self, dbFilePath, langHelper, projSrc, stopWords, goalWords, verbose)
		self.variantsDb = variantsDb

		self.idToPatchMap = {}
		self.fqnToIdMap = {}
		self.name = "Variant and equivalence aware: ", variantsDb

	def _addEdge(self, node1, node2, node1Type, node2Type, edgeType):

		self._updateEquivalenceInformation(node1)
		self._updateEquivalenceInformation(node2)

		node1Equivalent = self.getFqnOfEquivalentNode(node1)
		node2Equivalent = self.getFqnOfEquivalentNode(node2)

		VariantAwarePfisGraph._addEdge(self, node1Equivalent, node2Equivalent, node1Type, node2Type, edgeType)

	def _updateEquivalenceInformation(self, node, setAsNonEquivalent=False):
		if self.langHelper.isNavigablePatch(node) \
				and self.getPatchByFqn(node) is None:
			newPatch = self.getNewPatch(node, setAsNonEquivalent)
			self.fqnToIdMap[node] = newPatch.uuid
			if newPatch.uuid not in self.idToPatchMap.keys():
				self.idToPatchMap[newPatch.uuid] = newPatch

	def getNewPatch(self, patchFqn, setAsNonEquivalent=False):
		if self.langHelper.isMethodFqn(patchFqn):
			newPatch = MethodPatch(patchFqn)

			if not setAsNonEquivalent:
				if not self.langHelper.isPfigHeaderFqn(patchFqn):
					self.__updatePatchUUIDFromEquivalenceDb(newPatch)

		elif self.langHelper.isChangelogFqn(patchFqn):
			newPatch = ChangelogPatch(patchFqn)

		#TODO: Sruti, Souti: account for equivalence
		elif self.langHelper.isOutputFqn(patchFqn):
			newPatch = OutputPatch(patchFqn)

		else:
			raise Exception("Not a patch fqn:", patchFqn)
		return newPatch

	def getPatchByFqn(self, fqn):
		if fqn in self.fqnToIdMap.keys():
			uuid = self.fqnToIdMap[fqn]
			return self.idToPatchMap[uuid]
		return None

	def getFqnOfEquivalentNode(self, node):
		if self.langHelper.isNavigablePatch(node):
			equivalentPatch = self.getPatchByFqn(node)
			if equivalentPatch is not None:
				return equivalentPatch.fqn
		return node

	def containsNode(self, node):
		if node is None:
			return False
		equivalentNode = self.getFqnOfEquivalentNode(node)
		return equivalentNode in self.graph.nodes()

	def getNode(self, nodeName):
		equivalentNode = self.getFqnOfEquivalentNode(nodeName)
		return self.graph.node[equivalentNode]

	def __updatePatchUUIDFromEquivalenceDb(self, newPatch):
		patchRow = self.__getPatchRow(newPatch.fqn)
		newPatch.uuid = patchRow[4]


	def cloneNode(self, cloneTo, cloneFrom):
		VariantAwarePfisGraph.cloneNode(self, cloneTo, cloneFrom)

		# Do not add in actual equivalence information, for this temporarily created patch
		self._updateEquivalenceInformation(cloneTo, setAsNonEquivalent=True)

		return

	def removeNode(self, nodeFqn):
		# Output and method patches are treated as equivalent to last seen, so just update the maps.
		id = self.fqnToIdMap[nodeFqn]
		self.fqnToIdMap.pop(nodeFqn)


		# For changelog, there is an actual node added, so remove that node.
		if self.langHelper.isChangelogFqn(nodeFqn):
			self.idToPatchMap.pop(id)
			VariantAwarePfisGraph.removeNode(self, nodeFqn)

	def __getPatchRow(self, fqn):
		
		if self.langHelper.isMethodFqn(fqn):
			pathRelativeToVariant = self.langHelper.getPathRelativeToVariant(fqn)
			variantName = self.langHelper.getVariantName(fqn)

		if not os.path.exists(self.variantsDb):
			raise Exception("Db not found: ", self.variantsDb)

		conn = sqlite3.connect(self.variantsDb)

		if conn is None:
			raise Exception("Connection Error: ", self.variantsDb)

		c = conn.cursor()

		c.execute(self.GET_VARIANT_POSITION_QUERY, [variantName])
		variantNum = c.fetchone()[0]

		c.execute(self.FETCH_PATCH_FOR_FQN_QUERY, [pathRelativeToVariant, variantNum, variantNum])
		patchRow = c.fetchone()

		conn.close()

		return patchRow

