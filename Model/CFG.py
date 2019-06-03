"""
CFG has many blocks
blocks has many nodes
nodes may jump into blocks (if else)


"""
class CFG(object):
	def __init__(self):
		self.startingBlockIndex = 0
		self.blocks = []
		self.arguments = []
		self.vars = set()
		self.name = None
		self.returnVariables = []

	def setName(self,name):
		self.name = name

	def addBlock(self,block):
		self.blocks.append(block)

	def addVars(self,var):
		self.vars.add(var)

	def addArgument(self,argument):
		self.arguments.append(argument)

	def __str__(self):
		return self.printCFG()

	def __eq__(self, other):
		if not self.arguments.__eq__(other.arguments):
			return False
		if not self.vars.__eq__(other.vars):
			return False
		if self.name != other.name:
			return False
		if not self.blocks.__eq__(other.blocks):
			return False
		return True

	def printCFG(self):
		output = ""
		for block in self.blocks:
			output += str(block)
		return output

	def generateGraphViz(self,debug=False):
		block_formatting = ""
		block_formatting += "\"%s_header\" -> \"%s_block_1\" [\r\n]\r\n"%(self.name,self.name)
		block_formatting += "\"%s_header\" [\r\nlabel=\"Function %s:\"\r\nshape=\"rect\"\r\n]\r\n"%(self.name,self.name)
		for block in self.blocks:
			block_formatting += block.generateGraphViz(debug,self.name)
		output = "%s"%block_formatting
		return output