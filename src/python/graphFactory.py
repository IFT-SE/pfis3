from pfisGraph import PfisGraph
from pfisGraphWithVariants import PfisGraphWithVariants

class GraphFactory:
	def __init__(self, langHelper, dbPath, projSrcPath, stopWords=[]):
		self.langHelper = langHelper
		self.dbPath = dbPath
		self.projSrcPath = projSrcPath
		self.stopWords = stopWords

	def getGraph(self, graphType):
		if graphType == None:
			graphType = "PfisGraph"

		if graphType.lower() == "PfisGraph".lower():
			return PfisGraph(self.dbPath, self.langHelper, self.projSrcPath, self.stopWords)
		if graphType.lower() == "PfisGraphWithVariants".lower():
			return PfisGraphWithVariants(self.dbPath, self.langHelper, self.projSrcPath, self.stopWords)