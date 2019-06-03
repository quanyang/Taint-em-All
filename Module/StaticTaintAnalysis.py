from Policy.PHPTaintPolicy import *
from Engine.PHPEngine import *
from Model.Node import *
import copy
#name = "Static Taint Analysis"
prereq = None

class StaticTaintAnalysis:
	def __init__(self):
		self.policy = TaintPolicy()
		self.taintedSink = []
		self.visited = dict()
		self.customFunction = dict()
		self.CFGForest = None

	def taintAnalysisOnCFGForest(self,CFGForest,blockId):
		self.CFGForest = copy.deepcopy(CFGForest)
		taintState = dict()
		# Start taint analysis on block with blockId of every CFGForest.
		# So that if there's a disconnected graph we still attempt to analyze every block.
		#for forestKey,cfg in self.CFGForest.forest.iteritems():
		self.recurseBlockTaintAnalysis(self.CFGForest.getCFG("main"), 0, taintState, "main")
		return (self.CFGForest,self.taintedSink)

	def recurseBlockTaintAnalysis(self,CFG,blockId,propagatedState,forestKey):
		if len(CFG.blocks) <= blockId:
			return
		block = CFG.blocks[blockId]
		propagatedState = copy.deepcopy(propagatedState)
		initialState = copy.deepcopy(block.initialState)
		sameState = True
		for var,value in propagatedState.items():
			if var in block.initialState:
				sameState = (initialState[var] == value) & sameState
				initialState[var] = (initialState[var][0] | value[0],initialState[var][1] | value[1])
			else:
				initialState[var] = value
				sameState = False
		if not sameState:
			self.visited = dict()

		returnVariable = None

		block.initialState = initialState
		block.state = copy.deepcopy(initialState)
		for node in block.nodes:
			if isinstance(node,FuncNode):
				# Mark for custom defined functions
				self.customFunction[node.name] = True
			if isinstance(node,FuncCallNode) and node.getName() in self.customFunction:
				# Custom defined function taint propagation. Propagates return value state back as well.
				newState = dict()
				targetBlock = self.CFGForest.getCFG(node.getName())
				if targetBlock:
					for index,value in enumerate(node.inputs):
						if value in block.state:
							newState[targetBlock.arguments[index]] = block.state[value]
					funcCallPostState,funcCallOutput = self.recurseBlockTaintAnalysis(targetBlock,0,newState,node.getName())
				for output in node.outputs:
					# If the return value is not in the taint states, probably LITERAL(NULL).
					if funcCallOutput not in funcCallPostState:
						funcCallPostState[funcCallOutput] = (False, set())
					block.state[output] = funcCallPostState[funcCallOutput]
			elif isinstance(node,FuncCallNode) and node.getName() in self.policy.propagator:
				# If function propagates state of certain argument to another argument.
				variablesToTaint = self.policy.propagator[node.getName()][0]
				fromVariables = self.policy.propagator[node.getName()][1]
				taintState = False
				
				if fromVariables[0] == 0:
					for argument in node.inputs:
						taintState = taintState | block.state[argument][0]
				else:
					for index in fromVariables:
						taintState = taintState | block.state[node.inputs[index-1]][0]
				for varIndex in variablesToTaint:
					block.state[node.inputs[varIndex-1]] = (taintState,set())
			elif isinstance(node,OperandNode) and node.operation == "return" and len(node.inputs) > 0:
				# By default return value is literal(1)
				# Assume: only 1 variable in node.inputs
				# Can there be more than 1 variable for return?
				self.taintOnOperation(node,block.state)
				returnVariable = node.inputs[0]
			elif isinstance(node,OperandNode) and node.operation == "globalvar":
				# To-do: Need to map globalstate to block.state. However, how do we obtain the var of the affected variable.
				self.taintOnOperation(node,block.state)
				pass
			elif isinstance(node,OperandNode) and node.operation == "include":
				
				# Inclusion affects control flow.
				self.taintOnOperation(node,block.state)
				if len(node.inputs) > 0 and node.inputs[0].value != None:
					targetPath = os.path.basename(getLiteralValue(node.inputs[0].value))
					targetCfg = "%s_%s"%("main",targetPath)
					targetBlock = self.CFGForest.getCFG(targetCfg)
					if targetBlock:
						newState = dict()
						# i can iterate and get all used variables and then map accordingly
						# do the same for the edge back
						# or find a way to move all variable numbering back
						self.recurseBlockTaintAnalysis(targetBlock,0,block.state,targetCfg)

			elif isinstance(node,OperandNode):
				self.taintOnOperation(node,block.state)
			# The next 3 conditions affects control flow
			elif isinstance(node,JumpNode):
				edge = (blockId,int(node.target)-1,forestKey)
				if not edge in self.visited:
					self.visited[edge] = True
					self.recurseBlockTaintAnalysis(CFG,int(node.target)-1,block.state,forestKey)
			elif isinstance(node,SwitchNode):
				for case,target in sorted(node.cases.items()):
					edge = (blockId,int(target)-1,forestKey)
					if not edge in self.visited:
						self.visited[edge] = True
						self.recurseBlockTaintAnalysis(CFG,int(target)-1,block.state,forestKey)
			elif isinstance(node,JumpIfNode):
				edge = (blockId,int(node.ifTarget)-1,forestKey)
				if not edge in self.visited:
					self.visited[edge] = True
					self.recurseBlockTaintAnalysis(CFG,int(node.ifTarget)-1,block.state,forestKey)
				edge = (blockId,int(node.elseTarget)-1,forestKey)
				if not edge in self.visited:
					self.visited[edge] = True
					self.recurseBlockTaintAnalysis(CFG,int(node.elseTarget)-1,block.state,forestKey)

		return block.state,returnVariable


	def taintOnOperation(self,operation,state):
		#Checks for sanitizer
		isSanitizer = False
		# Check for sanitizer in CAST operations.
		if isinstance(operation,CastNode):
			for sanitizer in self.policy.sanitizer.FUNC_LIST:
				if operation.op in getattr(self.policy.sanitizer,sanitizer):
					isSanitizer = True
					for propagateVar in operation.outputs:
						state[propagateVar] = (False,set())
		if isinstance(operation,FuncCallNode):
			function = operation.getName()
			for taintSource in self.policy.source.FUNC_LIST:
				if function in getattr(self.policy.source,taintSource):
					for propagateVar in operation.outputs:
						state[propagateVar] = (True,set())
				#can break if found
			for sanitizer in self.policy.sanitizer.FUNC_LIST:
				if function in getattr(self.policy.sanitizer,sanitizer):
					isSanitizer = True
					for propagateVar in operation.outputs:
						state[propagateVar] = (False,set())
				#can break if found
			for sanitizer in self.policy.sanitizer.CONDITIONAL_FUNC_LIST:
				if function in getattr(self.policy.sanitizer,sanitizer):
					isSanitizer = True
					for propagateVar in operation.outputs:
						state[propagateVar] = (False,{function})
				#can break if found

		if not isSanitizer:
			for var in operation.inputs:
				if not var in state:
					state[var] = (False,set())
					#check if the input is from a taint source. $_GET or $_POST etc.
					if var.name != "" :
						source = var.name
						for taintSource in self.policy.source.VAR_LIST:
							if source in getattr(self.policy.source,taintSource):
								state[var] = (True,set())
				#propagate taint result to outputs
				# Look for false positives**
				# All operations that are not in sanitizer list would propagate from input to output.
				for propagateVar in operation.outputs:
					if propagateVar in state:
						state[propagateVar] = (state[var][0] | state[propagateVar][0],state[var][1] & state[propagateVar][1])
					else:
						state[propagateVar] = state[var]

		#Check for tainted sinks
		for taintSink in self.policy.sink.FUNC_LIST:
			op = operation.operation
			if isinstance(operation,FuncCallNode):
				op = operation.getName()
			#get sink policy
			if op in getattr(self.policy.sink,taintSink):
				status = getattr(self.policy.sink,taintSink)[op]
				tainted = False
				if status[0][0] == 0:
					for var in operation.inputs:
						taintState = (len(set(status[1]) & state[var][1]) == 0) & state[var][0]
						tainted = tainted | taintState
				else:
					for index in status[0]:
						if len(operation.inputs) >= index:
							taintState = (len(set(status[1]) & state[operation.inputs[index-1]][1]) == 0) & state[operation.inputs[index-1]][0]
							tainted = tainted | taintState

				if tainted and not operation in self.taintedSink:
					self.taintedSink.append(operation)
					operation.state = "*Dangerous: Tainted Input(s). Possible %s*"%(getattr(self.policy,"NAME%s"%taintSink[1:]))

		#not sure if results should be tainted as well atm.
		for var in operation.results:
			if var not in state:
				state[var] = (False,set())

