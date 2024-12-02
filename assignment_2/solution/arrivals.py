# -*- coding: utf-8 -*-
"""
Created on Wed Jun 21 09:12:29 2023

@author: tiihonen
"""


import patient

def setup(env, ward, t_inter, pretime, optime, posttime, endtime):
    """ keep creating patients and their timeneeds
    approx. every ``t_inter`` minutes until endtime."""

    # Create more patients while the simulation is running

    while (env.now < endtime):
        interarrivaltime=t_inter.new() # try to create all random variates at the same time
        pre=pretime.new()
        op=optime.new()
        post=posttime.new()
        new=patient.patient(env, ward, pre,op,post)
        env.process(new.run()) # Setup and start the simulation of a new patient process
        yield env.timeout(interarrivaltime)
        


       
            