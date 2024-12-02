# -*- coding: utf-8 -*-
"""
Created on Fri Jun  2 14:30:47 2023
Defines the structural elements of the model and needed components for 
status monitoring.

@author: tiihonen
"""


import simpy

class clinic(object):

    def __init__(self,env, num_pre, num_op, num_post):
        self.env = env
        self.Preparation=simpy.Resource(env,num_pre)
        self.Operation=simpy.Resource(env,num_op)
        self.Recovery=simpy.Resource(env,num_post)
        self.prewait=0
        self.opwait=0
        self.postwait=0
        self.isblocking=False
        self.isoperational=False
        
    def reset(self) :
        self.prewait=0
        self.opwait=0
        self.postwait=0
        

    def report(self) :
        print(self.prewait,self.opwait, self.postwait)












