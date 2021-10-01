# Taint'em All

This is a taint analysis tool for the PHP language and it makes use of Static Taint Analysis + Symbolic Execution to achieve high recall and high precision. This analysis tool was written using the framework designed and implemented as part of the project.

Used in this blog post [https://quanyang.github.io/part-1-continuous-pwning/](https://quanyang.github.io/part-1-continuous-pwning/). 

## Dependencies:
```
phpserialize
z3
flask
flask-codemirror
WTForms
flask-wtf
graphviz
php-cfg
```

php-cfg and its dependencies are already included in the src folder.

## Installation:

***Mac OS X***
```
pip install -r requirements.txt
brew install graphviz z3 php
```

***Linux***
```
pip install -r requirements.txt
apt-get install graphviz php-cli
```

## GUI Usage:
To use
```
python main.py
```
View site on http://localhost:80/

## CLI Usage:
To use
```
python cli.py <path to PHP file>
```

Example output:
```
Results:
Tainted Sink: 3
--------------------------------------------------------------------------------
    File: /SimpleXSS.php
    Starting Line: 6
    Ending Line: 6
    Type: <class 'Model.Node.OperandNode'>
    State: *Dangerous: Tainted Input(s). Possible Cross-Site Scripting*
    Terminal_Echo
    Inputs: Var#9
    Outputs:
    Results:

    File: /SimpleXSS.php
    Starting Line: 7
    Ending Line: 7
    Type: <class 'Model.Node.OperandNode'>
    State: *Dangerous: Tainted Input(s). Possible Cross-Site Scripting*
    Expr_Print
    Inputs: Var#10
    Outputs:
    Results: Var#11

    File: /SimpleXSS.php
    Starting Line: 8
    Ending Line: 8
    Type: <class 'Model.Node.OperandNode'>
    State: *Dangerous: Tainted Input(s). Possible Code Execution*
    Expr_Eval
    Inputs: Var#6<$user_specified_input>
    Outputs: Var#12
    Results:

================================================================================
```
