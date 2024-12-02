import simpy
from stream import Stream
from patient import Patient

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

        # Random streams - all exponential as per specification
        self.interarrival_stream = Stream('exp', config['mean_interarrival_time'])
        self.prep_stream = Stream('exp', config['mean_prep_time'])
        self.operation_stream = Stream('exp', config['mean_operation_time'])
        self.recovery_stream = Stream('exp', config['mean_recovery_time'])

    def reset(self):
        """Reset statistics"""
        self.pre_wait = 0
        self.op_wait = 0
        self.post_wait = 0
        
    def generate_patients(self):
        """Generate new patients"""
        while True:
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
        yield pre_req  # Request prep room first
        yield self.env.timeout(patient.prep_time)
        
        # Operation phase
        op_req = self.operating_room.request()
        yield op_req  # Request OR after prep is done
        self.is_operational = True
        self.prep_rooms.release(pre_req)  # Release prep room only after OR is secured
        yield self.env.timeout(patient.operation_time)
        
        # Recovery phase
        post_req = self.recovery_rooms.request()
        yield post_req  # Request recovery room
        self.is_operational = False
        self.operating_room.release(op_req)  # Release OR only after recovery room is secured
        yield self.env.timeout(patient.recovery_time)
        self.recovery_rooms.release(post_req)