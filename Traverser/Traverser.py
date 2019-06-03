class Traverser(object):
    def __init__(self):
        pass

    def addVisitor(self,visitor):
        pass

    def visitEvent(self,event,data):
        pass

    def traverseForest(self,CFGForest):
        pass

    def traverseFunc(self,funcName):
        pass

    def traverseBlock(self,CFG,blockId,forestKey,prevBlock):
        pass

    def traverseNode(self, node, CFG, block, blockId, forestKey, prevBlock = None):
        pass

    def traverseOperation(self, node, block):
        pass