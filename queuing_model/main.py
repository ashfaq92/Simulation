import numpy as np
import statistics


class Simulation:
    def __init__(self):
        self.num_in_system = 0  # number of customers in the system
        self.clock = 0  # initialize time to 0
        self.t_arrival = self.generate_interarrival()
        self.t_depart = float('inf')  # no departure scheduled initially

        # statistical counters
        self.num_arrivals = 0
        self.num_departs = 0
        self.total_wait = 0.0
    
    def advance_time(self):
        # Determine the time of the next event (either arrival or departure)
        t_event = min(self.t_arrival, self.t_depart)
        # Update the total waiting time for all customers currently in the system
        self.total_wait += self.num_in_system * (t_event - self.clock)
        # Advance the simulation clock to the time of the next event
        self.clock = t_event
        # Check if the next event is an arrival or a departure
        if self.t_arrival <= self.t_depart:
            self.handle_arrival_event()
        else:
            self.handle_departure_event()
    
    def handle_arrival_event(self):
        self.num_in_system += 1
        self.num_arrivals += 1
        if self.num_in_system <= 1:
            self.t_depart = self.clock + self.generate_service()
        self.t_arrival = self.generate_interarrival() + self.clock

    def handle_departure_event(self):
        self.num_in_system -= 1
        self.num_departs += 1
        if self.num_in_system > 0:
            self.t_depart = self.clock + self.generate_service()
        else:
            self.t_depart = float('inf')

    def generate_interarrival(self):
        return np.random.exponential(1.0/3.0)

    def generate_service(self):
        return np.random.exponential(1.0/4.0)
    

np.random.seed(0)
s = Simulation()

for i in range(100):
    s.advance_time()

print('number in system', s.num_in_system)
print('total arrivals', s.num_arrivals)
print('total departures', s.num_departs)
print('total wait', s.total_wait)