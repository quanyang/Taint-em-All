from Engine.PHPEngine import PHPEngine
from Traverser.DFSTraverser import DFSTraverser
from Module.StaticTaintAnalysisVisitor import StaticTaintAnalysisVisitor
from Module.SinkVisitor import SinkVisitor
import os
import sys


def scanFile(staticTaintAnalysisVisitor, inputFile):
    engine = PHPEngine(sandbox=False)
    CFGForest = engine.generateCFG(inputFile)
    sinkVisitor = SinkVisitor()

    traverser = DFSTraverser()
    traverser.addVisitor(sinkVisitor)
    CFGForest = traverser.traverseForest(CFGForest)

    traverser2 = DFSTraverser()
    traverser2.addVisitor(staticTaintAnalysisVisitor)
    CFGForest = traverser2.traverseForest(CFGForest)


def main():
    inputFile = os.path.realpath(sys.argv[1])
    staticTaintAnalysisVisitor = StaticTaintAnalysisVisitor()
    scanFile(staticTaintAnalysisVisitor, inputFile)
    output = "Results:\n"
    output += ("Tainted Sink: %s\n" %
               len(staticTaintAnalysisVisitor.taintedSink))
    output += ("-"*80+"\n")
    for i in staticTaintAnalysisVisitor.taintedSink:
        output += (i.__str__(True))
    output += ("="*80+"\n")
    output += ("\n")
    print output


if __name__ == "__main__":
    main()
