import copy,os,string,itertools,types
from z3 import *
from Common.Commons import *
from Policy.PHPTaintPolicy import *
from Engine.PHPEngine import *
from Visitor.Visitor import Visitor
from Model.Node import *

"""
Got to read up on symbolic execution again.
Looking at decidable set of operations
Always reduce to CNF.

SymbolicExpression
PathConstraint
"""
name = "Symbolic Execution Visitor"
prereq = None
class SymbolicExecutionVisitor(Visitor):
    def __init__(self):
        self.policy = TaintPolicy()
        self.analyzedLines = {}
        self.imprecise = False

        self.maximumLoop = 10
        self.exitLoopBlock = None

        self.symbolGeneratorLength = 1
        self.symbolGenerator = itertools.product(string.lowercase, repeat=self.symbolGeneratorLength)

        self.traverser = None
        self.listOfVariables = {"__builtins__":None, "True": True, "False": False}

        self.state = {}
        # Required functions from z3py
        self.listOfVariables['And'] = And
        self.listOfVariables['Not'] = Not
        self.listOfVariables['WildCard'] = Bool('WildCard')
        Visitor.__init__(self,0)

    def enterForest(self, traverser, forest):
        traverser.state['symbolMap'] = dict()
        traverser.state['symbolIsAssignedMap'] = dict()
        traverser.state['symbolicMap'] = dict()

        self.traverser = traverser

    def enterBlock(self, traverser, (block,blockId,CFG,forestKey,prevBlock)):
        edge = (blockId,forestKey)
        if block == self.exitLoopBlock:
            self.exitLoopBlock = None
        if edge in self.state:
            if self.traverser.state['symbolicMap'] != self.state[edge]:
                pass

    def enterNode(self, traverser, (node,block,blockId,CFG,forestKey,prevBlock)):
        if node.startLine != "None" and not block.imprecise:
            self.analyzedLines[node.startLine] = True
        if isinstance(node,OperandNode):
            if "Phi" in node.op:
                phiVarIndex = block.parent.index(prevBlock)
                if phiVarIndex >= len(node.inputs):
                    phiVarIndex = len(node.inputs) - 1
                phiVar = node.inputs[phiVarIndex]
                self.traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.outputs[0])] = self.traverser.state['symbolicMap'][self.createSymbolIfNotFound(phiVar)]
                if self.createSymbolIfNotFound(phiVar) in self.traverser.state['symbolIsAssignedMap']:
                    self.traverser.state['symbolIsAssignedMap'][self.createSymbolIfNotFound(node.outputs[0])] = True
        if isinstance(node,SwitchNode):
            prevConstraint = block.pathConstraint
            for case,target in sorted(node.cases.items()):
                targetBlock = CFG.blocks[int(target)-1] 
                if not targetBlock:
                    continue
                edge = (blockId, forestKey)
                if self.traverser.visitedBlock[edge] > self.maximumLoop:
                    targetBlock.pathReachable = False
                    continue
                if str(case) == "default":
                    targetBlock.pathConstraint = prevConstraint
                    targetBlock.pathReachable = True
                    continue
                currConstraint = [("(%s == %s)"%(self.traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.cond)], self.traverser.state['symbolicMap'][self.createSymbolIfNotFound(case)]))]
                if targetBlock:
                    targetBlock.pathConstraint, targetBlock.pathReachable, targetBlock.imprecise = self.testConstraintSatisfiable(prevConstraint + currConstraint)
                    targetBlock.imprecise = block.imprecise | targetBlock.imprecise
                    if edge not in self.traverser.visitedBlock or self.traverser.visitedBlock[edge] == self.maximumLoop:
                        self.traverser.visitedBlock[(int(target)-1,forestKey)] = self.maximumLoop - 1
                        targetBlock.imprecise = True
                        targetBlock.pathReachable = True

        elif isinstance(node,JumpNode):
            prevConstraint = block.pathConstraint
            jumpTarget = CFG.blocks[int(node.target)-1]
            # Must exist, but just check incase.
            if jumpTarget:
                jumpTarget.pathConstraint = prevConstraint
        elif isinstance(node,JumpIfNode):
            prevConstraint = block.pathConstraint
            currConstraint = self.generatePathConstraint(self.createSymbolIfNotFound(node.cond))
            ifTarget = CFG.blocks[int(node.ifTarget)-1]
            elseTarget = CFG.blocks[int(node.elseTarget)-1]
            if node in self.state and self.state[node] != currConstraint:
                self.traverser.visited = {}
            self.state[node] = currConstraint
            edge = (blockId, forestKey)
            if edge in self.traverser.visitedBlock and self.traverser.visitedBlock[edge] > self.maximumLoop:
                ifTarget.pathReachable = False
                elseTarget.pathReachable = False
                self.traverser.visitedBlock = {}
                self.traverser.isLooping = False
                ifTarget.imprecise = False
                elseTarget.imprecise = False
                return
            if ifTarget == elseTarget and ifTarget:
                ifTarget.pathConstraint = prevConstraint
                ifTarget.pathReachable = True
                return
            if ifTarget:
                ifTarget.pathConstraint, ifTarget.pathReachable, ifTarget.imprecise = self.testConstraintSatisfiable(prevConstraint + currConstraint)
                ifTarget.imprecise = block.imprecise | ifTarget.imprecise
                if edge in self.traverser.visitedBlock and self.traverser.visitedBlock[edge] == self.maximumLoop:
                    ifEdge = (int(node.ifTarget)-1,forestKey)
                    if self.exitLoopBlock == None:
                        if ifEdge not in self.traverser.visitedBlock or self.traverser.visitedBlock[ifEdge] != self.maximumLoop - 1:
                            self.exitLoopBlock = ifTarget
                    if self.exitLoopBlock != None and self.exitLoopBlock != ifTarget:
                        self.traverser.visitedBlock[ifEdge] = self.maximumLoop - 1
                        ifTarget.imprecise = True
                    ifTarget.pathReachable = True

            if elseTarget:
                elseTarget.pathConstraint, elseTarget.pathReachable, elseTarget.imprecise = self.testConstraintSatisfiable(prevConstraint + [self.negateConstraint(currConstraint)])
                elseTarget.imprecise = block.imprecise | elseTarget.imprecise
                if edge in self.traverser.visitedBlock and self.traverser.visitedBlock[edge] == self.maximumLoop:
                    elseEdge = (int(node.elseTarget)-1,forestKey)
                    if self.exitLoopBlock == None:
                        if elseEdge not in self.traverser.visitedBlock or self.traverser.visitedBlock[elseEdge] != self.maximumLoop - 1:
                            self.exitLoopBlock = elseTarget
                    if self.exitLoopBlock != None and self.exitLoopBlock != elseTarget:
                        elseTarget.imprecise = True
                    elseTarget.pathReachable = True


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
                    if str(returnVar) in self.traverser.state['symbolMap']:
                        self.traverser.state['symbolicMap'][self.createSymbolIfNotFound(output)] = self.traverser.state['symbolicMap'][self.createSymbolIfNotFound(returnVar)]

    def enterOp(self, traverser, (node, block, CFG)):
        op = node.op
        name = None
        if isinstance(node,FuncCallNode):
            name = node.getName()
            scope = node.getScope()
            if scope != None:
                name = "%s::%s"%(scope,name)

        if isinstance(node,FuncCallNode) and (name in traverser.customFunction or traverser.CFGForest.getCFG(name) != None):
            # Mapping arguments to CFG
            # Propagate symbolic repr and path constraint, but keep backup of original values.
            # This is to prevent issues when variables are coincidentally the same between functions.
            newState = dict()
            targetCfg = traverser.CFGForest.getCFG(name)
            block.tempSymbolicMap = copy.deepcopy(self.traverser.state['symbolicMap'])
            block.tempSymbolMap = copy.deepcopy(self.traverser.state['symbolMap'])
            if targetCfg:
                for index,value in enumerate(node.inputs):
                    if str(value) not in self.traverser.state['symbolMap']:
                        #Assume only possible for literals
                        self.createSymbolIfNotFound(value)
                    self.traverser.state['symbolicMap'][self.createSymbolIfNotFound(targetCfg.arguments[index])] = self.traverser.state['symbolicMap'][self.createSymbolIfNotFound(value)]
        if op[:14] == 'Expr_BinaryOp_':
            self.createSymbolForBinaryOp(node, traverser)
        elif op == "Iterator_Valid":
            self.traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.results[0])] = 'NOT IMPLEMENTED'
        elif op == 'Expr_Isset':
            if self.createSymbolIfNotFound(node.inputs[0]) not in traverser.state['symbolIsAssignedMap']:
                self.traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.results[0])] = 'False'
            else:
                self.traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.results[0])] = 'WildCard==True'
        elif op == 'Expr_Cast_Bool':
            traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.outputs[0])] = traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.inputs[0])]
        elif op == 'Expr_ConcatList':
            inputs = []
            for i in node.inputs:
                inputs.append("%s"%traverser.state['symbolicMap'][self.createSymbolIfNotFound(i)])
            traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.outputs[0])] = "%s"%' + '.join(inputs)
        elif op == 'Expr_Assign':
            # input might already have a symbolic expression.
            traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.results[0])] = self.createSymbolIfNotFound(node.results[0])
            traverser.state['symbolIsAssignedMap'][self.createSymbolIfNotFound(node.outputs[0])] = True
            traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.outputs[0])] = traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.inputs[0])]
        elif op == "Expr_ArrayDimFetch":
            # inputs wouldn't have a symbol and would be the simplest form already.
            var = "Var#%s<$%s>"%(node.inputs[0].id,node.inputs[0].name)
            if node.inputs[0].name in self.policy.source.V_USERINPUT or self.createSymbolIfNotFound(var) in traverser.state['symbolIsAssignedMap']:
                traverser.state['symbolIsAssignedMap'][self.createSymbolIfNotFound(node.outputs[0])] = True
            traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.outputs[0])] = self.createSymbolIfNotFound(node.inputs[0])
        else:
            for i in node.outputs:
                if str(i) not in self.traverser.state['symbolMap']:
                    traverser.state['symbolicMap'][self.createSymbolIfNotFound(i)] = self.createSymbolIfNotFound(i)

    def generatePathConstraint(self, symbol):
        finalPathConstraint = []
        queue = []
        queue.append(symbol)        
        while len(queue) > 0:
            currentSymbol = queue.pop(0)
            if currentSymbol in self.traverser.state['symbolicMap']:
                currentSymbolicExpr = self.traverser.state['symbolicMap'][currentSymbol]
                currentPathConstraint = "%s"%(currentSymbolicExpr)
                finalPathConstraint.append(currentPathConstraint)
                for possibleSymbol in self.traverser.state['symbolicMap'][currentSymbol].split(" "):
                    if possibleSymbol in self.traverser.state['symbolicMap'] and possibleSymbol != currentSymbol:
                        queue.append(possibleSymbol)
        return finalPathConstraint

    def negateConstraint(self, constraint):
        try:
            if len(constraint) > 0:
                set_option(rational_to_decimal=True)
                return "(%s)"%simplify(Not(eval(constraint[0], self.listOfVariables, {})))
            else:
                return 'True'
        except Exception as e:
            #print e
            return 'True'
    def testConstraintSatisfiable(self, constraints):
        try:
            simplifiedConstraint = []
            set_option(rational_to_decimal=True)
            S = Solver()
            S.set("timeout", 5000)
            for i in constraints:
                evaluatedConstraint = eval(str(i), self.listOfVariables, {})
                if not isinstance(evaluatedConstraint, bool):
                    simplifiedConstraint.append(str(simplify(evaluatedConstraint)))
                    S.append(eval(simplifiedConstraint[-1],self.listOfVariables, {}))
                else:
                    S.append(evaluatedConstraint)
            return simplifiedConstraint, S.check() == sat, False
        except Exception as e:
            #print e
            return [], True, True

    def createSymbolForBinaryOpBitVec(self, node, traverser):
        operator = None
        op = node.op
        if op == "Expr_BinaryOp_BitwiseAnd":
            operator = "&"
        elif op == "Expr_BinaryOp_BitwiseXor":
            operator = "^"
        elif op == "Expr_BinaryOp_BitwiseOr":
            operator = "|"
        elif op == "Expr_BinaryOp_Concat":
            operator = "+"
        elif op == "Expr_BinaryOp_ShiftLeft":
            operator = "<<"
        elif op == "Expr_BinaryOp_ShiftRight":
            operator = ">>"
        if operator:
            left = traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.inputs[0])]
            if left in self.listOfVariables:
                left = "BitVecRef(Z3_mk_int2bv(%s.ctx_ref(), 32, %s.as_ast()), %s.ctx)"%(left,left,left)
            right = traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.inputs[1])]
            if right in self.listOfVariables:
                right = "BitVecRef(Z3_mk_int2bv(%s.ctx_ref(), 32, %s.as_ast()), %s.ctx)"%(right,right,right)
            traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.results[0])] = "NOT IMPLEMENTED"

    def createSymbolForBinaryOpInt(self, node, traverser):
        operator = None
        op = node.op
        if op == "Expr_BinaryOp_Equal" or op == "Expr_BinaryOp_Identical":
            operator = "=="
        elif op == "Expr_BinaryOp_Greater":
            operator = ">"
        elif op == "Expr_BinaryOp_Smaller":
            operator = "<"
        elif op == "Expr_BinaryOp_SmallerOrEqual":
            operator = "<="
        elif op == "Expr_BinaryOp_NotEqual" or op == "Expr_BinaryOp_NotIdentical":
            operator = "!="
        elif op == "Expr_BinaryOp_GreaterOrEqual":
            operator = ">="
        elif op == "Expr_BinaryOp_Div":
            operator = "/"
        elif op == "Expr_BinaryOp_Mod":
            operator = "%"
        elif op == "Expr_BinaryOp_Mul":
            operator = "*"
        elif op == "Expr_BinaryOp_Minus":
            operator = "-"
        elif op == "Expr_BinaryOp_Pow":
            operator = "**"
        elif op == "Expr_BinaryOp_Plus":
            operator = "+"
        comparators = ["==",">","<","<=","!=",">="]
        if operator:
            leftOperand = traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.inputs[0])]
            leftOperand = self.simplifyValueWithoutOperator(leftOperand)
            rightOperand = traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.inputs[1])] 
            rightOperand = self.simplifyValueWithoutOperator(rightOperand)
            traverser.state['symbolicMap'][self.createSymbolIfNotFound(node.results[0])] = "((%s) %s (%s))"%(leftOperand, operator, rightOperand)

    def simplifyValueWithoutOperator(self, value):
        try:
            evaluatedValue = eval(str(value), self.listOfVariables, {})
            try:
                return simplify(evaluatedValue)
            except Exception as f:
                return evaluatedValue
        except Exception as e:
            return value

    def createSymbolForBinaryOp(self, node, traverser):
        # Only one of these would do something.
        self.createSymbolForBinaryOpInt(node,traverser)
        self.createSymbolForBinaryOpBitVec(node,traverser)

    def createSymbolIfNotFound(self, var, type=Real):
        if str(var) not in self.traverser.state['symbolMap']:
            generatedVariable = self.nextSymbol()
            self.traverser.state['symbolMap'][str(var)] = generatedVariable
            if isinstance(var,Var) and var.isLiteral():
                self.traverser.state['symbolicMap'][generatedVariable] = str(getSymbolicLiteralValue(str(var)))
            if generatedVariable not in self.listOfVariables:
                self.listOfVariables[generatedVariable] = type(generatedVariable)
            if generatedVariable not in self.traverser.state['symbolicMap']:
                self.traverser.state['symbolicMap'][generatedVariable] = 'False'
        return self.traverser.state['symbolMap'][str(var)]

    def nextSymbol(self):
        try:
            return "%s"%(''.join(self.symbolGenerator.next()))
        except StopIteration:
            self.symbolGeneratorLength += 1
            self.symbolGenerator = itertools.product(string.lowercase, repeat=self.symbolGeneratorLength)
            return self.nextSymbol()
