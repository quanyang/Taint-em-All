from Model.Node import *
class Visitor:
    logLevel = 0
    analyzedLines = {}
    def __init__(self, logLevel = 0):
        self.logLevel = logLevel
        if self.logLevel == 1:
            print "Starting Visitor"
    def enterForest(self, traverser, forest):
        if self.logLevel == 1:
            print "Entering Forest"
    def leaveForest(self, traverser, forest):
        if self.logLevel == 1:
            print "Leaving Forest"
    def enterFunc(self, traverser, (func,funcName)):
        if self.logLevel == 1:
            print "Entering Function %s"%funcName
    def leaveFunc(self, traverser, (func,funcName)):
        if self.logLevel == 1:
            print "Leaving Function %s"%funcName
    def enterBlock(self, traverser, (block,blockId,cfg,forestKey,prevBlock)):
        if self.logLevel == 1:
            print "Entering Block %s of %s"%(blockId, forestKey)
    def leaveBlock(self, traverser, (block,blockId,cfg,forestKey,prevBlock)):
        if self.logLevel == 1:
            print "Leaving Block %s of %s"%(blockId, forestKey)
    def enterNode(self, traverser, (node,block,blockId,cfg,forestKey,prevBlock)):
        if self.logLevel == 1:
            if isinstance(node,OperandNode):
                print "Entering Node %s of block %s"%(node.op, blockId)
            else:
                print "Entering Node %s of block %s"%(type(node), blockId)            
    def leaveNode(self, traverser, (node,block,blockId,cfg,forestKey,prevBlock)):
        if self.logLevel == 1:
            if isinstance(node,OperandNode):
                print "Leaving Node %s of block %s"%(node.op, blockId)
            else:
                print "Leaving Node %s of block %s"%(type(node), blockId)      
    def enterOp(self, traverser, (op, block, CFG)):
        if self.logLevel == 1:
            print "Entering Operation %s in block %s"%(op.op,block.blockId -1)
    def leaveOp(self, traverser, (op, block, CFG)):
        if self.logLevel == 1:
            print "Leaving Operation %s in block %s"%(op.op,block.blockId -1)