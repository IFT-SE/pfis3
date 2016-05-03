from pfisGraph import PfisGraph

class GraphFactory:
	def __init__(self, langHelper, dbPath, projSrcPath, stopWords=[]):
		self.langHelper = langHelper
		self.dbPath = dbPath
		self.projSrcPath = projSrcPath
		self.stopWords = stopWords

	def getGraph(self, graphType = "PfisGraph"):
		if graphType.lower() == "pfisgraph": return PfisGraph(self.dbPath, self.langHelper, self.projSrcPath, self.stopWords)