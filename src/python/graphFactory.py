from pfisGraph import PfisGraph
from pfisGraphWithVariants import PfisGraphWithVariants
from pfisGraphWithSimilarPatches import PfisGraphWithSimilarPatches

class GraphFactory:
	def __init__(self, langHelper, dbPath, projSrcPath, stopWords=[]):
		self.langHelper = langHelper
		self.dbPath = dbPath
		self.projSrcPath = projSrcPath
		self.stopWords = stopWords

	def getGraph(self, graphType, variantsDb):
		if graphType == None:
			graphType = "PfisGraph"

		if graphType.lower() == "PfisGraph".lower():
			return PfisGraph(self.dbPath, self.langHelper, self.projSrcPath, self.stopWords)

		if graphType.lower() == "PfisGraphWithVariants".lower():
			return PfisGraphWithVariants(self.dbPath, self.langHelper, self.projSrcPath, self.stopWords)

		if graphType.lower() == "PfisGraphWithSimilarPatches".lower():
			if variantsDb is None:
				raise Exception("Missing attrib: variantsDb for graphType PfisGraphWithSimilarPatches in XML config file.")
			return PfisGraphWithSimilarPatches(self.dbPath, self.langHelper, self.projSrcPath, variantsDb, self.stopWords)