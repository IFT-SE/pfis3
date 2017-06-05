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


	def __init__(self, dbFilePath, langHelper, projSrc, variantsDb, divorcedUntilMarried=False, stopWords=[], goalWords=[], verbose=False):
		VariantAwarePfisGraph.__init__(self, dbFilePath, langHelper, projSrc, stopWords, goalWords, verbose)
		self.variantsDb = variantsDb

		#TODO: This is a hack. Should go off when output equivalence is moved to common equivalence DB
		self.variantsOutputDb = os.path.join(os.path.dirname(self.variantsDb), 'variants-output.db')

		self.idToPatchMap = {}
		self.fqnToIdMap = {}
		self.divorcedUntilMarried = divorcedUntilMarried

		self.name = "Variant and equivalence aware: " + variantsDb
		if divorcedUntilMarried:
			self.name = self.name + "(DUM)"


	def _addEdge(self, node1, node2, node1Type, node2Type, edgeType):

		self._updateEquivalenceInformation(node1)
		self._updateEquivalenceInformation(node2)

		node1Equivalent = self.getFqnOfEquivalentNode(node1)
		node2Equivalent = self.getFqnOfEquivalentNode(node2)

		VariantAwarePfisGraph._addEdge(self, node1Equivalent, node2Equivalent, node1Type, node2Type, edgeType)

	def _updateEquivalenceInformation(self, node):
		if self.langHelper.isNavigablePatch(node) \
				and self.getPatchByFqn(node) is None:
			newPatch = self.getNewPatch(node)
			self.fqnToIdMap[node] = newPatch.uuid

			if newPatch.uuid not in self.idToPatchMap.keys():
				self.idToPatchMap[newPatch.uuid] = newPatch

	def getNewPatch(self, patchFqn, tempNode = False):
		if self.langHelper.isMethodFqn(patchFqn):
			newPatch = MethodPatch(patchFqn)

			if not tempNode:
				if not self.langHelper.isPfigHeaderFqn(patchFqn):
					self.__updatePatchUUIDFromEquivalenceDb(newPatch)

		elif self.langHelper.isChangelogFqn(patchFqn):
			newPatch = ChangelogPatch(patchFqn)

		elif self.langHelper.isOutputFqn(patchFqn):
			newPatch = OutputPatch(patchFqn)
			if not tempNode:
				self.__updateEquivalenceForOutput(newPatch, patchFqn)
		else:
			raise Exception("Not a patch fqn:", patchFqn)
		return newPatch

	def __updateEquivalenceForOutput(self, newPatch, patchFqn):
		#TODO: Sruti, Souti: cleanup this getOutputContent, put output equivalence info in the equivalence DBs.
		newPatchContent = self.__getOutputContent(patchFqn)
		newPatch.content = newPatchContent

		for _, patch in self.idToPatchMap.items():
			if patch.patchType == PatchType.OUTPUT and patch.content == newPatchContent:
				newPatch.uuid = patch.uuid

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
		if self.divorcedUntilMarried:
			self._cloneDivorceUntilMarried(cloneTo, cloneFrom)
		else:
			self._cloneMarriedUntilDivorced(cloneTo, cloneFrom)

	def _cloneMarriedUntilDivorced(self, cloneTo, cloneFrom):
		if self.langHelper.isChangelogFqn(cloneTo):
			VariantAwarePfisGraph.cloneNode(self, cloneTo, cloneFrom)
			tempPatch = self.getNewPatch(cloneTo)
			self.idToPatchMap[tempPatch.uuid] = tempPatch
			self.fqnToIdMap[cloneTo] = tempPatch.uuid
		else:
			self.fqnToIdMap[cloneTo] = self.fqnToIdMap[cloneFrom]

	def _cloneDivorceUntilMarried(self, cloneTo, cloneFrom):
		VariantAwarePfisGraph.cloneNode(self, cloneTo, cloneFrom)
		tempPatch = self.getNewPatch(cloneTo, tempNode=True)
		self.idToPatchMap[tempPatch.uuid] = tempPatch
		self.fqnToIdMap[cloneTo] = tempPatch.uuid


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

		c.close()
		conn.close()

		return patchRow

	def __getOutputContent(self, patchFqn):
		variant_name = self.langHelper.getVariantName(patchFqn)
		conn = sqlite3.connect(self.variantsOutputDb)
		c = conn.cursor()

		c.execute('SELECT output FROM variant_output WHERE variant=?', [variant_name])

		content = c.fetchone()[0]

		c.close()
		conn.close()

		return content

