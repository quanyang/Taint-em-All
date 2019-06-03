# _*_ coding:utf-8 _*_
"""
example:
$a = $GET['a'];

Output: $a
Result: $a=$GET['a'] //assignment
Argument: $GET['a'] 
"""
from Var import *

class Node(object):
	def __init__(self,fileName,startLine,endLine):
		self.fileName = fileName
		self.startLine = startLine
		self.endLine = endLine
		self.state = ""
	def __str__(self,debug = False):
		if debug:
			return "\tFile: %s\r\n\tStarting Line: %s\r\n\tEnding Line: %s\r\n\tType: %s\r\n\tState: %s\r\n"%(self.fileName,self.startLine,self.endLine,type(self),self.state)
		else:
			return ""
	def __repr__(self):
		return self.__str__()
	def __eq__(self, other):
		if self.fileName != other.fileName:
			return False
		if self.startLine != other.startLine:
			return False
		if self.endLine != other.endLine:
			return False
		if self.state != other.state:
			return False
		return True
	def generateGraphViz(self,debug = False):
		return self.__str__(debug).replace("\r\n","\l").replace("\t","")

class OperandNode(Node):
	def __init__(self,fileName,startLine,endLine):
		self.inputs = []
		self.outputs = []
		self.results = []
		self.scope = None
		Node.__init__(self,fileName,startLine,endLine)
	def setScope(self,scope):
		self.scope = scope
	def setOperand(self,op):
		self.op = op.encode('ascii','xmlcharrefreplace')
		self.operation = '_'.join(op.split("_")[1:]).lower()
	def addArgument(self,source):
		if isinstance(source,list):
			for var in source:
				self.inputs.append(Var.turnSourceIntoVar(var))
		else:
			self.inputs.append(Var.turnSourceIntoVar(source))
	def addOutput(self,sink):
		if isinstance(sink,list):
			self.outputs.extend(map(Var.turnSourceIntoVar,sink))
		else:
			self.outputs.append(Var.turnSourceIntoVar(sink))
	def addResult(self,sink):
		if isinstance(sink,list):
			self.results.extend(map(Var.turnSourceIntoVar,sink))
		else:
			self.results.append(Var.turnSourceIntoVar(sink))
	def __eq__(self, other):
		if not self.inputs.__eq__(other.inputs):
			return False
		if not self.outputs.__eq__(other.outputs):
			return False
		if not self.results.__eq__(other.results):
			return False
		if self.scope != other.scope:
			return False
		return Node.__eq__(self,other)
	def __str__(self,debug = False):
		if self.scope == None:
			return Node.__str__(self,debug)+"\t%s\r\n\tInputs: %s\r\n\tOutputs: %s\r\n\tResults: %s\r\n\r\n"%(self.op,','.join(map(str,self.inputs)),','.join(map(str,self.outputs)),','.join(map(str,self.results)))
		else:
			return Node.__str__(self,debug)+"\t%s\r\n\tScope: %s\r\n\tInputs: %s\r\n\tOutputs: %s\r\n\tResults: %s\r\n\r\n"%(self.op,self.scope,','.join(map(str,self.inputs)),','.join(map(str,self.outputs)),','.join(map(str,self.results)))
	def __repr__(self):
		return self.__str__()

class CastNode(OperandNode):
	def __init__(self,fileName,startLine,endLine):
		OperandNode.__init__(self,fileName,startLine,endLine)
	def __str__(self,debug = False):
			return OperandNode.__str__(self,debug)
	def __repr__(self):
		return self.__str__()		

class AssertionNode(OperandNode):
	def __init__(self,fileName,startLine,endLine):
		self.block = ""
		OperandNode.__init__(self,fileName,startLine,endLine)	
	def setAssertion(self,assertion):
		self.assertion = assertion
	def __str__(self,debug = False):
		return Node.__str__(self,debug)+"\t%s\r\n\tAssertion:%s\r\n\tInputs: %s\r\n\tOutputs: %s\r\n\tResults: %s\r\n\r\n"%(self.op,self.assertion,','.join(map(str,self.inputs)),','.join(map(str,self.outputs)),','.join(map(str,self.results)))
	def __repr__(self):
		return self.__str__()

class StaticNode(OperandNode):
	def __init__(self,fileName,startLine,endLine):
		self.block = ""
		OperandNode.__init__(self,fileName,startLine,endLine)	
	def setBlock(self,block):
		self.block = block
	def __eq__(self, other):
		if self.block != other.block:
			return False
		return OperandNode.__eq__(self, other)
	def __str__(self,debug = False):
		return OperandNode.__str__(self,debug).replace("\r\n\r\n","\r\n")+"\tDefault Block: %s\r\n\r\n"%(self.block)
	def __repr__(self):
		return self.__str__()

class PropertyNode(Node):
	def __init__(self,fileName,startLine,endLine):
		self.var = None
		self.name = None
		self.output = None
		Node.__init__(self,fileName,startLine,endLine)
	def setVar(self,var):
		self.var = Var.turnSourceIntoVar(var)
	def setName(self,name):
		self.name = Var.turnSourceIntoVar(name)
	def setOutput(self,result):
		self.output = Var.turnSourceIntoVar(result)
	def __eq__(self, other):
		if self.var != other.var:
			return False
		if self.name != other.name:
			return False
		if self.output != other.output:
			return False
		return Node.__eq__(self, other)
	def __str__(self,debug = False):
		return Node.__str__(self,debug)+"\tProperty Fetch:\r\n\tVar: %s\r\n\tName: %s\r\n\tOutputs: %s\r\n\r\n"%(str(self.var),str(self.name),str(self.output))
	def __repr__(self):
		return self.__str__()

class ParamNode(Node):
	def __init__(self,fileName,startLine,endLine):
		self.name = None
		self.output = None
		Node.__init__(self,fileName,startLine,endLine)
	def setName(self,name):
		self.name = Var.turnSourceIntoVar(name)
	def setOutput(self,result):
		self.output = Var.turnSourceIntoVar(result)
	def __eq__(self, other):
		if self.name != other.name:
			return False
		if self.output != other.output:
			return False
		return Node.__eq__(self, other)
	def __str__(self,debug = False):
		return Node.__str__(self,debug)+"\tExpr_Param\r\n\tName: %s\r\n\tOutputs: %s\r\n\r\n"%(str(self.name),str(self.output))
	def __repr__(self):
		return self.__str__()

#Nodes that adds a new block
#Seems unique to PHP
class TraitNode(Node):
	def __init__(self,fileName,startLine,endLine):
		self.extends = []
		self.traitName = None
		self.block = None
		Node.__init__(self,fileName,startLine,endLine)	
	def setTraitName(self,traitName):
		self.traitName = traitName
	def setBlock(self,block):
		self.block = block
	def __eq__(self, other):
		if not self.extends.__eq__(other.extends):
			return False
		if self.traitName != other.traitName:
			return False
		if self.block != other.block:
			return False
		return Node.__eq__(self, other)
	def __str__(self,debug = False):
		return Node.__str__(self,debug)+"\tTrait: %s\r\n\tBlock: %s\r\n\r\n"%(self.traitName,self.block)
	def __repr__(self):
		return self.__str__()

class InterfaceNode(Node):
	def __init__(self,fileName,startLine,endLine):
		self.extends = []
		self.interfaceName = None
		self.block = None
		Node.__init__(self,fileName,startLine,endLine)	
	def setInterfaceName(self,interfaceName):
		self.interfaceName = interfaceName
	def setBlock(self,block):
		self.block = block
	def addInheritance(self,parent):
		for i in parent:
			self.extends.append(i['value'])
	def __eq__(self, other):
		if not self.extends.__eq__(other.extends):
			return False
		if self.interfaceName != other.interfaceName:
			return False
		if self.block != other.block:
			return False
		return Node.__eq__(self, other)
	def __str__(self,debug = False):
		return Node.__str__(self,debug)+"\tInterface: %s\r\n\tBlock: %s\r\n\tExtends: %s\r\n\r\n"%(self.interfaceName,self.block,','.join(self.extends))
	def __repr__(self):
		return self.__str__()

class ClassNode(Node):
	def __init__(self,fileName,startLine,endLine):
		self.implements = []
		self.extends = []
		self.className = None
		self.block = None
		Node.__init__(self,fileName,startLine,endLine)	
	def setClassName(self,className):
		self.className = className
	def setBlock(self,block):
		self.block = block
	def addInterface(self,interface):
		for i in interface:
			self.implements.append(i['value'])
	def addInheritance(self,parent):
		self.extends.append(parent)
	def __eq__(self, other):
		if not self.implements.__eq__(other.implements):
			return False
		if not self.extends.__eq__(other.extends):
			return False
		if self.className != other.className:
			return False
		if self.block != other.block:
			return False
		return Node.__eq__(self, other)
	def __str__(self,debug = False):
		return Node.__str__(self,debug)+"\tClass: %s\r\n\tBlock: %s\r\n\tExtends: %s\r\n\tImplements: %s\r\n\r\n"%(self.className,self.block,','.join(self.extends),','.join(self.implements))
	def __repr__(self):
		return self.__str__()

class ClosureNode(Node):
	def __init__(self,fileName,startLine,endLine):
		self.params = []
		self.outputs = []
		self.useVars = []
		self.func = None
		self.block = None
		Node.__init__(self,fileName,startLine,endLine)
	def setFunc(self,op):
		self.func = op
	def setBlock(self,block):
		self.block = block
	def addUseVar(self,var):
		if isinstance(var,list):
			self.useVars.extend(map(Var.turnSourceIntoVar,var))
		else:
			self.useVars.append(Var.turnSourceIntoVar(var))
	def addParam(self,param):
		if isinstance(param,list):
			self.params.extend(map(Var.turnSourceIntoVar,param))
		else:
			self.params.append(Var.turnSourceIntoVar(param))
	def addOutput(self,output):
		if isinstance(output,list):
			self.outputs.extend(map(Var.turnSourceIntoVar,output))
		else:
			self.outputs.append(Var.turnSourceIntoVar(output))
	def __eq__(self, other):
		if not self.params.__eq__(other.params):
			return False
		if not self.outputs.__eq__(other.outputs):
			return False
		if not self.useVars.__eq__(other.useVars):
			return False
		if self.func != other.func:
			return False
		if self.block != other.block:
			return False
		return Node.__eq__(self, other)
	def __str__(self,debug = False):
		return Node.__str__(self,debug)+"\t%s\r\n\tUse vars:%s\r\n\tParams: %s\r\n\tOutput: %s\r\n\tBlock: %s\r\n\r\n"%(self.func,','.join(map(str,self.useVars)),','.join(map(str,self.params)),','.join(map(str,self.outputs)),self.block)
	def __repr__(self):
		return self.__str__()

class FuncNode(Node):
	def __init__(self,fileName,startLine,endLine):
		self.params = []
		self.block = None
		self.name = None
		self.func = None
		Node.__init__(self,fileName,startLine,endLine)
	def setFunc(self,op):
		self.func = op
	def setName(self,name):
		self.name = name
	def setBlock(self,block):
		self.block = block
	def addParam(self,param):
		if isinstance(param,list):
			self.params.extend(map(Var.turnSourceIntoVar,param))
		else:
			self.params.append(Var.turnSourceIntoVar(param))
	def __eq__(self, other):
		if not self.params.__eq__(other.params):
			return False
		if self.block != other.block:
			return False
		if self.name != other.name:
			return False
		if self.func != other.func:
			return False
		return Node.__eq__(self, other)
	def __str__(self,debug = False):
		if self.name != "":
			op = "%s<%s>"%(self.func,self.name)
		else:
			op = self.func
		return Node.__str__(self,debug)+"\t%s\r\n\r\n"%(op)
	def __repr__(self):
		return self.__str__()


#Control Flow Modifying Nodes
class StaticFuncCallNode(OperandNode):
	def __init__(self,fileName,startLine,endLine):
		self.name = None
		OperandNode.__init__(self,fileName,startLine,endLine)
	def setName(self,name):
		self.name = Var.turnSourceIntoVar(name);
	def getName(self):
		name = self.name.__str__(True)
		if "LITERAL(" == name[:8]:
			name = name[9:-2]
		return name
	def __eq__(self, other):
		if not isinstance(other, FuncCallNode):
			return False
		if self.name != other.name:
			return False
		return OperandNode.__eq__(self, other)
	def __str__(self,debug = False):
		if self.name and self.scope:
			op = "%s#%s::%s()"%(self.op,self.scope,self.name.__str__(True))
		else:
			op = self.Operand
		return Node.__str__(self,debug)+"\t%s\r\n\tInputs: %s\r\n\tOutputs: %s\r\n\tResults: %s\r\n\r\n"%(op,','.join(map(str,self.inputs)),','.join(map(str,self.outputs)),','.join(map(str,self.results)))
	def __repr__(self):
		return self.__str__()

class FuncCallNode(OperandNode):
	def __init__(self,fileName,startLine,endLine):
		self.name = None
		OperandNode.__init__(self,fileName,startLine,endLine)
	def setName(self,name):
		self.name = Var.turnSourceIntoVar(name);
	def getScope(self):
		if self.scope == None:
			return self.scope
		scope = self.scope
		if "LITERAL(" == scope[:8]:
			scope = scope[9:-2]
		return scope
	def getName(self):
		name = self.name.__str__(True)
		if "LITERAL(" == name[:8]:
			name = name[9:-2]
		return name
	def __eq__(self, other):
		if not isinstance(other, FuncCallNode):
			return False
		if self.name != other.name:
			return False
		return OperandNode.__eq__(self, other)
	def __str__(self,debug = False):
		if self.name and self.scope:
			op = "%s#%s::%s()"%(self.op,self.scope,self.name.__str__(True))
		elif self.name:
			op = "%s#%s()"%(self.op,self.name.__str__(True))
		else:
			op = self.Operand
		return Node.__str__(self,debug)+"\t%s\r\n\tInputs: %s\r\n\tOutputs: %s\r\n\tResults: %s\r\n\r\n"%(op,','.join(map(str,self.inputs)),','.join(map(str,self.outputs)),','.join(map(str,self.results)))
	def __repr__(self):
		return self.__str__()

class JumpIfNode(Node):
	def setIf(self,target):
		self.ifTarget = target
	def setElse(self,target):
		self.elseTarget = target
	def setCond(self,cond):
		self.cond = Var.turnSourceIntoVar(cond)
	def __eq__(self, other):
		if self.ifTarget != other.ifTarget:
			return False
		if self.elseTarget != other.elseTarget:
			return False
		if self.cond != other.cond:
			return False
		return Node.__eq__(self, other)
	def __str__(self,debug = False):
		return Node.__str__(self,debug)+"\tJumpIf\r\n\tCond: %s\r\n\tIf: %s\r\n\tElse: %s\r\n\r\n"%(self.cond,self.ifTarget,self.elseTarget)
	def __repr__(self):
		return self.__str__()

class SwitchNode(Node):
	def __init__(self,fileName,startLine,endLine):
		self.cases = dict()
		self.cond = ""
		Node.__init__(self,fileName,startLine,endLine)
	def setCond(self,cond):
		self.cond = Var.turnSourceIntoVar(cond)
	def addCase(self,block,case):
		self.cases[Var.turnSourceIntoVar(case)] = block
	def __eq__(self, other):
		if not self.cases.__eq__(other.cases):
			return False
		if self.cond != other.cond:
			return False
		return Node.__eq__(self, other)
	def __str__(self,debug = False):
		representation = ""
		for case,block in sorted(self.cases.items()):
			representation += str(case)+": "+str(block)+"\l"
		return Node.__str__(self,debug)+"\tSwitch\r\n\tCond: %s\r\n%s\r\n\r\n"%(str(self.cond),representation)
	def __repr__(self):
		return self.__str__() 

class JumpNode(Node):
	def setJump(self,target):
		self.target = target
	def __eq__(self, other):
		if self.target != other.target:
			return False
		return Node.__eq__(self, other)
	def __str__(self,debug = False):
		return Node.__str__(self,debug)+"\tJump\r\n\tTarget: %s\r\n\r\n"%self.target
	def __repr__(self):
		return self.__str__()
