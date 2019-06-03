#!/bin/python
# -*- coding: utf-8 -*-
import subprocess,json
from Model.CFGForest import CFGForest
from Model.CFG import CFG
from Model.Block import Block
from Model.Node import *
from Common.Commons import *
import os
"""
Purpose:
Engine would be used to generate AST/CFG/DFG accordingly for the language.
"""

class PHPEngine:
    def __init__(self, sandbox=True):
        #print "PHP Engine initialized"
        self.sandbox=sandbox
        self.initialized=True

    def generateAST(self,pathToSourceFile):
        print "Not Implemented"

    def generateCFG(self, pathToSourceFile, included=None):
        #print "Generating CFG for \'%s\'"%pathToSourceFile
        # Uses PHP-CFG to generate CFG
        path = pathToSourceFile
        if included:
            path = included
        enginePath = resolvePathAgainst("generateCFG.php",os.path.abspath(__file__))
        helper = subprocess.Popen("php %s '%s'"%(enginePath, path),shell=True,stdout=subprocess.PIPE)
        output = helper.communicate()[0]
        if len(output) > 0:
            try:
                jsonOutput = json.loads(output)
                forest = CFGForest()
                for i in jsonOutput:
                    key = i.replace("\\","\\\\").replace("()","")
                    cfg = self.parseToCFG(jsonOutput[i])
                    forest.addCFG(cfg, key)
                fileInclusions = self.getAllInclusion(jsonOutput, pathToSourceFile)
                for includedFile in fileInclusions:
                    includedForest =  self.generateCFG(pathToSourceFile, includedFile).forest
                    for key,cfg in includedForest.iteritems():
                        if key == "main":
                            key = "%s_%s"%(key, os.path.basename(includedFile))
                        forest.addCFG(cfg, "%s"%key)
                return forest
            except Exception as e:
                print e
                raise Exception("PHP Snippet is invalid.")
        else:
            raise Exception("File %s does not exist." % path)

    # Gets all filepath of literal file inclusion in script.
    def getAllInclusion(self, inputJson, origFile):
        return []
        if self.sandbox:
            return []
        listOfInclusion = []
        for i in inputJson:
            for block_ in inputJson[i]:
                for node_ in block_['blocks']:
                    if node_['op'] == "Expr_Include" and "value" in node_['expr']:
                        targetPath = getLiteralValue(node_['expr']['value'])
                        if targetPath:
                            resolvedPath = resolvePathAgainst(targetPath,origFile)
                            listOfInclusion.append(resolvedPath)
        return listOfInclusion

    def parseToCFG(self,inputJson):
        cfg = CFG()
        for block_ in inputJson:
            block = Block(block_['blockId'])
            for parent in block_['parentBlock']:
                block.addParent(parent)
            # parse every node individually
            for node_ in block_['blocks']:
                if self.sandbox:
                    node_['file'] = "**SandBoxed**"
                node = self.parseOp(node_)
                if node != None:
                    block.addNode(node)
                    if isinstance(node,ParamNode):
                        cfg.addArgument(node.output)
                else:
                    print "New unseen node: %s"%node_
            cfg.addBlock(block)

        return cfg
    def parseTerminalOp(self,node_):
        op = node_['op']
        node = None
        if op == "Terminal_Echo":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['expr'])
        elif op == "Terminal_Const":
            #something seems wrong.
            node = StaticNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addOutput(node_['name'])
            node.addArgument(node_['value'])
            node.setBlock(node_['valueBlock'])
        elif op == "Terminal_GlobalVar":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['var'])
        elif op == "Terminal_StaticVar":
            node = StaticNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.setBlock(node_['defaultBlock'])
            node.addArgument(node_['defaultVar'])
            node.addOutput(node_['var'])
        elif op == "Terminal_Unset":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            if "exprs" in node_:
                node.addArgument(node_['exprs'])
        elif op == "Terminal_Throw":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['expr'])
        elif op == "Terminal_Return":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            if "expr" in node_:
                node.addArgument(node_['expr'])
        return node

    def parseStmtOp(self,node_):
        op = node_['op']
        node = None
        if op == "Stmt_Jump":
            node = JumpNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setJump(node_['target'])
        elif op == "Stmt_JumpIf":
            node = JumpIfNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setIf(node_['if'])
            node.setElse(node_['else'])
            node.setCond(node_['cond'])
        elif "Stmt_Function" == op[:13]:
            node = FuncNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setFunc(op)
            if "opName" in node_:
                node.setName(node_['opName'])
            if "stmts" in node_:
                node.setBlock(node_['stmts'])
            if "params" in node_:
                node.addParam(node_['params'])
        elif op == "Stmt_Class":
            node = ClassNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setClassName(node_['name']['value'])
            if "extends" in node_:
                node.addInheritance(node_['extends']['value'])
            if "implements" in node_:
                node.addInterface(node_['implements'])
            #May have more than one.
            node.setBlock(node_['stmts'])
        elif op == "Stmt_Property":
            node = StaticNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            if "defaultBlock" in node_:
                node.setBlock(node_['defaultBlock'])
            if "defaultVar" in node_:
                node.addArgument(node_['defaultVar'])
        elif op == "Stmt_Interface":
            node = InterfaceNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setInterfaceName(node_['name']['value'])
            node.setBlock(node_['stmts'])
            if "extends" in node_:
                node.addInheritance(node_['extends'])
        elif "Stmt_ClassMethod" == op[:16]:
            node = FuncNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setFunc(op)
            if "opName" in node_:
                node.setName(node_['opName'])
            if "stmts" in node_:
                node.setBlock(node_['stmts'])
            if "params" in node_:
                node.addParam(node_['params'])
        elif op == "Stmt_Trait":
            node = TraitNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setTraitName(node_['name'])
            node.setBlock(node_['stmts'])
        elif op == "Stmt_Switch":
            node = SwitchNode(node_['file'],node_['startLine'],node_['endLine'])
            cases = flattenList(node_['cases'])
            for i,x in enumerate([x for x in node_['targets']]):
                node.addCase(x,cases[int(i)])
            if "default" in node_:
                node.addCase(node_['default'],{"value":"default"})
            node.setCond(node_['cond'])
        return node

    def parseExprCastOp(self,node_):
        op = node_['op']
        node = CastNode(node_['file'],node_['startLine'],node_['endLine'])
        node.setOperand(op)
        node.addArgument(node_['expr'])
        node.addOutput(node_['result'])
        return node

    def parseExprBinaryOp(self,node_):
        op = node_['op']
        # left = input[0],right= input[1]
        node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
        node.setOperand(op)
        node.addArgument(node_['left'])
        node.addArgument(node_['right'])
        node.addResult(node_['result'])
        return node

    def parseExprOp(self,node_):
        op = node_['op']
        node = None
        if "Expr_Cast_" == op[:10]:
            # When Cast to Int, XSS is gone.
            node = self.parseExprCastOp(node_)
        elif "Expr_BinaryOp_" == op[:14]:
            node = self.parseExprBinaryOp(node_)
        elif op == "Expr_ArrayDimFetch":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            if "dim" in node_ and "value" in node_['dim']:
                node_['var']['dim'] = node_['dim']['value']
                node.addArgument(node_['var'])
            else:
                node.addArgument(node_['var'])
            node.addOutput(node_['result'])
        elif op == "Expr_Assign":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['expr'])
            node.addResult(node_['result'])
            node.addOutput(node_['var'])
        elif op == "Expr_Include":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['expr'])
            node.addResult(node_['result'])
        elif op == "Expr_Isset":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            if "vars" in node_:
                node.addArgument(node_['vars'])
            node.addResult(node_['result'])
        elif op == "Expr_MethodCall":
            node = FuncCallNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.setScope(str(Var.turnSourceIntoVar(node_['var']).name))
            node.setName(node_['name'])
            if "args" in node_:
                node.addArgument(node_['args'])
            node.addOutput(node_['result'])
        elif "Expr_StaticCall" == op[:15]:
            node = FuncCallNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.setScope(node_['class']['value'])
            if "name" in node_:
                node.setName(node_['name'])
            if "args" in node_:
                node.addArgument(node_['args'])
            node.addOutput(node_['result'])
        elif op == "Expr_FuncCall":
            node = FuncCallNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            if "name" in node_:
                node.setName(node_['name'])
            else:
                node.setOperand(op)
            node.addOutput(node_['result'])
            if "args" in node_:
                node.addArgument(node_['args'])
        elif op == "Expr_ConstFetch":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['name'])
            node.addOutput(node_['result'])
        elif op == "Expr_New":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['class'])
            node.addOutput(node_['result'])
        elif op == "Expr_Array":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            if "values" in node_:
                node.addArgument(node_['values'])
            node.addOutput(node_['result'])
        elif op == "Expr_AssignRef":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['expr'])
            node.addOutput(node_['var'])
            node.addResult(node_['result'])
        elif op == "Expr_BooleanNot":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['expr'])
            node.addOutput(node_['result'])
        elif op == "Expr_BitwiseNot":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['expr'])
            node.addOutput(node_['result'])
        elif op == "Expr_PropertyFetch":
            #work on this
            node = PropertyNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setVar(node_['var'])
            node.setName(node_['name'])
            node.setOutput(node_['result'])
        elif op == "Expr_Clone":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['expr'])
            node.addOutput(node_['result'])
        elif op == "Expr_Empty":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['expr'])
            node.addResult(node_['result'])
        elif op == "Expr_ConcatList":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['list'])
            node.addOutput(node_['result'])
        elif op == "Expr_ClassConstFetch":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            var = dict()
            var["value"] = "%s::%s"%(Var.turnSourceIntoVar(node_['class']),Var.turnSourceIntoVar(node_['name']))
            node.addArgument(var)
            node.addOutput(node_['result'])
        elif op == "Expr_Exit":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addResult(node_['result'])
        elif op == "Expr_Eval":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['expr'])
            node.addOutput(node_['result'])
        elif op == "Expr_InstanceOf":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['expr'])
            node.addArgument(node_['class'])
            node.addResult(node_['result'])
        elif op == "Expr_Print":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['expr'])
            node.addResult(node_['result'])
        elif op == "Expr_Yield":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['key'])
            node.addOutput(node_['result'])
        elif op == "Expr_UnaryPlus" or op == "Expr_UnaryMinus":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['expr'])
            node.addOutput(node_['result'])
        elif "Expr_Closure" == op[:13]:
            node = ClosureNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setFunc(op)
            if "params" in node_:
                node.addParam(node_['params'])
            if "useVars" in node_:
                node.addUseVar(node_['useVars'])
            if "stmts" in node_:
                node.setBlock(node_['stmts'])
            node.addOutput(node_['result'])
        elif op == "Expr_StaticPropertyFetch":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['class'])
            node.addArgument(node_['name'])
            node.addOutput(node_['result'])
        elif "Expr_Assertion" == op[:14]:
            node = AssertionNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            if "assertion" in node_:
                node.setAssertion(node_['assertion'])
            node.addArgument(node_['expr'])
            node.addOutput(node_['result'])
        elif "Expr_Param" == op[:10]:
            node = ParamNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setName(node_['name'])
            node.setOutput(node_['result'])
        return node

    def parseIteratorOp(self,node_):
        op = node_['op']
        node = None
        if op == "Iterator_Reset":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['var'])
        elif op == "Iterator_Valid":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['var'])
            node.addResult(node_['result'])
        elif op == "Iterator_Key":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['var'])
            node.addOutput(node_['result'])
        elif op == "Iterator_Value":
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            node.addArgument(node_['var'])
            node.addOutput(node_['result'])
        return node

    def parsePhiOp(self,node_):
        op = node_['op']
        node = None
        if "Phi" in op:
            node = OperandNode(node_['file'],node_['startLine'],node_['endLine'])
            node.setOperand(op)
            if "vars" in node_:
                node.addArgument(node_['vars'])
            if "result" in node_:
                node.addOutput(node_['result'])
        return node

    def parseOp(self,node_):
        op = node_['op']
        #Expr,Stmt,Terminal,Iterator,Op,Phi
        if "Expr" in op[:4]:
            return self.parseExprOp(node_)
        elif "Stmt" in op[:4]:
            return self.parseStmtOp(node_)
        elif "Terminal" in op[:8]:
            return self.parseTerminalOp(node_)
        elif "Iterator" in op[:8]:
            return self.parseIteratorOp(node_)
        elif "Phi" in op:
            return self.parsePhiOp(node_)
        return None