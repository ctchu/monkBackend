# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 21:11:34 2015

@author: Randy
"""

import psycopg2
psycopg2.extras.register_uuid()
from psycopg2.extensions import AsIs

import uuid
import constants as cons
import logging
import base
import sys
import uuid
from datetime import datetime

#import constants as cons

logger = logging.getLogger("monk.crane")

# pool of the connection to PostgreSQL database
class PostgrePool(object):
    def __init__(self):
        self.__clients = {}
    
    def getDataBase(self, connectionString, databaseName, user):
        key = (connectionString, databaseName)
        if key in self.__clients:
            return self.__clients[key]
        else:
            try:
                client = psycopg2.connect("dbname={0} user={1}".format(databaseName, user))
                self.__clients[key] = client
                return client
            except Exception as e:
                logger.warning(e.message)
                logger.warning('failed to connect {}@{}'.format(databaseName, connectionString))
        return None
    
    def closeDataBase(self):
        for client in self.__clients.values():
            if client:
                client.close()

class Crane(object):
    postgrePool = PostgrePool()

    def __init__(self, connectionString=None, database=None, user=None, tableName=None):
        if connectionString is None or database is None or user is None:
            return
        
        logger.info('initializing {0} '.format(database))
        
        if tableName:
            self._defaultTableName = tableName
            self._currentTableName = tableName
        else:
            self._defaultTableName = cons.DEFAULT_TABLENAME
            self._currentTableName = cons.DEFAULT_TABLENAME
            
        self._database = self.postgrePool.getDataBase(connectionString, database, user)
        self._cursor = self._database.cursor(cursor_factory=psycopg2.extras.DictCursor)    
        self._cache = {}

    # cache related operation
    def __get_one(self, key):
        if key in self._cache:
            return self._cache[key]
        else:
            return None

    def __get_all(self, keys):
        objs = [self._cache[key] for key in keys if key in self._cache]
        rems = [key for key in keys if key not in self._cache]
        return objs, rems

    def __put_one(self, obj):
        self._cache[obj._id] = obj

    def __put_all(self, objs):
        map(self.__put_one, objs)

    def __erase_one(self, obj):
        try:
            del self._cache[obj._id]
        except:
            pass

    def __erase_all(self, objs):
        map(self.__erase_one, objs)
        
    def update_one_in_fields(self, obj, fields):
        try:
            targetTableName = obj.table_name
            targetIdInTable = obj._id
            
            # [TODO]: check if it exists   
            executeString = "SELECT * FROM {0} WHERE _id = {1}".format(targetTableName, psycopg2.extensions.adapt(targetIdInTable).getquoted())
            #self._cursor.execute("select exists(select * from %s where _id=%s)", (targetTableName, targetIdInTable,))
            
            #executeString = "SELECT _id FROM {0} WHERE _id = {1}".format(targetTableName, targetIdInTable)
            self._cursor.execute(executeString)
                
            row = self._cursor.fetchone()
            if row is None:            
                self.add_one(targetTableName, targetIdInTable)
        
        except psycopg2.DatabaseError, e:        
            self._database.rollback()
            print 'Error %s' % e                
        
        except Exception as e:
            logger.warning(e.message)
            logger.warning('can not update _id {0} in table {1} in fields {2}'.format(obj.TABLE_NAME, obj._id, fields))
            
        try:     
            # update
            executePushStrings = []
            
            for keyInTarget in fields.keys():
                if keyInTarget == '_id':
                    raise Exception('_id cannot be updated')
                
                requestValue = fields[keyInTarget]
    
                # [TODO] how to check what the data type is? e.g., datatime, string, dict/json etc.
                if requestValue is not "" and requestValue is not None: 
                    useStringFormat = False
                    useJsonFormat = False
                     
                    if isinstance(requestValue, basestring) or isinstance(requestValue, datetime):
                        useStringFormat = True
                    
                    if isinstance(requestValue, dict):
                        useJsonFormat = True
                        
                    if useStringFormat and not useJsonFormat: 
                        executePushString = "UPDATE {0} SET {1} = '{2}' WHERE _id = {3}".format(targetTableName, keyInTarget, requestValue, psycopg2.extensions.adapt(targetIdInTable).getquoted())
                        #print 'requestValue is string'
                    elif not useStringFormat and not useJsonFormat: 
                        executePushString = "UPDATE {0} SET {1} = {2} WHERE _id = {3}".format(targetTableName, keyInTarget, requestValue, psycopg2.extensions.adapt(targetIdInTable).getquoted())
                        #print 'requestValue is not string'
                    elif not useStringFormat and useJsonFormat: 
                        executePushString = "UPDATE {0} SET {1} = {2} WHERE _id = {3}".format(targetTableName, keyInTarget, psycopg2.extras.Json(requestValue), psycopg2.extensions.adapt(targetIdInTable).getquoted())
                        
                    executePushStrings.append(executePushString)
                    
            for executePushString in executePushStrings:
                self._cursor.execute(executePushString)
                
            self._database.commit()
            
        
        except psycopg2.DatabaseError, e:            
            self._database.rollback()
            print 'Error %s' % e            
            return False
        
        except Exception as e:
            logger.warning(e.message)
            logger.warning('can not update _id {0} in table {1} in fields {2}'.format(obj.TABLE_NAME, obj._id, fields))
            return False
            
        return True
    
    def add_one(self, targetTableName, targetIdInTable):
         try:
            executeString = "insert into {0} (_id) VALUES({1})".format(targetTableName, psycopg2.extensions.adapt(targetIdInTable).getquoted())
            self._cursor.execute(executeString)
            self._database.commit()
            
         except psycopg2.DatabaseError, e:
            self._database.rollback()
            print 'Error %s' % e
            logger.warning(e.message)
            logger.warning('can not add one')
            return False
    
    def add_column(self, column, typeString):        
        executeString = "alter table {0} add column %s {1}".format(self._currentTableName, typeString)
        ## e.g., "alter table Tasks add column %s char(40)"
        ## columns = ['add1', 'add2']
        
        try:
            self._cursor.execute(executeString, (AsIs(column),))        
            self._database.commit()
            return True
            
        except psycopg2.DatabaseError, e:
            self._database.rollback()
            print 'Error %s' % e    
            logger.warning(e.message)
            logger.warning('can not add column')
            return False
            
    def delete_column(self, column):        
        executeString = "alter table {0} drop column %s".format(self._currentTableName)
        ## e.g., "alter table Tasks drop column %s"
        ## columns = ['add1', 'add2']
        
        try:
            self._cursor.execute(executeString, (AsIs(column),))        
            self._database.commit()
            return True
            
        except psycopg2.DatabaseError, e:
            self._database.rollback()
            print 'Error %s' % e    
            logger.warning(e.message)
            logger.warning('can not delete column')
            return False
            
    def load_or_create(self, obj, tableName=None, tosave=False):
        if obj is None:
            return None
        
        if isinstance(obj, uuid.UUID) and tableName is not None:
            return self.load_one_by_id(obj, tableName)
        else:
            objId = self.load_one_in_id({'name':obj.get('name', cons.DEFAULT_EMPTY),
                                         'creator':obj.get('creator', cons.DEFAULT_CREATOR),
                                         'table_name':obj.get('table_name', cons.DEFAULT_TABLENAME)})
            if objId:
                return self.load_one_by_id(objId, obj.get('table_name', cons.DEFAULT_TABLENAME))
            elif 'monk_type' in obj:
                obj = self.create_one(obj)
                if tosave:
                    obj.save()
                return obj
            else:
                return None   
     
    def load_one_by_id(self, objId, tableName):
        obj = self.__get_one(objId)
        if not obj and objId:
            try:
                executeString = "SELECT * FROM {0} WHERE _id = {1}".format(tableName, psycopg2.extensions.adapt(objId).getquoted())
                self._cursor.execute(executeString)
                
                row = self._cursor.fetchone()
                if row is not None:            
                    obj = base.monkFactory.decode(row)

                if obj:
                    self.__put_one(obj)
                    
            except psycopg2.DatabaseError, e:
                self._database.rollback()
                obj = None
                
            except Exception as e:
                logger.warning(e.message)
                logger.warning('can not load document by _id {0}'.format(objId))
                obj = None
        return obj
    
    def load_one_in_id(self, query):
        try:
            executeString = "SELECT * FROM {0} WHERE name = '{1}' ".format(query['table_name'], query['name'])
            self._cursor.execute(executeString)
                
            row = self._cursor.fetchone()
            if row is not None:            
                return row['_id']
            return None
            
        except psycopg2.DatabaseError, e:
            self._database.rollback()
            print 'Error %s' % e   
            return None
        except Exception as e: 
            logger.warning(e.message)
            logger.warning('can not load document by query'.format(query))
            return None
            
    def delete_by_id(self, objId, tableName):
            if not objId:
                return False
            
            if not isinstance(objId, uuid):
                return False
            
            try:
                executeSearchString = "SELECT FROM {0} WHERE _id = {1}".format(tableName, objId)
                executeDeleteString = "DELETE FROM {0} WHERE _id = {1} ".format(tableName, objId)
            
                self._cursor.execute(executeSearchString)
                
                row = self._cursor.fetchone()
                if row is None:
                    raise Exception('_id {0} cannot be found so it cannot be deleted', objId)
                
                self._cursor.execute(executeDeleteString)
                
                self._database.commit()
                self.__erase_one(objId)
                return True
                
            except psycopg2.DatabaseError, e:
                self._database.rollback()
                print 'Error %s' % e    
                sys.exit(1)
        
            except Exception as e:
                logger.warning(e.message)
                logger.warning('can not delete document by query')
                            
            return False
            
    def create_one(self, obj):
        obj = base.monkFactory.decode(obj)
        if obj:
            self.__put_one(obj)
        return obj
        
    def update_turtleId(self, tableName, contractId, turtleId):
        try:
            executePushString = "UPDATE {0} SET turtle_id = {1} WHERE _id = {2}".format(tableName, psycopg2.extensions.adapt(turtleId).getquoted(), psycopg2.extensions.adapt(contractId).getquoted())    
        
            self._cursor.execute(executePushString)
            
            self._database.commit()
            
        except psycopg2.DatabaseError, e:
            self._database.rollback()
            print 'Error %s' % e    
            sys.exit(1)
    
        except Exception as e:
            logger.warning(e.message)
            logger.warning('can not delete document by query')
        
contractStore = None
turtleStore = None

def exit_storage():
    Crane.postgrePool.closeDataBase()
    
def initialize_storage(config):
    global contractStore, turtleStore
    
    contractStore  = Crane(config['connectionString'],
                           config['dbname'],
                           config['user'],
                           config['contractStoreTableName'])
                         
    turtleStore  = Crane(config['connectionString'],
                         config['dbname'],
                         config['user'],
                         config['turtleStoreTableName'])

    from turtle import Turtle
    Turtle.store = turtleStore
    
    from contract import Contract
    Contract.store = contractStore
    
    return True
