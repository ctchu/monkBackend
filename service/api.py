# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 21:12:42 2015

@author: Randy
"""

#from flask import render_template
from flask import request
#from flask import redirect
from flask import jsonify
#from flask import make_response
from flask import abort
#from flask import url_for

from flask.ext.cors import cross_origin

import yaml
import os
import sys
import uuid
import logging
import json
import ast
logger = logging.getLogger("monk.api")
logging.basicConfig(filename='.\\log\\logfile.log', filemode='w', level=logging.INFO)

from service import monkService
from service import con

import psycopg2
import psycopg2.extras
#from psycopg2.extensions import AsIs

import crane

ContractTable = "contract"
TurtleTable = "turtle"

t = os.path.join(os.path.dirname(__file__), '..\\monk_config.yml')
        
with open(t, 'r') as yf:
    config = yaml.load(yf)
    #con = psycopg2.connect("dbname={0} user={1}".format(config['dbname'], config['user']))    
    crane.initialize_storage(config)
            
#===========================================
#===========================================
def getTableEntryById(category, targetId):
    
    executeString = "SELECT * FROM {0} WHERE id = {1}".format(category, targetId)
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)    
        cur.execute(executeString)
        
        row = cur.fetchone()
        if row is not None:            
            return dict(row)
        else:
            return None
        #for index in row.keys():
            #entry[index] = copy.deepcopy(row[index])
             
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e    
        sys.exit(1)

#===========================================
#===========================================
def performMerge(consensus, delta):
    if len(consensus) != len(delta):
        return False
        
    for i in range(len(consensus)):
        consensus[i] += delta[i]
    
    return True

#===========================================
#===========================================
def updateTurtleConsensus(turtleId, consensus):
    
    category = TurtleTable
    turtle = getTableEntryById(category, turtleId)
    
    if not turtle:
        abort(404)
    
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)   
        
        executePushString = "UPDATE {0} SET {1} = {2} WHERE id = {3}".format(category, 'consensus', consensus, turtleId)
        
        cur.execute(executePushString)
        con.commit()
            
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e    
        sys.exit(1)
    
    return True

#===========================================
#===========================================
def load_turtle(contractId):
    contract = crane.contractStore.load_or_create(contractId, ContractTable)
    return crane.turtleStore.load_or_create(contract.turtle_id, TurtleTable)

#===========================================
#===========================================
def create_turtle(turtleScript):  
    _turtle = crane.turtleStore.load_or_create(turtleScript, TurtleTable, True)
    if _turtle is None:
        logger.error('failed to load or create the turtle {0}'.format(turtleScript))
        return None
    return _turtle

#===========================================
#===========================================
def create_contract(contractScript):  
    _contract = crane.contractStore.load_or_create(contractScript, ContractTable, True)
    if _contract is None:
        logger.error('failed to load or create the contract {0}'.format(contractScript))
        return None
    return _contract
    
#===========================================
#===========================================
def addTableColumn(category, column, typeString):
    if category == 'turtle':
        return crane.turtleStore.add_column(column, typeString)
    elif category == 'contract':
        return crane.contractStore.add_column(column, typeString)
    
#===========================================
#===========================================
def deleteTableColumn(category, column):
    if category == 'turtle':
        return crane.turtleStore.delete_column(column)
    elif category == 'contract':
        return crane.contractStore.delete_column(column)

#===========================================
#===========================================
def updateTurtleIdInContractTable(contractId, turtleId):
    crane.contractStore.update_turtleId(ContractTable, contractId, turtleId)
        
#=========================================== server API ===========================================
#===========================================
# Check out consensus model
#===========================================
@monkService.route('/api/v1.0/checkout', methods=['GET'])
@cross_origin(allow_headers=['Content-Type'])
def CheckOut():
    
    if not request.json or not 'contract_id' in request.json:
        abort(400)
    
    contractId = uuid.UUID(request.json['contract_id'])
    print contractId
    turtle = load_turtle(contractId)
    
    if turtle:
        return jsonify({'model': turtle.weights})
    else:
        abort(400)    
# curl -i -H "Content-Type: application/json" -X GET -d "{""contract_id"":""03081145-d15d-40d5-9b08-879da802e944""}" http://localhost:5000/api/v1.0/checkout
        
#===========================================
# Merge and update consensus model
#===========================================
@monkService.route('/api/v1.0/merge', methods=['PUT'])
@cross_origin(allow_headers=['Content-Type'])
def Merge():
    
    if not request.json or not 'contract_id' in request.json or not 'delta' in request.json:
        abort(400)
    
    contractId = uuid.UUID(request.json['contract_id'])
    print contractId    
    turtle = load_turtle(contractId)
    print request.json['delta']
    
    # if using array type as delta
    #delta  = json.loads(request.json['delta'])
    
    # if using json type as delta
    delta = ast.literal_eval(request.json['delta'])     # transform unicode to dict
    
    print delta
    
    if turtle:
        succeed = turtle.merge(delta)
    else:
        succeed = False        
    
    return jsonify({'result': succeed})

# if using json type as delta
# curl -i -H "Content-Type: application/json" -X PUT -d "{""contract_id"":""03081145-d15d-40d5-9b08-879da802e944"", ""delta"":""{"'0'": "0.1", "'1'": "0.8", "'2'": "0.35"}""}" http://localhost:5000/api/v1.0/merge
#
# if using array type as delta
# curl -i -H "Content-Type: application/json" -X PUT -d "{""contract_id"":""03081145-d15d-40d5-9b08-879da802e944"", ""delta"":""[1,2,3]""}" http://localhost:5000/api/v1.0/merge









