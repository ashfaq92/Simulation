# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 12:20:35 2023
Wrapper for different needed random streams that facilitates the 
design of experiments (systematic varying of parameters in an outer loop) 
without touching the actual simulation model/loop.

@author: tiihonen
"""

import random

class stream :
    
    def __init__(self, type, *args):
        self.type=type
        if(self.type=='exp') :
            self.p1= args[0]
        if (type=='unif') :
            self.p1=args[0]-args[1]
            self.p2=args[0]+args[1]
            
    def new(self):
        if (self.type=='exp') :
            return random.expovariate(1/self.p1)
        if(self.type=='unif') :
            return random.uniform(self.p1,self.p2)

        