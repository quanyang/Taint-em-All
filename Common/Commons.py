import os, re,string,binascii

import importlib
from ast import ClassDef, parse, ImportFrom
import inspect


def getAnalyzerClassName(module):
    # Get the module
    p = parse(inspect.getsource(module))
    className = ""
    for node in p.body:
      if isinstance(node, ClassDef):
          className = node.name
    return className

def flattenList(targetList):
    if isinstance(targetList,list):
        tmp = []
        for subList in targetList:
            tmp.extend(flattenList(subList))
        return tmp
    return [targetList]

def convertStringToInt(string):
    return int(binascii.hexlify(string.encode('utf8')),16)

def getSymbolicLiteralValue(literal):
    result = getLiteralValue(literal)
    return result
    try:
        m = re.search("^\'(.*?)\'$", result)
        if m:
            return convertStringToInt(m.group(1))
    except:
        return result

def getLiteralValue(literal):
    try:
        m = re.search('^LITERAL\(\'?(.*?)\'?\)$', literal)
        value = m.group(1)
        if value.lower() == "true" or value.lower() == "false":
            #for boolean
            return eval(value,{'true':True,'false':False})
        elif any(not char.isdigit() for char in value) or len(value)==0:
            #for strings/numbers
            return "'%s'"%value
        else:
            return value
    except:
        print literal

def resolvePathAgainst(targetPath, againstPath):
    return os.path.abspath(os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(againstPath)),os.path.dirname(targetPath))),os.path.basename(targetPath)))