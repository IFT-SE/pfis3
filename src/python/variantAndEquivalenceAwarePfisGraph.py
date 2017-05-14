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

	FILE_TARGET_REGEX = re.compile(r'L/hexcom/(.*?)/(.*)')


	def __init__(self, dbFilePath, langHelper, projSrc, variantsDb, stopWords=[], goalWords=[], verbose=False):
		VariantAwarePfisGraph.__init__(self, dbFilePath, langHelper, projSrc, stopWords, goalWords, verbose)
		self.variantsDb = variantsDb

		self.idToPatchMap = {}
		self.fqnToIdMap = {}

	def _addEdge(self, node1, node2, node1Type, node2Type, edgeType):

		self._updateEquivalenceInformationIfNeeded(node1)
		self._updateEquivalenceInformationIfNeeded(node2)

		node1Equivalent = self.getFqnOfEquivalentNode(node1)
		node2Equivalent = self.getFqnOfEquivalentNode(node2)

		VariantAwarePfisGraph._addEdge(self, node1Equivalent, node2Equivalent, node1Type, node2Type, edgeType)

	def _updateEquivalenceInformationIfNeeded(self, node):
		if (self.langHelper.isMethodFqn(node) or self.langHelper.isChangelogFqn(node)) \
				and not self.langHelper.isLibMethodWithoutSource(node):
			self.addPatchIfNotPresent(node)


	def addPatchIfNotPresent(self, patchFqn):
		# See patch for same FQN exists, else add
		if self.getPatchByFqn(patchFqn) is not None:
			return

		newPatch = self.__getNewlyVisitedPatch(patchFqn)

		#Update the patch details in fqn-id-node maps
		if newPatch.uuid not in self.idToPatchMap.keys():
			self.idToPatchMap[newPatch.uuid] = newPatch
		self.fqnToIdMap[patchFqn] = newPatch.uuid

	def __getNewlyVisitedPatch(self, patchFqn):
		if self.langHelper.isMethodFqn(patchFqn):
			newPatch = MethodPatch(patchFqn)

			# If it is an actual method patch (not PFIGHeader),
			# get the right patch UUID from the equivalence DB

			if not self.langHelper.isPfigHeaderFqn(patchFqn):
				self.__updatePatchUUIDFromEquivalenceDb(newPatch)

		elif self.langHelper.isChangelogFqn(patchFqn):
			newPatch = ChangelogPatch(patchFqn)

		else:
			raise Exception("Not a patch fqn:", patchFqn)
		return newPatch

	def getPatchByFqn(self, fqn):
		if fqn in self.fqnToIdMap.keys():
			uuid = self.fqnToIdMap[fqn]
			return self.idToPatchMap[uuid]
		return None

	def getFqnOfEquivalentNode(self, node):
		if (self.langHelper.isMethodFqn(node) or self.langHelper.isChangelogFqn(node)) \
				and not self.langHelper.isLibMethodWithoutSource(node):
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
		if self.langHelper.isMethodFqn(cloneTo):
			self.fqnToIdMap[cloneTo] = self.fqnToIdMap[cloneFrom]

		if self.langHelper.isChangelogFqn(cloneTo):
			VariantAwarePfisGraph.cloneNode(self, cloneTo, cloneFrom)
			self._updateEquivalenceInformationIfNeeded(cloneTo)

		return

	def removeNode(self, nodeFqn):
		id = self.fqnToIdMap[nodeFqn]
		self.fqnToIdMap.pop(nodeFqn)

		if not self.langHelper.isMethodFqn(nodeFqn):
			self.idToPatchMap.pop(id)
			VariantAwarePfisGraph.removeNode(self, nodeFqn)


	def __getPatchRow(self, fqn):

		pathRelativeToVariant = self.__getPathRelativeToVariantFolder(fqn)
		variantName = self.__getVariantName(fqn)

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


	def __getPathRelativeToVariantFolder(self, fqn):
		if self.langHelper.isMethodFqn(fqn):
			return self.FILE_TARGET_REGEX.match(fqn).groups()[1]

	def __getVariantName(self, fqn):
		if self.langHelper.isMethodFqn(fqn):
			return self.FILE_TARGET_REGEX.match(fqn).groups()[0]
