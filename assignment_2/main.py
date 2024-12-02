import simpy
import random
import numpy as np
from dataclasses import dataclass

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

@dataclass
class Patient:
    """Patient with service times"""
    id: int
    arrival_time: float
    prep_time: float
    operation_time: float
    recovery_time: float

class Monitor:
    """System monitor"""
    def __init__(self, check_freq, iter_count):
        self.check = check_freq
        self.iter = iter_count
        self.block_freq = 0
        self.oper_freq = 0
        self.check_freq = 0
        self.bf_dump = []
        self.op_dump = []
        
    def reset(self):
        self.block_freq = 0
        self.check_freq = 0
        self.oper_freq = 0
        
    def report(self, it):
        self.bf_dump.append(self.block_freq)
        self.op_dump.append(self.oper_freq)
        
    def run(self, hospital, env):
        while True:
            yield env.timeout(self.check)
            self.check_freq += 1
            if hospital.is_blocking:
                self.block_freq += 1
            if hospital.is_operational:
                self.oper_freq += 1
    
    def dump(self):
        return {
            'blocking_mean': np.mean(self.bf_dump),
            'blocking_std': np.std(self.bf_dump),
            'operational_mean': np.mean(self.op_dump),
            'operational_std': np.std(self.op_dump)
        }

class HospitalSimulation:
    def __init__(self, env: simpy.Environment, config: dict):
        self.env = env
        self.config = config

        # Resources
        self.prep_rooms = simpy.Resource(env, capacity=config['num_prep_rooms'])
        self.operating_room = simpy.Resource(env, capacity=1)
        self.recovery_rooms = simpy.Resource(env, capacity=config['num_recovery_rooms'])

        # Statistics
        self.total_patients = 0
        self.pre_wait = 0
        self.op_wait = 0
        self.post_wait = 0
        self.is_blocking = False
        self.is_operational = False

        # Random streams
        self.interarrival_stream = Stream('exp', config['mean_interarrival_time'])
        self.prep_stream = Stream('unif', config['mean_prep_time'], config['prep_time_var'])
        self.operation_stream = Stream('exp', config['mean_operation_time'])
        self.recovery_stream = Stream('unif', config['mean_recovery_time'], config['recovery_time_var'])

    def reset(self):
        """Reset statistics"""
        self.pre_wait = 0
        self.op_wait = 0
        self.post_wait = 0
        
    def generate_patients(self, runtime):
        """Generate new patients"""
        while self.env.now < runtime:
            self.total_patients += 1
            patient = Patient(
                id=self.total_patients,
                arrival_time=self.env.now,
                prep_time=self.prep_stream.new(),
                operation_time=self.operation_stream.new(),
                recovery_time=self.recovery_stream.new()
            )

            self.env.process(self.patient_flow(patient))
            yield self.env.timeout(self.interarrival_stream.new())

    def patient_flow(self, patient: Patient):
        """Process a single patient through the hospital system"""
        # Preparation phase
        pre_req = self.prep_rooms.request()
        op_req = self.operating_room.request()
        post_req = self.recovery_rooms.request()

        arrival_time = self.env.now
        yield pre_req
        yield self.env.timeout(patient.prep_time)
        
        # Operation phase
        yield op_req
        self.is_operational = True
        op_wait_time = self.env.now
        self.pre_wait += self.env.now - arrival_time
        self.prep_rooms.release(pre_req)

        yield self.env.timeout(patient.operation_time)
        self.is_operational = False
        self.is_blocking = True
        
        # Recovery phase
        yield post_req
        self.is_blocking = False
        post_wait_time = self.env.now
        self.op_wait += self.env.now - op_wait_time
        self.operating_room.release(op_req)

        yield self.env.timeout(patient.recovery_time)
        self.recovery_rooms.release(post_req)
        self.post_wait += self.env.now - post_wait_time

def run_simulation(config: dict):
    """Run simulation with given configuration"""
    random.seed(config['random_seed'])
    
    total_time = config['repeats'] * (config['warm_time'] + config['sim_time'])
    reporter = Monitor(config['check_interval'], config['repeats'])
    
    env = simpy.Environment()
    hospital = HospitalSimulation(env, config)
    
    # Start processes
    env.process(hospital.generate_patients(total_time))
    env.process(reporter.run(hospital, env))
    
    # Run simulation with repeats
    for i in range(config['repeats']):
        env.run(until=env.now + config['warm_time'])
        reporter.reset()
        hospital.reset()
        env.run(until=env.now + config['sim_time'])
        reporter.report(i)
    
    return reporter.dump()

if __name__ == "__main__":
    config = {
        'num_prep_rooms': 4,
        'num_recovery_rooms': 4,
        'mean_interarrival_time': 25,
        'mean_prep_time': 40,
        'prep_time_var': 10,
        'mean_operation_time': 20,
        'mean_recovery_time': 40,
        'recovery_time_var': 10,
        'check_interval': 10,
        'warm_time': 1000,
        'sim_time': 10000,
        'repeats': 10,
        'random_seed': 42
    }

    # Run simulation and print results
    results = run_simulation(config)
    print("\nSimulation Results:")
    for metric, value in results.items():
        print(f"{metric}: {value:.2f}")