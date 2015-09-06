# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 21:11:34 2015

@author: Randy
"""
import base
import constants as cons
import crane

import logging
import copy

logger = logging.getLogger("monk.turtle")

class Turtle(base.MONKObject):
    FM                    = 'm'
    FRHO                  = 'rho'
    FWEIGHTS              = 'weights'
    FWEIGHTSDIMENSION     = 'weights_dimension'
    
    store = crane.turtleStore
    
    def __default__(self):
        super(Turtle, self).__default__()
        self.m = 0
        self.rho = 1
        self.weights_dimension = 0
        self.weights = {}
        
    def __restore__(self):
        super(Turtle, self).__restore__()
        # TODO

    def generic(self):
        result = super(Turtle, self).generic()

        result[self.FM]   = self.m
        result[self.FRHO] = self.rho
        result[self.FWEIGHTSDIMENSION] = self.weights_dimension
        result[self.FWEIGHTS] = self.weights
        
        return result
    
    def clone(self, userName):
        obj = super(Turtle, self).clone(userName)
        obj.m = self.m
        obj.rho = self.rho
        obj.weights = copy.deepcopy(self.weights)
        obj.weights_dimension = self.weights_dimension
        return obj
        
    def save(self):
        super(Turtle, self).save()
        
    def delete(self, deep=False):
        result = super(Turtle, self).delete()

        return result
    
    def checkout(self):
        # Do we always load form db? or just use the weights in the object?
        obj = self.store.load_one_by_id(self._id, self.table_name)
        self.__dict__.update(obj)
        return obj.weights
        
    def merge(self, delta):
        # Should we always load from database and merge. Necessary? 
#        obj = self.store.load_one_by_id(self._id, self.table_name)
#        if obj:
#            for i in range(len(delta)):        
#                obj.weights[i] += delta[i]
#            self.store.update_one_in_fields(obj, {'weights': obj.weights})
#            self.__dict__.update(obj)
#        else:
#            logger.error('unable to merge in turtle {0}'.format(self._id))
#            return False    
        
        scaleFactor = self.m + 1 / self.rho
        for k in delta.keys():
            if k in self.weights:
                self.weights[k] += delta[k] / scaleFactor
            else:
                self.weights[k] = delta[k]
            
        self.store.update_one_in_fields(self, {'weights': self.weights})
        
        return True

        
base.register(Turtle)
