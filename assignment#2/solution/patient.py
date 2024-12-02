# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 08:41:08 2023

@author: tiihonen
"""

class patient(object):
    
    def __init__(self,env, ward, pre, op, post):
        self.env=env
        self.ward=ward
        self.pre=pre
        self.op=op
        self.post=post

    def run (self):
        """ The main life cycle that explains the patient flow through the 
        system. Pay attention to the interplay of requesting and releasing
        different resources that ensures that the payload is always under
        supervision.
        
        Status bits are used to facilitate exernal monitoring of the process.

        """
        Prep=self.ward.Preparation
        Op=self.ward.Operation
        Post=self.ward.Recovery
        pre_req=Prep.request()
        op_req=Op.request()
        post_req=Post.request()

        arrivaltime = self.env.now
        yield pre_req
        yield self.env.timeout(self.pre)
        yield op_req
        self.ward.isoperational=True
        opwaittime=self.env.now
        self.ward.prewait+=self.env.now-arrivaltime
        Prep.release(pre_req)

        yield self.env.timeout(self.op)
        self.ward.isoperational=False
        self.ward.isblocking=True
        yield post_req
        self.ward.isblocking=False
        postwaittime=self.env.now
        self.ward.opwait+=self.env.now-opwaittime
        Op.release(op_req)

        yield self.env.timeout(self.post)
        Post.release(post_req)
        self.ward.postwait+=self.env.now-postwaittime
    
    