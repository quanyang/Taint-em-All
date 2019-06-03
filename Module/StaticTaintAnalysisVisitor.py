import copy,os
from Policy.WP_PHPTaintPolicy import *
from Engine.PHPEngine import *
from Visitor.Visitor import Visitor
from Model.Node import *

name = "Static Taint Analysis Visitor"
prereq = None
class StaticTaintAnalysisVisitor(Visitor):
    def __init__(self):
        self.analyzedLines = {}
        self.taintedSink = []
        self.taintedSinkLines = []
        self.policy = TaintPolicy()
        self.pathTaken = []
        Visitor.__init__(self,0)
    def enterBlock(self, traverser, (block,blockId,CFG,forestKey,prevBlock)):
        propagatedState = block.incomingState
        initialState = copy.deepcopy(block.initialState)
        # Checks if the state of block is the same as previous initial state
        # i.e. fixed point theorem
        sameState = True
        for var,value in propagatedState.items():
            if var in initialState:
                sameState = (initialState[var] == value) & sameState
                initialState[var] = (initialState[var][0] | value[0],initialState[var][1] | value[1])
            else:
                initialState[var] = value
                sameState = False
        if not sameState:
            traverser.visited = dict()
        block.initialState = initialState
        block.state = copy.deepcopy(initialState)

    def enterNode(self, traverser, (node,block,blockId,CFG,forestKey,prevBlock)):
        if node.startLine != "None":
            self.analyzedLines[node.startLine] = True
        if isinstance(node,JumpNode):
            targetBlock = CFG.blocks[int(node.target)-1]
            targetBlock.incomingState = block.state
        elif isinstance(node,SwitchNode):
            for case,target in sorted(node.cases.items()):
                targetBlock = CFG.blocks[int(target)-1]    
                targetBlock.incomingState = block.state
        elif isinstance(node,JumpIfNode):
            targetBlock = CFG.blocks[int(node.ifTarget)-1]
            targetBlock.incomingState = block.state
            targetBlock = CFG.blocks[int(node.elseTarget)-1]
            targetBlock.incomingState = block.state

    def leaveNode(self, traverser, (node,block,blockId,CFG,forestKey,prevBlock)):
        pass
        # if isinstance(node,OperandNode):
        #     if "Phi" in node.op:
        #         phiVarIndex = block.parent.index(prevBlock)
        #         if phiVarIndex >= len(node.inputs):
        #             phiVarIndex = len(node.inputs) - 1
        #         phiVar = node.inputs[phiVarIndex]
        #         block.state[node.outputs[0]] = block.state[phiVar]

    def enterOp(self, traverser, (node, block, CFG)):
        name = None
        if isinstance(node,FuncCallNode):
            name = node.getName()
            scope = node.getScope()
            if scope != None:
                name = "%s::%s"%(scope,name)
        if isinstance(node,FuncCallNode) and (name in traverser.customFunction or traverser.CFGForest.getCFG(name) != None):
            # Mapping arguments to CFG
            # Taint propagation for custom defined function. Propagates return value state back as well.
            newState = dict()
            targetCfg = traverser.CFGForest.getCFG(name)
            if targetCfg:
                for index,value in enumerate(node.inputs):
                    if value in block.state:
                        newState[targetCfg.arguments[index]] = block.state[value]
                targetCfg.blocks[0].incomingState = newState
                targetCfg.blocks[0].initialState = newState
        elif isinstance(node,OperandNode) and node.operation == "include":
            self.taintOnOperation(node,block.state)
            if len(node.inputs) > 0 and node.inputs[0].value != None and False:
                targetPath = os.path.basename(getLiteralValue(node.inputs[0].value))
                targetCfg = "%s_%s"%("main",targetPath)
                targetCfg = traverser.CFGForest.getCFG(targetCfg)
                targetBlock = targetCfg.blocks[0]
                if targetBlock:
                    targetBlock.initialState = block.state

    def leaveOp(self, traverser, (node, block, CFG)):
        name = None
        if isinstance(node,FuncCallNode):
            name = node.getName()
            scope = node.getScope()
            if scope != None:
                name = "%s::%s"%(scope,name)

        if isinstance(node,FuncCallNode) and (name in traverser.customFunction or traverser.CFGForest.getCFG(name) != None):
            targetCfg = traverser.CFGForest.getCFG(name)
            targetBlock = targetCfg.blocks[0]
            for output in node.outputs:
                # If the return value is not in the taint states, probably LITERAL(NULL).
                for returnVar,returningBlock in targetCfg.returnVariables:
                    if returnVar not in returningBlock.state:
                        returningBlock.state[returnVar] = (False, set())
                    if output not in block.state:
                        block.state[output] = (False, set())
                    block.state[output] = (returningBlock.state[returnVar][0] | block.state[output][0], returningBlock.state[returnVar][1] | block.state[output][1])
        elif isinstance(node,OperandNode) and node.operation == "return" and len(node.inputs) > 0:
            CFG.returnVariables.append((node.inputs[0],block))
            self.taintOnOperation(node,block.state)
        elif isinstance(node,FuncCallNode) and node.getName() in self.policy.propagator and node.getScope == None:
            self.taintNativePropagatingFunction(node,block)
        elif isinstance(node,OperandNode):
            self.taintOnOperation(node,block.state)

    def taintNativePropagatingFunction(self, node, block):
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
                if "Expr_BinaryOp_" == operation.op[:14]:
                    for propagateVar in operation.results:
                        if propagateVar in state:
                            state[propagateVar] = (state[var][0] | state[propagateVar][0],state[var][1] & state[propagateVar][1])
                        else:
                            state[propagateVar] = state[var]

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

                if tainted and not operation.startLine in self.taintedSinkLines:
                    self.taintedSink.append(operation)
                    self.taintedSinkLines.append(operation.startLine)
                    operation.state = "*Dangerous: Tainted Input(s). Possible %s*"%(getattr(self.policy,"NAME%s"%taintSink[1:]))

        #not sure if results should be tainted as well atm.
        for var in operation.results:
            if var not in state:
                state[var] = (False,set())

