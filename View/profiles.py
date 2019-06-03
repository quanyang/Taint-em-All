import json
import os

from Traverser.DFSTraverser import DFSTraverser
import Module.LivenessVisitor
import Module.StaticTaintAnalysisVisitor
import Module.SymbolicExecutionVisitor
from Module.LivenessVisitor import LivenessVisitor
from Module.StaticTaintAnalysisVisitor import StaticTaintAnalysisVisitor
from Module.SymbolicExecutionVisitor import SymbolicExecutionVisitor

from Common.Commons import *

startingPath = os.getcwd()
profileLocation = "profiles.json"



class Profile:
    # List of traversals in FIFO order
    traversals = []
    # List of analysis module for each traversal in FIFO order
    # Each traversal = 1 array.
    modules = []

    def __init__(self):
        pass

    def addTraversal(self, traverser):
        self.traversals.append(traverser)
        self.modules.append(list())

    def addModule(self, index, module):
        assert(index < len(self.traversals))
        self.modules[index].append((module.__name__,module.name))

    def getResult(self):
        result = []
        index = 0
        for i in self.traversals:
            result.append({"traversal":i.__name__, "modules": self.modules[index]})
            index += 1
        return result

def getProfiles():
    try:
        with file("%s/%s"%(startingPath, profileLocation), "rb") as profile:
            profiles = json.load(profile)
            for name,profile in profiles.iteritems():
                temp = []
                for traversal in profile:
                    tempTraversal = {'modules':[], 'traversal': traversal['traversal']}
                    for module in traversal['modules']:
                        try:
                            __import__(module[0])
                            tempTraversal['modules'].append(module)
                        except:
                            pass
                    temp.append(tempTraversal)
                profiles[name] = temp
            return profiles
    except:
        return None

def saveProfile(profiles):
    with file("%s/%s"%(startingPath, profileLocation), "wb") as profile:
        json.dump(profiles, profile)
        return True
    return False

def updateProfile(name, profile):
    profiles = getProfiles()
    if name in profiles:
        profiles[name] = profile
        saveProfile(profiles)

def addProfile(name, profile):
    profiles = getProfiles()
    if name not in profiles:
        profiles[name] = profile
        saveProfile(profiles)
        return True
    return False

def deleteProfile(name):
    profiles = getProfiles()
    if name in profiles:
        del profiles[name]
        saveProfile(profiles)
        return True
    return False

def initializeWithDefault():
    default = Profile()
    default.addTraversal(DFSTraverser)
    default.addModule(0, Module.LivenessVisitor)
    default.addModule(0, Module.StaticTaintAnalysisVisitor)
    default.addModule(0, Module.SymbolicExecutionVisitor)
    with file("%s/%s"%(startingPath, profileLocation), "wb") as profile:
        json.dump({"default": default.getResult()}, profile)

# Check if an existing profile can be found.        
if getProfiles() == None:
    initializeWithDefault()