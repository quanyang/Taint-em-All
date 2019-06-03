from Policy.PHPTaintPolicy import *
from Engine.PHPEngine import *
from Model.Node import *
from Traverser import Traverser
import copy

name = "BFS Traversal"

class BFSTraverser(Traverser):

    def __init__(self):
        self.visitQueue = []
        self.visitors = []
        self.visited = dict()
        self.customFunction = dict()
        self.CFGForest = None
        Traverser.__init__(self)

    def addVisitor(self,visitor):
        self.visitors.append(visitor)

    def visitEvent(self,event,data):
        for visitor in self.visitors:
            getattr(visitor, event)(self, data)

    def visitLoop(self):
        # Loop under queue is empty
        while len(self.visitQueue) > 0:
            currNode = self.visitQueue.pop(0)
            node = currNode[0]
            if isinstance(node, CFGForest):
                self.traverseForestReal(node)
            elif isinstance(node, CFG):
                self.traverseFunc(node)
            elif isinstance(node, Block):
                self.traverseBlock(*currNode)
            elif isinstance(node, Node):
                self.traverseNode(*currNode)

    def traverseForestReal(self, CFGForest):
        self.CFGForest = CFGForest
        self.visitEvent("enterForest",[self.CFGForest])
        # Assumes starting from main
        if self.CFGForest.getCFG("main"):
            self.visitQueue.append((self.CFGForest.getCFG("main"),None))
        self.visitEvent("leaveForest",[self.CFGForest])
        return self.CFGForest

    def traverseForest(self,CFGForest):
        self.visitQueue.append((CFGForest,None))
        self.visitLoop()
        return self.CFGForest

    def traverseFunc(self,func):
        if func:
            self.visitEvent("enterFunc",[func,func.name])
            if len(func.blocks) > 0:
                block = func.blocks[0]
                self.visitQueue.append((block,func,0,func.name,0))
            self.visitEvent("leaveFunc",[func,func.name])

    def traverseBlock(self,block,CFG,blockId,forestKey,prevBlock):
        # If blockId not found
        self.visitEvent("enterBlock",[block,blockId,CFG,forestKey,prevBlock])
        for node in block.nodes:
            if isinstance(node,OperandNode) and node.operation == "exit":
                break
            self.visitQueue.append((node, CFG, block, blockId, forestKey, prevBlock))
        self.visitEvent("leaveBlock",[block,blockId,CFG,forestKey,prevBlock])

    def traverseNode(self, node, CFG, block, blockId, forestKey, prevBlock = None):
        self.visitEvent("enterNode",[node,block,blockId,CFG,forestKey,prevBlock])
        if isinstance(node,FuncNode):
            # Mark for custom defined functions
            self.customFunction[node.name] = True
        elif isinstance(node,OperandNode):
            self.traverseOperation(node, block, CFG)
        elif isinstance(node,JumpNode):
            edge = (blockId,int(node.target)-1,forestKey)
            targetBlock = CFG.blocks[int(node.target) - 1]
            if not edge in self.visited:
                self.visited[edge] = True
                self.visitQueue.append((targetBlock,CFG,int(node.target)-1,forestKey, block.blockId))
        elif isinstance(node,SwitchNode):
            for case,target in sorted(node.cases.items()):
                edge = (blockId,int(target)-1,forestKey)
                if not edge in self.visited:
                    targetBlock = CFG.blocks[int(target) - 1]
                    if targetBlock and targetBlock.pathReachable:
                        self.visited[edge] = True
                        self.visitQueue.append((targetBlock,CFG,int(target)-1,forestKey, block.blockId))
        elif isinstance(node,JumpIfNode):
            edge = (blockId,int(node.ifTarget)-1,forestKey)
            if not edge in self.visited:
                targetBlock = CFG.blocks[int(node.ifTarget) - 1]
                if targetBlock and targetBlock.pathReachable:
                    self.visited[edge] = True
                    self.visitQueue.append((targetBlock,CFG,int(node.ifTarget)-1,forestKey, block.blockId))
            edge = (blockId,int(node.elseTarget)-1,forestKey)
            if not edge in self.visited:
                targetBlock = CFG.blocks[int(node.elseTarget) - 1]
                if targetBlock and targetBlock.pathReachable:
                    self.visited[edge] = True
                    self.visitQueue.append((targetBlock, CFG,int(node.elseTarget)-1,forestKey, block.blockId))
        self.visitEvent("leaveNode",[node,block,blockId,CFG,forestKey,prevBlock])

    def traverseOperation(self, node, block, CFG):
        self.visitEvent("enterOp",[node,block, CFG])
        if isinstance(node,FuncCallNode) and node.getName() in self.customFunction:
            if self.CFGForest.getCFG(node.getName()):
                self.visitQueue.append((self.CFGForest.getCFG(node.getName()),None))
        elif node.operation == "include":
            if len(node.inputs) > 0 and node.inputs[0].value != None:
                targetPath = os.path.basename(getLiteralValue(node.inputs[0].value))
                targetCfg = "%s_%s"%("main",targetPath)
                targetBlock = self.CFGForest.getCFG(targetCfg)
                if targetBlock:
                    self.visitQueue.append((targetBlock.blocks[0], targetBlock, 0, targetCfg, block.blockId))
        self.visitEvent("leaveOp",[node,block, CFG])
