from Policy.PHPTaintPolicy import *
from Engine.PHPEngine import *
from Model.Node import *
from Traverser import Traverser
import copy,random

name = "DFS Traversal"

class DFSTraverser(Traverser):

    def __init__(self):
        self.visitors = []
        self.visited = dict()
        self.customFunction = dict()
        self.CFGForest = None
        self.tempStorage = dict()
        self.state = dict()

        self.visitedBlock = {}
        self.isLooping = False

        Traverser.__init__(self)

    def addVisitor(self,visitor):
        self.visitors.append(visitor)

    def visitEvent(self,event,data):
        for visitor in self.visitors:
            getattr(visitor, event)(self, data)

    def traverseForest(self,CFGForest):
        self.CFGForest = CFGForest
        self.visitEvent("enterForest",[self.CFGForest])
        self.traverseFunc("main")
        self.visitEvent("leaveForest",[self.CFGForest])
        return self.CFGForest

    def traverseFunc(self,funcName):
        func = self.CFGForest.getCFG(funcName)
        if func:
            self.visitEvent("enterFunc",[func,funcName])
            self.traverseBlock(func, 0, funcName, 0)
            self.visitEvent("leaveFunc",[func,funcName])

    def traverseBlock(self,CFG,blockId,forestKey,prevBlock):
        # If blockId not found
        if len(CFG.blocks) <= blockId:
            return
        block = CFG.blocks[blockId]
        edge = (blockId, forestKey)
        if edge not in self.visitedBlock:
            self.visitedBlock[edge] = 0
        else:
            self.isLooping = True
        self.visitedBlock[edge] += 1

        self.visitEvent("enterBlock",[block,blockId,CFG,forestKey,prevBlock])
        for node in block.nodes:
            if isinstance(node,OperandNode) and node.operation == "exit":
                break
            self.traverseNode(node, CFG, block, blockId, forestKey, prevBlock)
        self.visitEvent("leaveBlock",[block,blockId,CFG,forestKey,prevBlock])

    def traverseNode(self, node, CFG, block, blockId, forestKey, prevBlock = None):
        self.visitEvent("enterNode",[node,block,blockId,CFG,forestKey,prevBlock])
        randomInt = random.random()
        tempState = copy.deepcopy(self.state)
        self.tempStorage[randomInt] = copy.deepcopy(CFG)
        edge = (blockId, forestKey)
        tempVisitBlock = copy.deepcopy(self.visitedBlock)
        if isinstance(node,OperandNode) and node.operation == "return":
            self.visitedBlock = {}
            self.isLooping = False
        if isinstance(node,FuncNode):
            # Mark for custom defined functions
            self.customFunction[node.name] = True
        elif isinstance(node,OperandNode):
            self.traverseOperation(node, block, CFG)
        elif isinstance(node,JumpNode):
            edge = (blockId,int(node.target)-1,forestKey)
            if not edge in self.visited:
                self.visited[edge] = True
                self.traverseBlock(CFG,int(node.target)-1,forestKey, block.blockId)
        elif isinstance(node,SwitchNode):
            for case,target in sorted(node.cases.items()):
                edge = (blockId,int(target)-1,forestKey)
                if not edge in self.visited:
                    targetBlock = CFG.blocks[int(target) - 1]
                    if targetBlock and targetBlock.pathReachable:
                        self.state = copy.deepcopy(tempState)
                        self.visited[edge] = True
                        self.traverseBlock(CFG,int(target)-1,forestKey, block.blockId)
        elif isinstance(node,JumpIfNode):
            edge = (blockId,int(node.ifTarget)-1,forestKey)
            if not edge in self.visited:
                targetBlock = CFG.blocks[int(node.ifTarget) - 1]
                if targetBlock and targetBlock.pathReachable:
                    self.visited[edge] = True
                    self.traverseBlock(CFG,int(node.ifTarget)-1,forestKey, block.blockId)

            self.state = copy.deepcopy(tempState)
            self.visitedBlock = tempVisitBlock
            
            CFG.blocks[int(node.ifTarget) - 1].pathConstraint = copy.deepcopy(self.tempStorage[randomInt].blocks[int(node.ifTarget) - 1].pathConstraint)
            CFG.blocks[int(node.ifTarget) - 1].pathReachable = copy.deepcopy(self.tempStorage[randomInt].blocks[int(node.ifTarget) - 1].pathReachable)
            CFG.blocks[int(node.elseTarget) - 1].pathConstraint = copy.deepcopy(self.tempStorage[randomInt].blocks[int(node.elseTarget) - 1].pathConstraint)
            CFG.blocks[int(node.elseTarget) - 1].pathReachable = copy.deepcopy(self.tempStorage[randomInt].blocks[int(node.elseTarget) - 1].pathReachable)

            edge = (blockId,int(node.elseTarget)-1,forestKey)
            if not edge in self.visited:
                targetBlock = CFG.blocks[int(node.elseTarget) - 1]
                if targetBlock and targetBlock.pathReachable:
                    self.visited[edge] = True
                    self.traverseBlock(CFG,int(node.elseTarget)-1,forestKey, block.blockId)
        self.visitEvent("leaveNode",[node,block,blockId,CFG,forestKey,prevBlock])

    def traverseOperation(self, node, block, CFG):
        self.visitEvent("enterOp",[node,block, CFG])
        name = None
        if isinstance(node,FuncCallNode):
            name = node.getName()
            scope = node.getScope()
            if scope != None:
                name = "%s::%s"%(scope,name)
        if isinstance(node,FuncCallNode) and (name in self.customFunction or self.CFGForest.getCFG(name) != None):
            self.traverseFunc(name)
        elif node.operation == "include":
            if len(node.inputs) > 0 and node.inputs[0].value != None and False:
                targetPath = os.path.basename(getLiteralValue(node.inputs[0].value))
                targetCfg = "%s_%s"%("main",targetPath)
                targetBlock = self.CFGForest.getCFG(targetCfg)
                if targetBlock:
                    self.traverseBlock(targetBlock, 0, targetCfg, block.blockId)
        self.visitEvent("leaveOp",[node,block, CFG])
