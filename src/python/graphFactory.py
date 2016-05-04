from pfisGraph import PfisGraph
from pfisGraphWithVariants import PfisGraphWithVariants

class GraphFactory:
	def __init__(self, langHelper, dbPath, projSrcPath, stopWords=[]):
		self.langHelper = langHelper
		self.dbPath = dbPath
		self.projSrcPath = projSrcPath
		self.stopWords = stopWords

	def getGraph(self, graphType = "PfisGraph"):
		if graphType.lower() == "PfisGraph".lower():
			print "PfisGraph !!!"
			return PfisGraph(self.dbPath, self.langHelper, self.projSrcPath, self.stopWords)
		if graphType.lower() == "PfisGraphWithVariants".lower():
			print "PfisGraphWithVariants !!!"
			return PfisGraphWithVariants(self.dbPath, self.langHelper, self.projSrcPath, self.stopWords)