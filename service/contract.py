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

logger = logging.getLogger("monk.contract")

class Contract(base.MONKObject):
    FTURTLEID           = 'turtle_id'
    FTURTLE             = 'turtle'
    
    store = crane.contractStore
    
    def __default__(self):
        super(Contract, self).__default__()
        self.turtle_id = None
        self.turtle = None
        
    def __restore__(self):
        super(Contract, self).__restore__()
        # TODO

    def generic(self):
        result = super(Contract, self).generic()

        result[self.FTURTLEID]   = self.turtle_id
        del result[self.FTURTLE]
        
        return result
    
    def clone(self, userName):
        obj = super(Contract, self).clone(userName)
        obj.turtle_id = self.turtle_id
        obj.turtle = self.turtle   # two contracts share the same turtle object?
        
        return obj
        
    def save(self):
        super(Contract, self).save()
        
    def delete(self, deep=False):
        result = super(Contract, self).delete()

        return result
    
    def checkout(self):
        # Do we always load form db? or just use the weights in the object?
        obj = self.store.load_one_by_id(self._id, self.table_name)
        self.__dict__.update(obj)
        return obj
        
    def merge(self, delta):
        obj = self.store.load_one_by_id(self._id, self.table_name)
        if obj:
            for i in range(len(delta)):        
                obj.weights[i] += delta[i]
            self.store.update_one_in_fields(obj, {'weights': obj.weights})
            self.__dict__.update(obj)
        else:
            logger.error('unable to merge in turtle {0}'.format(self._id))
            return False    
        
        return True

        
base.register(Contract)
