import random
import simpy

class HospitalSimulation:
    def __init__(self, env, config):
        self.env = env
        self.config = config
        
        self.operation_time = 0
        self.total_time = 0
        self.last_operation_start = 0

        # Resources
        self.prep_rooms = simpy.Resource(env, capacity=config['num_prep_rooms'])
        self.operation_room = simpy.Resource(env, capacity=1)
        self.recovery_rooms = simpy.Resource(env, capacity=config['num_recovery_rooms'])
        
        # Statistics
        self.prep_queue = []
        self.operation_blocked = False
        self.recovery_full = False
    
    def generate_time(self, mean, dist_type='exp', min_val=None, max_val=None):
        """Generate time based on distribution type"""
        if dist_type == 'exp':
            return random.expovariate(1.0 / mean)
        elif dist_type == 'unif':
            # For uniform distribution, we use the provided min and max values
            # or calculate them to maintain the same mean
            if min_val is None or max_val is None:
                # Default to ±25% of mean for uniform distribution
                min_val = 0.75 * mean
                max_val = 1.25 * mean
            return random.uniform(min_val, max_val)
        else:
            raise ValueError(f"Unknown distribution type: {dist_type}")

    def generate_interarrival_time(self):
        """Generate time between patient arrivals"""
        if self.config['arrival_dist'] == 'unif':
            if self.config['mean_interarrival_time'] == 25:
                return self.generate_time(25, 'unif', 20, 30)
            else:  # mean = 22.5
                return self.generate_time(22.5, 'unif', 20, 25)
        else:  # exponential
            return self.generate_time(self.config['mean_interarrival_time'], 'exp')

    def generate_prep_time(self):
        """Generate preparation time"""
        if self.config['prep_dist'] == 'unif':
            return self.generate_time(40, 'unif', 30, 50)
        else:  # exponential
            return self.generate_time(40, 'exp')

    def generate_operation_time(self):
        """Generate operation time (always exponential)"""
        return self.generate_time(self.config['mean_operation_time'], 'exp')

    def generate_recovery_time(self):
        """Generate recovery time"""
        if self.config['recovery_dist'] == 'unif':
            return self.generate_time(40, 'unif', 30, 50)
        else:  # exponential
            return self.generate_time(40, 'exp')

    def patient_journey(self):
        """Simulate a single patient's journey through the hospital"""
        # Record arrival and queue length
        arrival_time = self.env.now
        self.prep_queue.append(arrival_time)
        
        # Preparation phase
        with self.prep_rooms.request() as prep_req:
            yield prep_req
            self.prep_queue.remove(arrival_time)
            yield self.env.timeout(self.generate_prep_time())
        
        # Operation phase
        with self.operation_room.request() as op_req:
            # Check if recovery is full before starting operation
            if self.recovery_rooms.count >= self.recovery_rooms.capacity:
                self.operation_blocked = True
                yield self.recovery_rooms.request()
                self.operation_blocked = False
            
            yield op_req
            yield self.env.timeout(self.generate_operation_time())
        
        # Recovery phase
        with self.recovery_rooms.request() as recovery_req:
            if self.recovery_rooms.count >= self.recovery_rooms.capacity:
                self.recovery_full = True
            yield recovery_req
            self.recovery_full = False
            yield self.env.timeout(self.generate_recovery_time())

    def generate_patients(self):
        """Generate new patients arriving at the hospital"""
        while True:
            # Create a new patient
            self.env.process(self.patient_journey())
            
            # Wait for next patient
            interarrival_time = self.generate_interarrival_time()
            yield self.env.timeout(interarrival_time)

    def get_current_queue_length(self):
        """Get current length of preparation queue"""
        return len(self.prep_queue)

    def is_operation_blocked(self):
        """Check if operation room is blocked"""
        return self.operation_blocked

    def is_recovery_full(self):
        """Check if recovery is full"""
        return self.recovery_full

    def calculate_theater_utilization(self):
        """Calculate operating theater utilization rate"""
        return self.operation_time / self.total_time if self.total_time > 0 else 0

    def start_operation(self, env):
        """Track operation start time"""
        self.last_operation_start = env.now

    def end_operation(self, env):
        """Update operation time tracking"""
        self.operation_time += env.now - self.last_operation_start
        self.total_time = env.now