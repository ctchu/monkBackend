# -*- coding: utf-8 -*-
"""
Created on Thu May 07 23:04:36 2015

@author: Randy
"""

#from flask import Flask
#app = Flask(__name__)
#
#@app.route('/')
#def hello_world():
#    return 'Randy!!! Hello World!'

from service import monkService

if __name__ == '__main__':
    monkService.run(debug = True)       # set debug to True, so whenever the source code changes, Flask will restart the service automatically