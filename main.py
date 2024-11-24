import simpy
import random
from dataclasses import dataclass


@dataclass
class Patient:
    """Patient with service times"""
    id: int
    arrival_time: float
    prep_time: float
    operation_time: float
    recovery_time: float


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
        self.queue_lengths = []
        self.or_busy_times = []  # Tracks periods when OR is actively in use
        self.or_blocked_times = []  # Tracks periods when OR is blocked
        self.patient_times = []  # Total time in system for each patient

        # Start monitoring
        self.env.process(self.monitor())

    def monitor(self):
        """Monitor queue length periodically"""
        while True:
            self.queue_lengths.append(len(self.prep_rooms.queue))
            yield self.env.timeout(self.config['monitoring_interval'])

    def generate_patients(self):
        """Generate new patients"""
        while True:
            self.total_patients += 1
            patient = Patient(
                id=self.total_patients,
                arrival_time=self.env.now,
                prep_time=random.expovariate(1.0 / self.config['mean_prep_time']),
                operation_time=random.expovariate(1.0 / self.config['mean_operation_time']),
                recovery_time=random.expovariate(1.0 / self.config['mean_recovery_time'])
            )

            print(f"Patient {patient.id} arrives at {self.env.now:.1f}")
            self.env.process(self.patient_flow(patient))

            yield self.env.timeout(random.expovariate(1.0 / self.config['mean_interarrival_time']))

    def patient_flow(self, patient: Patient):
        """Process a single patient through the hospital system"""
        arrival = self.env.now

        # Preparation phase
        with self.prep_rooms.request() as prep_req:
            yield prep_req
            print(f"Patient {patient.id} starts preparation at {self.env.now:.1f}")
            yield self.env.timeout(patient.prep_time)

        # Operation phase
        with self.operating_room.request() as or_req:
            yield or_req
            op_start = self.env.now
            print(f"Patient {patient.id} starts operation at {self.env.now:.1f}")
            yield self.env.timeout(patient.operation_time)

            # Try to get recovery room - OR might be blocked here
            block_start = self.env.now
            with self.recovery_rooms.request() as recovery_req:
                yield recovery_req

                # Record OR statistics
                if self.env.now > block_start:  # OR was blocked
                    self.or_blocked_times.append(self.env.now - block_start)
                self.or_busy_times.append(block_start - op_start)  # Actual operation time

                # Recovery phase
                print(f"Patient {patient.id} starts recovery at {self.env.now:.1f}")
                yield self.env.timeout(patient.recovery_time)

        # Record total time
        self.patient_times.append(self.env.now - arrival)
        print(f"Patient {patient.id} completes at {self.env.now:.1f}")


def run_simulation(config: dict):
    """Run simulation with given configuration"""
    # Setup
    env = simpy.Environment()
    hospital = HospitalSimulation(env, config)

    # Start patient generation
    env.process(hospital.generate_patients())

    # Run simulation
    env.run(until=config['sim_duration'])

    # Calculate statistics
    stats = {
        'total_patients': hospital.total_patients,
        'avg_queue_length': sum(hospital.queue_lengths) / len(hospital.queue_lengths) if hospital.queue_lengths else 0,
        'or_utilization': sum(hospital.or_busy_times) / config['sim_duration'] * 100,
        'avg_blocking_time': sum(hospital.or_blocked_times) / len(
            hospital.or_blocked_times) if hospital.or_blocked_times else 0,
        'avg_patient_time': sum(hospital.patient_times) / len(hospital.patient_times) if hospital.patient_times else 0
    }
    return stats


if __name__ == "__main__":
    config = {
        'num_prep_rooms': 3,
        'num_recovery_rooms': 3,
        'mean_interarrival_time': 25,
        'mean_prep_time': 40,
        'mean_operation_time': 20,
        'mean_recovery_time': 40,
        'monitoring_interval': 5,
        'sim_duration': 1000,
        'random_seed': 42
    }

    # Set random seed
    random.seed(config['random_seed'])

    # Run simulation and print results
    results = run_simulation(config)
    print("\nSimulation Results:")
    for metric, value in results.items():
        print(f"{metric}: {value:.2f}")