# monitor.py
import numpy as np

class Monitor:
    """Enhanced monitoring system"""
    def __init__(self, check_freq):
        self.check_freq = check_freq
        self.reset()
        
    def reset(self):
        # Queue and blocking samples
        self.prep_queue_samples = []
        self.op_blocking_samples = []
        self.recovery_full_samples = []
        
        # Utilization samples
        self.prep_util_samples = []
        self.op_util_samples = []
        self.recovery_util_samples = []
        
        # Additional samples
        self.prep_waiting_samples = []
        self.op_waiting_samples = []
        self.recovery_waiting_samples = []
        
        self.sample_count = 0
        
    def run(self, hospital, env):
        """Regular sampling of system state"""
        while True:
            # Sample queue lengths
            self.prep_queue_samples.append(len(hospital.prep_rooms.queue))
            self.op_waiting_samples.append(len(hospital.operating_room.queue))
            self.recovery_waiting_samples.append(len(hospital.recovery_rooms.queue))
            
            # Sample OR blocking
            self.op_blocking_samples.append(1 if hospital.is_blocking else 0)
            
            # Sample recovery room fullness
            recovery_usage = len(hospital.recovery_rooms.users) + len(hospital.recovery_rooms.queue)
            self.recovery_full_samples.append(
                1 if recovery_usage >= hospital.recovery_rooms.capacity else 0
            )
            
            # Sample utilizations
            self.prep_util_samples.append(
                len(hospital.prep_rooms.users) / hospital.prep_rooms.capacity
            )
            self.op_util_samples.append(
                len(hospital.operating_room.users)  # Capacity is 1
            )
            self.recovery_util_samples.append(
                len(hospital.recovery_rooms.users) / hospital.recovery_rooms.capacity
            )
            
            self.sample_count += 1
            yield env.timeout(self.check_freq)
            
    def get_results(self):
        """Compute averages for the sampling period"""
        if self.sample_count == 0:
            return 0, 0, 0, 0, 0, 0
        
        return (
            np.mean(self.prep_queue_samples),
            np.mean(self.op_blocking_samples),
            np.mean(self.recovery_full_samples),
            np.mean(self.prep_util_samples),
            np.mean(self.op_util_samples),
            np.mean(self.recovery_util_samples)
        )



    def get_raw_data(self):
        """Return raw sample data for detailed analysis"""
        if self.sample_count == 0:
            return {}
            
        return {
            'prep_queue': np.array(self.prep_queue_samples),
            'op_blocking': np.array(self.op_blocking_samples),
            'recovery_full': np.array(self.recovery_full_samples),
            'prep_util': np.array(self.prep_util_samples),
            'op_util': np.array(self.op_util_samples),
            'recovery_util': np.array(self.recovery_util_samples),
            'op_waiting': np.array(self.op_waiting_samples),
            'recovery_waiting': np.array(self.recovery_waiting_samples)
        }

    def get_statistics(self):
        """Get detailed statistics of all measures"""
        raw_data = self.get_raw_data()
        if not raw_data:
            return {}
            
        stats = {}
        for name, data in raw_data.items():
            stats[name] = {
                'mean': np.mean(data),
                'std': np.std(data),
                'min': np.min(data),
                'max': np.max(data),
                'samples': len(data)
            }
        return stats