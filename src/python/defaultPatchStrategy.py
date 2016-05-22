from patches import MethodPatch
class DefaultPatchStrategy(object):

	def getMethodInMethodList(self, methodFqn, methodList):
		# Return the method data object in the list that matches the desired FQN
		for method in methodList:
			if method.fqn == methodFqn:
				return method
		return None

	def appendMethodPatch(self, filePathOrFqn, methodList):
		methodList.append(MethodPatch(filePathOrFqn))