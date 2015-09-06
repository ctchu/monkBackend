# -*- coding: utf-8 -*-
"""
Created on Sat Aug 22 14:14:48 2015

@author: Randy
"""

import sys
import os.path

# needs to add this here in order to import service.crane
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# When I install flask cor, it is installed under myenv environment, so needs to append it here
sys.path.append('C:\\Users\\Randy\\Anaconda\\envs\\myenv\\Lib\\site-packages')

print sys.path

#
#import service.api
import yaml
import uuid
import service.crane as crane
import service.api as api

def yaml2json(yamlFileName):
    with open(yamlFileName, 'r') as yf:
        return yaml.load(yf)
    return None


def addTableColumns(targetTable, targetConfig):        
    
   # the order of the keys is not the same as in the file.
   # make sure _id is always the first column
    for column in targetConfig.keys():  
        typeString = targetConfig[column]
        if column == '_id':
            if not api.addTableColumn(targetTable, column, typeString):
                print "Failed to add column {0}".format(column)
            break    
    
    for column in targetConfig.keys():  
        typeString = targetConfig[column]
        if column != '_id':
            if not api.addTableColumn(targetTable, column, typeString):
                print "Failed to add column {0}".format(column)            

def deleteTableColumns(targetTable, targetConfig):
       
    for column in targetConfig.keys():  
        if not api.deleteTableColumn(targetTable, column):
            print "Failed to delete column {0}".format(column)
            

if __name__=='__main__':
    config = yaml2json('..\\monk_config.yml')
    crane.initialize_storage(config)
    
#    targetTable = 'turtle'
#    targetConfig = yaml2json('..\\turtleTable_config.yml')
#    addTableColumns(targetTable, targetConfig)
    
#    turtleConfig = yaml2json('..\\turtle_config.yml')
#    turtle = api.create_turtle(turtleConfig)
    
#    contractConfig = yaml2json('..\\contract_config.yml')
#    contract = api.create_contract(contractConfig)
    
    contractId = uuid.UUID("03081145-d15d-40d5-9b08-879da802e944")
    turtle = api.load_turtle(contractId);
    print turtle.weights
    delta = {"0": 0.1, "1": 0.8, "2": 0.35}
    turtle.merge(delta)
    print turtle.weights
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    