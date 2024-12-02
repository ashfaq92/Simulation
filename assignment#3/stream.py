import random

class Stream:
    """Random number stream wrapper"""
    def __init__(self, type_name, *args):
        self.type = type_name
        if type_name == 'exp':
            self.p1 = args[0]
        elif type_name == 'unif':
            self.p1 = args[0] - args[1]
            self.p2 = args[0] + args[1]
            
    def new(self):
        if self.type == 'exp':
            return random.expovariate(1/self.p1)
        elif self.type == 'unif':
            return random.uniform(self.p1, self.p2)