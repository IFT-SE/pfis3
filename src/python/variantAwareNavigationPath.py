from navpath import NavigationPath

class VariantAwareNavigationPath(NavigationPath):

	def __init__(self, dbFilePath, langHelper, projectFolderPath, verbose = False):
		NavigationPath.__init__(self, dbFilePath, langHelper, projectFolderPath, verbose)
		self._variantAwareNavigations = []


	# def getLength(self):
	# 	return len(self._variantAwareNavigations)
	#
	# def getNavigation(self, i):
	# 	return self._variantAwareNavigations[i]