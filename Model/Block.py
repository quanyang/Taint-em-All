"""
Block contains many nodes which can be operations or etc
"""
from Node import *
class Block(object):
	def __init__(self,blockId):
		self.liveVars = set()
		self.vars = set()

		# Used by symbolic execution
		self.pathReachable = True
		self.imprecise = False
		self.pathConstraint = [True]

		self.incomingState = dict()
		self.initialState = dict()
		self.state = dict()

		self.nodes = []
		self.parent = []
		self.arguments = []
		self.blockId = blockId

		self.analysisState = dict()
		
	def addParent(self, parentBlockId):
		self.parent.append(parentBlockId)

	def addNode(self,node):
		self.nodes.append(node)

	def __str__(self):
		nodes_output = ""
		for node in self.nodes:
			nodes_output += str(node)
		return "Block: %s\r\nParent: %s\r\nPath Constraint: %s\r\nOperands: \r\n%s"%(self.blockId,self.parent,self.pathConstraint,nodes_output)

	def __repr__(self):
		return self.__str__()

	def __eq__(self, other):
		if other == None:
			return False
		if not self.liveVars.__eq__(other.liveVars):
			return False
		if not self.state.__eq__(other.state):
			return False
		if not self.nodes.__eq__(other.nodes):
			return False
		if not self.parent.__eq__(other.parent):
			return False
		if not self.arguments.__eq__(other.arguments):
			return False
		if self.blockId != other.blockId:
			return False
		return True

	def generateGraphViz(self,debug = False,name = ""):
		node_formatting = ""
		control_flow = ""
		for node in self.nodes:
			node_formatting += node.generateGraphViz(debug)
			if isinstance(node,JumpNode):
				control_flow += "\"%s_block_%s\" -> \"%s_block_%s\" [\r\nlabel=\"target\"\r\n]\r\n"%(name,self.blockId,name,node.target)
			elif isinstance(node,JumpIfNode):
				control_flow += "\"%s_block_%s\" -> \"%s_block_%s\" [\r\nlabel=\"if\"\r\n]\r\n"%(name,self.blockId,name,node.ifTarget)
				control_flow += "\"%s_block_%s\" -> \"%s_block_%s\" [\r\nlabel=\"else\"\r\n]\r\n"%(name,self.blockId,name,node.elseTarget)
			elif isinstance(node,ClassNode):
				control_flow += "\"%s_block_%s\" -> \"%s_block_%s\" [\r\nlabel=\"%s\"\r\n]\r\n"%(name,self.blockId,name,node.block,node.className)
			elif isinstance(node,StaticNode):
				control_flow += "\"%s_block_%s\" -> \"%s_block_%s\" [\r\nlabel=\"Block\"\r\n]\r\n"%(name,self.blockId,name,node.block)
			elif isinstance(node,InterfaceNode):
				control_flow += "\"%s_block_%s\" -> \"%s_block_%s\" [\r\nlabel=\"%s\"\r\n]\r\n"%(name,self.blockId,name,node.block,node.interfaceName)
			elif isinstance(node,TraitNode):
				control_flow = "\"%s_block_%s\" -> \"%s_block_%s\" [\r\nlabel=\"%s\"\r\n]\r\n"%(name,self.blockId,name,node.block,node.traitName)
			elif isinstance(node,SwitchNode):
				for case,target in sorted(node.cases.items()):
					control_flow += "\"%s_block_%s\" -> \"%s_block_%s\" [\r\nlabel=\"%s\"\r\n]\r\n"%(name,self.blockId,name,target,case)
		if debug:
			# This should not be here, the classes should be agnostic from the analysis modules.
			# Use visitor class to abstract this portion
			if len(self.state) > 0:
				debugState = ""
				for label,state in sorted(self.state.items()):
					# Filter away literals
					if not label.isLiteral() and label in self.liveVars:
						debugState += str(label)+": "+str(state)+"\l"
				initial = ""
				for label,state in sorted(self.initialState.items()):
					if not label.isLiteral() and label in self.liveVars:
						initial += str(label)+": "+str(state)+"\l"
				output = "\"%s_block_%d\" [\r\nlabel=\"block_%s\l\lInitial State:\l%s\lPost State:\l%s\l%s\"\r\nshape=\"rect\"\r\n]\r\n%s"%(name,self.blockId,self.blockId,initial,debugState,node_formatting,control_flow)
			else:
				live = '\l'.join([str(i) for i in sorted(self.liveVars)])
				output = "\"%s_block_%d\" [\r\nlabel=\"block_%s\l\lLive Vars:\l%s\l\l%s\"\r\nshape=\"rect\"\r\n]\r\n%s"%(name,self.blockId,self.blockId,live,node_formatting,control_flow)
		else:
			output = "\"%s_block_%d\" [\r\nlabel=\"block_%s\l%s\"\r\nshape=\"rect\"\r\n]\r\n%s"%(name,self.blockId,self.blockId,node_formatting,control_flow)
		return output
