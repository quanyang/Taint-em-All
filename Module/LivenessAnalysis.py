from Policy.PHPTaintPolicy import *
from Engine.PHPEngine import *
from Model.Node import *
import copy

#name = "Liveness Analysis"
prereq = None

class LivenessAnalysis:
    def __init__(self):
        self.CFGForest = None
        self.visited = dict()
        self.customFunction = dict()
    def livenessAnalysisOnCFGForest(self,CFGForest,blockId):
        self.CFGForest = copy.deepcopy(CFGForest)
        self.recurseBlockLivenessAnalysis(self.CFGForest.getCFG("main"), 0, "main")
        return self.CFGForest
    def recurseBlockLivenessAnalysis(self,CFG,blockId,forestKey):
        if len(CFG.blocks) <= blockId:
            return
        block = CFG.blocks[blockId]
        variables = set()
        tempVisited = copy.deepcopy(self.visited)
        for node in block.nodes:
            for attribute in node.__dict__:
                if isinstance(node.__dict__[attribute],list):
                    for entry in node.__dict__[attribute]:
                        if isinstance(entry,Var):
                            variables.add(entry)
                            block.vars.add(entry)
                elif isinstance(node.__dict__[attribute],Var):
                    variables.add(node.__dict__[attribute])
                    block.vars.add(node.__dict__[attribute])
            if isinstance(node,FuncNode):
                # Mark for custom defined functions
                self.customFunction[node.name] = True
            if isinstance(node,FuncCallNode) and node.getName() in self.customFunction:
                # Custom defined function taint propagation. Propagates return value state back as well.
                targetBlock = self.CFGForest.getCFG(node.getName())
                if targetBlock:
                    targetBlock.blocks[0].liveVars = self.recurseBlockLivenessAnalysis(targetBlock,0,node.getName())
                    self.visited = copy.deepcopy(tempVisited)
            elif isinstance(node,OperandNode) and node.operation == "include":
                # Inclusion affects control flow.
                if len(node.inputs) > 0 and node.inputs[0].value != None:
                    targetPath = os.path.basename(getLiteralValue(node.inputs[0].value))
                    targetCfg = "%s_%s"%("main",targetPath)
                    targetBlock = self.CFGForest.getCFG(targetCfg)
                    edge = (blockId,targetCfg,forestKey)
                    if not edge in self.visited:
                        if targetBlock:
                            self.visited[edge] = True
                            self.recurseBlockLivenessAnalysis(targetBlock, 0, targetCfg)
                            self.visited = copy.deepcopy(tempVisited)
            elif isinstance(node,JumpNode):
                edge = (blockId,int(node.target)-1,forestKey)
                if not edge in self.visited:
                    self.visited[edge] = True
                    variables = variables.union(self.recurseBlockLivenessAnalysis(CFG,int(node.target)-1,forestKey))
                    self.visited = copy.deepcopy(tempVisited)
            elif isinstance(node,SwitchNode):
                for case,target in sorted(node.cases.items()):
                    edge = (blockId,int(target)-1,forestKey)
                    if not edge in self.visited:
                        self.visited[edge] = True
                        variables = variables.union(self.recurseBlockLivenessAnalysis(CFG,int(target)-1,forestKey))
                        self.visited = copy.deepcopy(tempVisited)
            elif isinstance(node,JumpIfNode):
                edge = (blockId,int(node.ifTarget)-1,forestKey)
                if not edge in self.visited:
                    self.visited[edge] = True
                    variables = variables.union(self.recurseBlockLivenessAnalysis(CFG,int(node.ifTarget)-1,forestKey))
                    self.visited = copy.deepcopy(tempVisited)
                edge = (blockId,int(node.elseTarget)-1,forestKey)
                if not edge in self.visited:
                    self.visited[edge] = True
                    variables = variables.union(self.recurseBlockLivenessAnalysis(CFG,int(node.elseTarget)-1,forestKey))
                    self.visited = copy.deepcopy(tempVisited)
        block.liveVars = block.liveVars.union(variables)
        return variables
