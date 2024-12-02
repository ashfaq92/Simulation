# -*- coding: utf-8 -*-
"""
Created on Thu Aug  10

@author: tiihonen
"""

import random

import simpy

import arrivals
import clinic
import monitor as M
import stream


# System configuration specifics
PRECAPACITY=4
OPCAPACITY=1
POSTCAPACITY=4

T_INTER = 25
PRETIME = 40 
OPTIME = 20
POSTTIME =40      # Create a car every ~6 minutes

# Simulation experiment specifics
WARM_TIME = 1000   # Warm up time in minutes
SIM_TIME =10000    # Simulation time
REPEATS = 10      # number of repeats
CHECK =10         # measuring interval
RANDOM_SEED = 42  # This helps reproducing the results


runtime=REPEATS*(WARM_TIME+SIM_TIME) # needed mainly for a hack to stop the arrival process after the simulation

random.seed(RANDOM_SEED)  

# Create an environment and start the setup process
env = simpy.Environment()
reporter=M.monitor(CHECK,REPEATS)
ward=clinic.clinic(env,PRECAPACITY,OPCAPACITY,POSTCAPACITY)
interarrival=stream.stream('exp',T_INTER)
preparationtime=stream.stream('unif',PRETIME,10)
operationtime=stream.stream('exp',OPTIME)
recoverytime=stream.stream('unif', POSTTIME,10)
env.process(arrivals.setup(env, ward, interarrival,preparationtime,operationtime,recoverytime,runtime)) # start the simulation
env.process(reporter.run(ward, env))

# Execute!
for i in range(REPEATS):
    env.run(until=env.now+WARM_TIME)
    reporter.reset()
    env.run(until=env.now+SIM_TIME)
    reporter.report(i)

reporter.dump()
 
