from Visitor.Visitor import Visitor
from Model.Node import *
from Policy.WP_PHPTaintPolicy import *
name = "Sink Liveness Analysis Visitor"
prereq = None
class SinkVisitor(Visitor):
    def __init__(self):
        self.analyzedLines = {}
        self.policy = TaintPolicy()
        Visitor.__init__(self,0)
        
    def leaveBlock(self, traverser, (block,blockId,CFG,forestKey,prevBlock)):
        variables = set()
        hasSensitiveSink = False
        hasSource = False
        for node in block.nodes:
            if hasSource:
                break
            if node.startLine != "None":
                self.analyzedLines[node.startLine] = True
            if isinstance(node, OperandNode):
                for taintSink in self.policy.sink.FUNC_LIST:
                    op = node.operation
                    if isinstance(node,FuncCallNode):
                        op = node.getName()
                    #get sink policy
                    if op in getattr(self.policy.sink,taintSink):
                        hasSensitiveSink = True
                for var in node.inputs:
                    if var.name != "" :
                        source = var.name
                        for taintSource in self.policy.source.VAR_LIST:
                            if source in getattr(self.policy.source,taintSource):
                                hasSource = True & hasSensitiveSink
                                break
            if isinstance(node,JumpNode):
                targetBlock = CFG.blocks[int(node.target)-1]
                if targetBlock and targetBlock.pathReachable:
                    hasSource = True
                    break
            elif isinstance(node,SwitchNode):
                for case,target in sorted(node.cases.items()):
                    targetBlock = CFG.blocks[int(target)-1]    
                    if targetBlock and targetBlock.pathReachable:
                        hasSource = True
                        break
            elif isinstance(node,JumpIfNode):
                targetBlock = CFG.blocks[int(node.ifTarget)-1]
                if targetBlock and targetBlock.pathReachable:
                    hasSource = True
                    break
                targetBlock = CFG.blocks[int(node.elseTarget)-1]
                if targetBlock and targetBlock.pathReachable:
                    hasSource = True
                    break
        block.pathReachable = hasSource | hasSensitiveSink

