# -*- coding: utf-8 -*-
"""
Created on Fri Aug 11 12:55:22 2023

Monitoring process that records observations of the system variables.

@author: tiihonen
"""

import numpy

class monitor(object):
    
    def __init__(self,checkfreq, itercount):
        self.check=checkfreq
        self.iter=itercount
        self.blockfrq=0
        self.operfrq=0
        self.checkfrq=0
        self.bf_dump=[]
        self.op_dump=[]
        
        
    def reset(self):
        self.blockfrq=0
        self.checkfrq=0
        self.operfrq=0
        
    def report(self,it):
        self.bf_dump.append(self.blockfrq)
        self.op_dump.append(self.operfrq)
       
        
    def run(self,machine,env):
        while True :
            yield env.timeout(self.check)
            self.checkfrq=self.checkfrq+1
            if(machine.isblocking):
                self.blockfrq+=1
            if(machine.isoperational):
                self.operfrq+=1
            
    def dump(self):
        print(self.bf_dump)
        print(self.op_dump)
        print('means %s, %s'% (numpy.mean(self.bf_dump), numpy.mean(self.op_dump)))
        print('stddev %s, %s'% (numpy.std(self.bf_dump), numpy.std(self.op_dump)))