import re
"""
Var object that contains var attributes
"""
class Var(object):
    def __init__(self):
        self.type = None
        self.byRef = False
        self.value = ""
        self.scope = "" #default global
        self.name = ""
        self.dim = ""
        self.id = -1
    @staticmethod
    def turnSourceIntoVar(source):
        var = Var()
        if "type" in source:
            var.type = source['type']
        if "byRef" in source:
            var.byRef = source['byRef']
        if "value" in source:
            var.value = source['value']
        if "scope" in source:
            var.scope = source['scope']
        if "var_name" in source:
            var.name = source['var_name']
        if "id" in source:
            var.id = source['id']
        if "dim" in source:
            var.dim = source['dim']
        return var
    def isLiteral(self):
        m = re.search('LITERAL\(\'?(.*?)\'?\)', self.value)
        return m != None
    def __str__(self,FuncCall=False):
        self.name = self.name.encode('ascii','ignore')
        self.value = self.value.encode('ascii','ignore')
        if FuncCall:
            if self.byRef:
                prefix = "&"
            else:
                prefix = ""
            if self.name != "":
                return "%s$%s"%(prefix,self.name)
            return self.value
        elif self.id == -1:
            if self.byRef:
                prefix = "&"
            else:
                prefix = ""
            if self.name != "":
                return "%s<%s$%s>"%(self.scope,prefix,self.name)
            return self.value
        else:
            if self.byRef:
                prefix = "&"
            else:
                prefix = ""
            if self.name != "":
                name = "<%s$%s>"%(prefix,self.name)
            else:
                name = "%s%s"%(prefix,self.name)
            if self.dim != "":
                name += "[%s]"%(self.dim)
            return "Var#%s%s%s"%(self.id,self.scope,name)
    def __repr__(self):
        return self.__str__()
    def __hash__(self):
        return hash((self.value,self.id,self.name))
    def __eq__(self,other):
        if not other:
            return False
        if self.dim and self.dim != other.dim:
            return False
        return (self.value,self.id,self.name) == (other.value,other.id,other.name)
    def __ne__(self,other):
        return not(self == other)
    def __lt__(self,other):
        if self.id != -1 and other.id != -1:
            return int(self.id) < int(other.id)
        return self.__str__() < other.__str__()
