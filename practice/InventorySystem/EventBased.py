'''
discrete event simulation using event scheduling approach
object oriented representation to avoid global variables
'''

import numpy as np
import matplotlib.pyplot as plt


class Simulation:
    def __init__(self, orderCutoff, orderTarget):
        '''
        cutoff = minimum inventory left to push new order
        target = max inventory limit that we aspire to fill 
        '''
        self.orderTarget = orderTarget
        self.orderCutoff = orderCutoff

        '''system state'''
        self.inventory = orderTarget
        self.numOrdered = 0

        '''simulation variables'''
        self.clock = 0
        self.tCustomer = self.generateInterarrival()
        self.tDelivery = float('inf')
        self.eventList = []

        '''Statistical Counters'''
        self.revenue = 0.00
        self.costOrders = 0.00
        self.costHolding = 0.00

    
    def advanceTime(self):
        tEvent = min(self.tCustomer, self.tDelivery)
        self.costHolding += self.inventory * 2 * (tEvent - self.clock)
        self.clock = tEvent

        if self.tDelivery <= self.tCustomer:
            self.handleDeliveryEvent()
        else:
            self.handleCustomerEvent()

    
    def handleCustomerEvent(self):
        demand = self.generateDemand()
        if self.inventory > demand:
            self.revenue += demand * 100
            self.inventory -= demand
        else:
            self.revenue += self.inventory * 100
            self.inventory = 0

        if self.inventory < self.orderCutoff and self.numOrdered == 0:
            self.numOrdered = self.orderTarget - self.inventory
            self.costOrders += self.numOrdered * 50 
            self.tDelivery = self.clock + 2
        
        self.tCustomer = self.clock + self.generateInterarrival() 

    
    def handleDeliveryEvent(self):
        self.inventory += self.numOrdered
        self.numOrdered = 0
        self.tDelivery = float('inf')
    
    
    def generateInterarrival(self):
        return np.random.exponential(1.0 / 5.0)  # Avg. 5 customers/min

    def generateDemand(self):
        return np.random.randint(1, 5)  # because upper limit is exclusive
    

np.random.seed(0)
s = Simulation(10, 30)

while s.clock <= 2.0:
    s.advanceTime()
    print(f'{s.clock:.2f} \t {s.inventory} \t {s.revenue} \n')