from flask import Flask, render_template, redirect, url_for, session, request
from flask_codemirror.fields import CodeMirrorField
from wtforms.fields import SubmitField
from flask_codemirror import CodeMirror
from flask_wtf import Form
from graphviz import Source

from Engine.PHPEngine import PHPEngine
from Module.StaticTaintAnalysisVisitor import StaticTaintAnalysisVisitor
from Module.SymbolicExecutionVisitor import SymbolicExecutionVisitor
from Traverser.DFSTraverser import *
from Traverser.BFSTraverser import *
from Module.LivenessVisitor import LivenessVisitor
from Visitor.Visitor import Visitor

import tempfile, os, json, importlib, inspect, time, modules, profiles
from ast import ClassDef, parse, ImportFrom
from Common.Commons import *

import sys, traceback

class MyForm(Form):
  source_code = CodeMirrorField(language = 'application/x-httpd-php',
                                config = {
                                  'lineNumbers' : 'true',
                                  'matchBrackets' : 'true',
                                  'indentWithTabs' : 'true',
                                  'indentUnit' : 4
                                },
                                )
  submit = SubmitField('Analyze')

class ModuleForm(Form):
  source_code = CodeMirrorField(language = 'python',
                                config = {
                                  'lineNumbers' : 'true',
                                  'matchBrackets' : 'true',
                                  'indentWithTabs' : 'true',
                                  'indentUnit' : 4
                                },
                                )

defaultCode = """<?php
  $input = $_GET['cmd'];
  echo $input;
?>"""

defaultModuleCode = """
from Visitor.Visitor import Visitor
from Model.Node import *
name = "Module Name"
prereq = None

class ModuleName(Visitor):    
    def __init__(self):
      pass
"""

def analyze(input, profile):
  (fd, filename) = tempfile.mkstemp()
  engine = PHPEngine()
  try:
      tfile = os.fdopen(fd, "wb")
      tfile.write(input.encode("utf-8"))
      tfile.close()

      profileMap = profiles.getProfiles()
      if profile in profileMap:
        profile = profileMap[profile]
      else:
        return None, [], {}, False

      stats = dict()
      taintedSink = []
      CFGForest = engine.generateCFG(filename)
      for i,traversal in enumerate(profile):
        stats[i] = dict()
        traversalName = traversal['traversal']
        traverser = __import__("Traverser.%s"%traversalName)
        traverser = traverser.__dict__[traversalName].__dict__[traversalName]()
        modules = []
        for module in traversal['modules']:
          temp = importlib.import_module(module[0])
          className = getAnalyzerClassName(temp)
          name = temp.name
          temp = temp.__dict__[className]()
          modules.append({'module': name,'object':temp})
          traverser.addVisitor(temp)
        try:
          CFGForest = traverser.traverseForest(CFGForest)
        finally:
          for x,module in enumerate(modules):
            stats[i][x] = module['object'].analyzedLines.keys()
            if "taintedSink" in module['object'].__dict__:
              taintedSink = module['object'].taintedSink

      return CFGForest, taintedSink, stats, False
  except Exception as e:
    print e
    return None, [], {}, e
  finally:
      os.remove(filename)

class Server:
  app = Flask(__name__)
  app.config.update(CODEMIRROR_LANGUAGES = ['php','htmlmixed','xml','css','javascript','clike','python'],
                    SECRET_KEY = 'change_this',
                    CODEMIRROR_THEME = 'ambiance',
                    )
  codemirror = CodeMirror(app)

  @app.context_processor
  def inject_configuration():
    configuration = {
    "description": """This is a taint analysis tool for the PHP language and it makes use of Static Taint Analysis + Symbolic Execution to achieve high recall and high precision. This analysis tool was written using the framework designed and implemented as part of the project.""",
    "title": "Taint'em All"
    }
    return configuration

  @app.route("/analyze", methods=["POST"])
  def analyzeEndpoint():
    form = MyForm()
    if form.validate_on_submit():
      profile = request.form.get('profile')
      start = time.time()
      CFGForest,taintedSink,stats,err = analyze(form.source_code.data, profile)
      end = time.time()
      timetaken = (end - start)
      if err:
        return json.dumps({ "error": err.message }),400
      sinks = []
      profileJson = profiles.getProfiles()
      if profile in profileJson:
        profile = profileJson[profile]
      for sink in taintedSink:
        sinkDict = dict()
        sinkDict['startLine'] = sink.startLine
        sinkDict['endLine'] = sink.endLine
        sinkDict['state'] = sink.state
        sinks.append(sinkDict)
      graph = ""
      if CFGForest:
        graphviz = Source(CFGForest.generateGraphViz(True))
        graphviz.format = 'svg'
        graph = graphviz.pipe().decode('utf-8')
    return json.dumps({'sinks':sinks,'graph':graph,'stats': stats, 'profile': profile, 'timetaken': timetaken})

  @app.route('/getModuleInfo', methods=["POST"])
  def getModuleInfo():
    filename = request.form.get('filename')
    return json.dumps(modules.getModuleInfo(filename))

  @app.route("/modules", methods=["GET"])
  def showModules():
    moduleList = modules.getModules()
    form = ModuleForm()
    form.source_code.data = form.source_code.data or defaultModuleCode
    return render_template('modules.html', modules=moduleList, form=form)

  @app.route("/addModule", methods=["POST"])
  def addModule():
    form = MyForm()
    if modules.addModule(form.source_code.data):
      return ""
    else:
      return json.dumps({ "error": "something went wrong." }), 400

  @app.route("/deleteModule", methods=["POST"])
  def deleteModule():
    if modules.deleteModule(request.form.get('filename')):
      return ""
    else:
      return json.dumps({ "error": "something went wrong." }), 400

  @app.route("/editModule", methods=["POST"])
  def editModule():
    form = MyForm()
    filename = request.form.get('filename')
    print filename
    if modules.editModule(filename, form.source_code.data):
      return ""
    else:
      return json.dumps({ "error": "something went wrong." }), 400

  @app.route("/addProfile", methods=["POST"])
  def addProfile():
    if profiles.addProfile(request.form.get('profileName'), []):
      return ""
    else:
      return json.dumps({ "error": "something went wrong." }), 400

  @app.route("/updateProfile", methods=["POST"])
  def editProfile():
    profileName = request.form.get('profileName')
    delete = request.form.get('delete')
    module = request.form.get('module')
    traversal = request.form.get('traversal')
    profileJson = profiles.getProfiles()
    if profileName not in profileJson:
      return json.dumps({ "error": "something went wrong." }), 400
    profile = profileJson[profileName]
    if delete == None:
      if module != None:
        temp = importlib.import_module("Module.%s"%module)
        className = getAnalyzerClassName(temp)
        if len(profile) == 0:
          return json.dumps({ "error": "Add a traversal first." }), 400
        profile[-1]['modules'].append(("Module.%s"%module, temp.name))
        if profiles.updateProfile(profileName, profile):
          return ""
      elif traversal != None:
        profile.append({'traversal':traversal,'modules':[]})
        if profiles.updateProfile(profileName, profile):
          return ""
    else:
      if module != None:
        traversal = int(traversal)
        module = int(module)
        if traversal <= len(profile) and traversal > 0 and module > 0 and module <= len(profile[traversal-1]['modules']):
          del profile[traversal-1]['modules'][module-1]
          print profile
          if profiles.updateProfile(profileName, profile):
            return ""
      elif traversal != None:
        traversal = int(traversal)
        if traversal <= len(profile) and traversal > 0:
          del profile[traversal-1]
          if profiles.updateProfile(profileName, profile):
            return ""
    return json.dumps({ "error": "something went wrong." })

  @app.route("/deleteProfile", methods=["POST"])
  def deleteProfile():
    if profiles.deleteProfile(request.form.get('profileName')):
      return ""
    else:
      return json.dumps({ "error": "something went wrong." })

  @app.route("/profile", methods=["GET"])
  def viewProfile():
    profile = request.args.get('name')
    moduleList = modules.getModules()
    traversalList = modules.getTraversals()
    profileJson = profiles.getProfiles()
    if profile in profileJson:
      return render_template('profile.html', traversals=traversalList, modules=moduleList, profile = profileJson[profile], name=profile)
    else:
      return json.dumps({ "error": "something went wrong." }), 400

  @app.route("/profiles", methods=["GET"])
  def showProfiles():
    profileJson = profiles.getProfiles()
    return render_template('profiles.html', profiles = profileJson)

  @app.route("/", methods=["GET"])
  def analysisForm():
    form = MyForm()
    profileJson = profiles.getProfiles()
    form.source_code.data = form.source_code.data or defaultCode
    return render_template('analysis.html', profiles=profileJson, form=form)

  def run(self):
    self.app.run(port=8080, debug=True, threaded=True)
