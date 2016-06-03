from pfisGraph import PfisGraph
from pfisGraphWithVariants import PfisGraphWithVariants
from pfisGraphWithSimilarPatches import PfisGraphWithSimilarPatches

class GraphFactory:
	def __init__(self, langHelper, dbPath, projSrcPath, stopWords=[], variantsDb=None):
		self.langHelper = langHelper
		self.dbPath = dbPath
		self.projSrcPath = projSrcPath
		self.stopWords = stopWords
		self.variantsDb = variantsDb

	def getGraph(self, graphType):
		if graphType == None:
			graphType = "PfisGraph"

		if graphType.lower() == "PfisGraph".lower():
			return PfisGraph(self.dbPath, self.langHelper, self.projSrcPath, self.stopWords)
		if graphType.lower() == "PfisGraphWithVariants".lower():
			return PfisGraphWithVariants(self.dbPath, self.langHelper, self.projSrcPath, self.stopWords)
		if graphType.lower() == "PfisGraphWithSimilarPatches".lower():
			return PfisGraphWithSimilarPatches(self.dbPath, self.langHelper, self.projSrcPath, self.variantsDb, self.stopWords)