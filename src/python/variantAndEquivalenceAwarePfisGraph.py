from variantAwarePfisGraph import VariantAwarePfisGraph
from patches import *
import os
import sqlite3
from graphAttributes import NodeType
from graphAttributes import EdgeType

class VariantAndEquivalenceAwarePfisGraph(VariantAwarePfisGraph):

	GET_VARIANT_POSITION_QUERY = 'select * from VARIANTS where NAME= ?'
	FETCH_PATCH_FOR_FQN_QUERY_FORMAT = 'select vf.uuid from {} as vf where vf.fqn = ? and start <= ? and end >=?'


	def __init__(self, dbFilePath, langHelper, projSrc, variantsDb, divorcedUntilMarried=False, stopWords=[], goalWords=[], variantOverrides = {}, verbose=False):
		VariantAwarePfisGraph.__init__(self, dbFilePath, langHelper, projSrc, stopWords, goalWords, variantOverrides, verbose)
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
		self._updateEquivalenceInformation(node1, node1Type)
		self._updateEquivalenceInformation(node2, node2Type)

		node1Equivalent = self.getFqnOfEquivalentNode(node1)
		node2Equivalent = self.getFqnOfEquivalentNode(node2)

		if not (edgeType == EdgeType.SIMILAR and node1Equivalent == node2Equivalent): #Happens for equivalent nodes: do not add self loops.
			VariantAwarePfisGraph._addEdge(self, node1Equivalent, node2Equivalent, node1Type, node2Type, edgeType)

	def _updateEquivalenceInformation(self, node, nodeType):
		if nodeType in [NodeType.VARIANT, NodeType.WORD, NodeType.OUTPUT_INFO_FEATURE]: return
		if self.getPatchByFqn(node) is not None: return
		if self.langHelper.isLibMethodWithoutSource(node): return

		if self.langHelper.isNavigablePatch(node):
			newPatch = self.getNewLeafLevelPatch(node)
		else:
			newPatch = self.getNewNonLeafPatch(node)
		if newPatch is None:
			raise Exception("Cannot create representative patch for:", node)

		self.setAsEquivalent(node, newPatch.uuid, newPatch)

	def getNewNonLeafPatch(self, fqn):
		if self.langHelper.isFileFqn(fqn) and \
				not VariantAwarePfisGraph.optionToggles['excludeFileEquivalence']:
			fqn = self.langHelper.fileFqn(fqn)
			filePatch = FilePatch(fqn)
			if self.temporaryMode: return filePatch
			else:
				filePatch.uuid = self.__getEquivalenceUUIDFromDB(filePatch)
				return filePatch
		else: return Patch(fqn)

	def getNewLeafLevelPatch(self, patchFqn):
		if self.langHelper.isMethodFqn(patchFqn):
			newPatch = MethodPatch(patchFqn)
			if not self.temporaryMode:
				if not self.langHelper.isPfigHeaderFqn(patchFqn):
					newPatch.uuid = self.__getEquivalenceUUIDFromDB(newPatch)

		elif self.langHelper.isChangelogFqn(patchFqn):
			newPatch = ChangelogPatch(patchFqn)

		elif self.langHelper.isOutputFqn(patchFqn):
			newPatch = OutputPatch(patchFqn)
			if not self.temporaryMode:
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

	def cloneNode(self, cloneTo, cloneFrom):
		def _cloneAsEquivalent(toNode, fromNode):
			#Set the equivalence first because graph manipulation is based on equivalent FQN.
			self.setAsEquivalent(toNode, self.fqnToIdMap[fromNode])
			VariantAwarePfisGraph.cloneNode(self, toNode, fromNode)

		def _cloneAsNonEquivalent(toNode, fromNode):
			#Set the equivalence first because graph manipulation is based on equivalent FQN.
			tempPatch = self.getNewLeafLevelPatch(toNode)
			self.setAsEquivalent(toNode, tempPatch.uuid, tempPatch)
			VariantAwarePfisGraph.cloneNode(self, toNode, fromNode)

		# Changelog patches are never equivalent, so always create from and to as non-equivalent.
		if self.langHelper.isChangelogFqn(cloneTo):
			_cloneAsNonEquivalent(cloneTo, cloneFrom)

		# For output or source code patches, clone cloneTo as equivalent to cloneFrom or not, based on config.
		elif self.langHelper.isOutputFqn(cloneTo) or self.langHelper.isMethodFqn(cloneTo):
			if self.divorcedUntilMarried:
				_cloneAsNonEquivalent(cloneTo, cloneFrom)
			else:
				_cloneAsEquivalent(cloneTo, cloneFrom)

	def setAsEquivalent(self, fqn, id, equivalentPatch=None):
		if fqn not in self.fqnToIdMap.keys():
			self.fqnToIdMap[fqn] = id
			if self.temporaryMode:
				self.tempNodes.add(fqn)

			if id not in self.idToPatchMap.keys() and equivalentPatch is not None:
				self.idToPatchMap[id] = equivalentPatch

			if self.VERBOSE_BUILD:
				print "Equivalent {0} : {1}".format(fqn, self.idToPatchMap[id].fqn)


	def removeNode(self, nodeFqn):
		if nodeFqn not in self.fqnToIdMap.keys(): #Variant nodes do not have equivalents, and they need to be deleted.
			VariantAwarePfisGraph.removeNode(self, nodeFqn)

		else:
			id = self.fqnToIdMap[nodeFqn]
			self.fqnToIdMap.pop(nodeFqn)
			print "Remove node equivalence: ", nodeFqn


			# If the ID is equivalent of some other other fqn also, removing node from FQNtoID map is enough. So, remove it from temp added nodes list.
			# Otherwise, remove from ID to patch map, and remove the representative node from the graph.

			if id not in self.fqnToIdMap.values(): #It is an orphan entry in idtoPatchMap, so remove.
				patch = self.idToPatchMap[id]
				self.idToPatchMap.pop(id)
				VariantAwarePfisGraph.removeNode(self, patch.fqn)

	def __getEquivalenceUUIDFromDB(self, patch):
		tableNames = {PatchType.METHOD: "VARIANTS_TO_FUNCTIONS", PatchType.FILE: "VARIANTS_TO_FILES"}
		fqn = patch.fqn

		if patch.patchType in tableNames.keys():
			pathRelativeToVariant = self.langHelper.getPathRelativeToVariant(fqn)
			variantName = self.langHelper.getVariantName(fqn)

			conn = sqlite3.connect(self.variantsDb)
			c = conn.cursor()
			c.execute(self.GET_VARIANT_POSITION_QUERY, [variantName])
			variantNum = c.fetchone()[0]

			queryString = self.FETCH_PATCH_FOR_FQN_QUERY_FORMAT.format(tableNames[patch.patchType])
			c.execute(queryString, [pathRelativeToVariant, variantNum, variantNum])

			patchRow = c.fetchone()
			c.close()
			conn.close()

			if patchRow is None:
				raise Exception("Missing patch equivalence:", patch, variantName, variantNum, pathRelativeToVariant)

			uuid = patchRow[0]
			return uuid

	def __getOutputContent(self, patchFqn):
		variant_name = self.langHelper.getVariantName(patchFqn)
		conn = sqlite3.connect(self.variantsOutputDb)
		c = conn.cursor()

		c.execute('SELECT output FROM variant_output WHERE variant=?', [variant_name])

		content = c.fetchone()[0]

		c.close()
		conn.close()

		return content

