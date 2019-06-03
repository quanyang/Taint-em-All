"""
CFGFOREST has many CFGs
CFG has many blocks
blocks has many nodes
nodes may jump into blocks (if else)
"""
class CFGForest(object):
    def __init__(self):
        self.forest = dict()

    def getCFG(self,key):
        if key in self.forest:
            return self.forest[key]
        return None

    def addCFG(self,cfg,key):
        cfg.setName(key)
        self.forest[key] = cfg

    def printForest(self):
        output = ""
        for key,cfg in self.forest.iteritems():
            output += "="*80+"\r\n\r\n"
            output += "CFG: %s\r\n"%key
            output += str(cfg)
        return output

    def generateGraphViz(self,debug=False):
        CFG_formatting = ""
        for key,cfg in self.forest.iteritems():
            CFG_formatting += cfg.generateGraphViz(debug)
        output = "digraph \"CFG_forest\" {\r\n%s\r\n}"%CFG_formatting
        return output

    def __eq__(self, other):
        for key,cfg in sorted(self.forest.iteritems()):
            if key not in other.forest:
                return False
            elif not cfg.__eq__(other.forest[key]):
                return False
        return True