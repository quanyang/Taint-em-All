import os
from os import listdir
from os.path import isfile, join
from importlib import *
import random
from time import time
import py_compile

mypath = os.getcwd()
modulesPath = mypath +"/Module/"
traversalsPath = mypath + "/Traverser/"
def readFile(filePath):
    with file(filePath, 'rb') as output:
        return output.read()

def deleteModule(filename):
    filename = filename.split("/")[-1]
    os.remove(modulesPath + filename + "c")
    return os.remove(modulesPath + filename)

def editModule(filename, content):
    filename = filename.split("/")[-1]
    with file(modulesPath + filename, 'wb') as outputFile:
        outputFile.write(content)
        outputFile.close()
        py_compile.compile(modulesPath + filename)
        return True
    return False

def addModule(content):
    filename = "module_%s.py" % str(time()).replace(".","_")
    with file(modulesPath + filename, 'wb') as outputFile:
        outputFile.write(content)
        outputFile.close()
        py_compile.compile(modulesPath + filename)
        return True
    return False

def getModuleInfo(filename):
    filename = filename.split("/")[-1]
    modulePath = modulesPath + filename
    fileContent = readFile(modulePath)
    return {'content': fileContent, 'filename': filename}

def getTraversals():
    files = [f for f in listdir(traversalsPath) if isfile(join(traversalsPath, f))]
    traversals = []
    for filename in files:
        if filename[-3:] == ".py" and filename != "__init__.py":
            traversals.append(filename)

    traversalNames = []
    for filename in traversals:
        traversalName = filename[:-3]
        traversal = __import__("Traverser.%s"%traversalName)
        print traversal.__dict__[traversalName]
        if "name" in traversal.__dict__[traversalName].__dict__:
            traversalNames.append({'modulename': traversalName,'name':traversal.__dict__[traversalName].__dict__['name'], 'filename': filename})
    return traversalNames

def getModules():
    files = [f for f in listdir(modulesPath) if isfile(join(modulesPath, f))]
    modules = []
    for filename in files:
        if filename[-3:] == ".py" and filename != "__init__.py":
            modules.append(filename)

    moduleNames = []
    for filename in modules:
        moduleName = filename[:-3]
        module = __import__("Module.%s"%moduleName)
        if "name" in module.__dict__[moduleName].__dict__:
            moduleNames.append({'modulename': moduleName,'name':module.__dict__[moduleName].__dict__['name'], 'filename': filename, 'prerequisite': module.__dict__[moduleName].__dict__['prereq']})
    return moduleNames