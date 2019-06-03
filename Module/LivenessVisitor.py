from Visitor.Visitor import Visitor
from Model.Node import *
name = "Liveness Analysis Visitor"
prereq = None
class LivenessVisitor(Visitor):
    def __init__(self):
        self.analyzedLines = {}
        Visitor.__init__(self,0)
        
    def leaveBlock(self, traverser, (block,blockId,CFG,forestKey,prevBlock)):
        variables = set()
        for node in block.nodes:
            if node.startLine != "None":
                self.analyzedLines[node.startLine] = True
            for attribute in node.__dict__:
                if isinstance(node.__dict__[attribute],list):
                    for entry in node.__dict__[attribute]:
                        if isinstance(entry,Var):
                            variables.add(entry)
                elif isinstance(node.__dict__[attribute],Var):
                    variables.add(node.__dict__[attribute])
            if isinstance(node,JumpNode):
                targetBlock = CFG.blocks[int(node.target)-1]
                variables = variables.union(targetBlock.liveVars)
            elif isinstance(node,SwitchNode):
                for case,target in sorted(node.cases.items()):
                    targetBlock = CFG.blocks[int(target)-1]    
                    variables = variables.union(targetBlock.liveVars)
            elif isinstance(node,JumpIfNode):
                targetBlock = CFG.blocks[int(node.ifTarget)-1]
                variables = variables.union(targetBlock.liveVars)
                targetBlock = CFG.blocks[int(node.elseTarget)-1]
                variables = variables.union(targetBlock.liveVars)
        block.liveVars = variables
        block.analysisState['livenessAnalysis'] = True
        Visitor.leaveBlock(self, traverser, (block, blockId, CFG, forestKey,prevBlock))
