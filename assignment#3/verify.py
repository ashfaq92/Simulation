import random
import numpy as np
import simpy
from hospital import HospitalSimulation
from monitor import Monitor
from scipy.stats import t, sem
from collections import defaultdict


def verify_rates(config, seed, duration=10000):
    """Verify actual arrival and service rates"""
    random.seed(seed)
    env = simpy.Environment()
    arrivals = []
    services = defaultdict(list)  # Track prep, op, and recovery times
    last_time = 0
    
    hospital = HospitalSimulation(env, config)
    
    def track_timing():
        nonlocal last_time
        while True:
            interarrival = hospital.interarrival_stream.new()
            yield env.timeout(interarrival)
            arrivals.append(env.now - last_time)
            last_time = env.now
            
            # Sample service times
            services['prep'].append(hospital.prep_stream.new())
            services['op'].append(hospital.operation_stream.new())
            services['recovery'].append(hospital.recovery_stream.new())
    
    env.process(track_timing())
    env.run(until=duration)
    
    results = {
        'arrivals': {
            'theoretical_rate': 1/config['mean_interarrival_time'],
            'actual_rate': len(arrivals) / duration,
            'actual_mean': np.mean(arrivals),
            'actual_std': np.std(arrivals)
        }
    }
    
    # Map service types to config keys
    service_map = {
        'prep': 'prep',
        'op': 'operation',
        'recovery': 'recovery'
    }
    
    for service_type, config_key in service_map.items():
        results[service_type] = {
            'theoretical_mean': config[f'mean_{config_key}_time'],
            'actual_mean': np.mean(services[service_type]),
            'actual_std': np.std(services[service_type])
        }
    
    return results

def verify_warmup(config, seed):
    """Run a longer simulation to check warm-up period adequacy"""
    random.seed(seed)
    env = simpy.Environment()
    hospital = HospitalSimulation(env, config)
    monitor = Monitor(config['check_interval'])
    
    env.process(hospital.generate_patients())
    env.process(monitor.run(hospital, env))
    
    # Run for 5x the current warm-up period
    env.run(until=5 * config['warm_time'])
    
    # Get raw data
    raw_data = monitor.get_raw_data()
    
    # Calculate moving averages with different window sizes
    windows = [50, 100, 200]
    mas = {}
    
    for window in windows:
        mas[window] = {
            metric: np.convolve(data, np.ones(window)/window, mode='valid')
            for metric, data in raw_data.items()
        }
    
    return mas

def verify_simulation(base_config):
    """Run comprehensive verification of the simulation"""
    seed = 42
    
    print("Starting simulation verification...")
    
    print("\n1. Rate Verification:")
    rates = verify_rates(base_config, seed)
    print("\nArrival process:")
    for metric, value in rates['arrivals'].items():
        print(f"{metric}: {value:.4f}")
    
    # Use same service types as in verify_rates
    for service_type in ['prep', 'op', 'recovery']:
        print(f"\n{service_type.capitalize()} service times:")
        for metric, value in rates[service_type].items():
            print(f"{metric}: {value:.4f}")
    
    print("\n2. Warm-up Analysis:")
    mas = verify_warmup(base_config, seed)
    for window, metrics in mas.items():
        print(f"\nWindow size: {window}")
        for metric, values in metrics.items():
            stabilized_mean = np.mean(values[-100:])
            print(f"{metric} stabilizes around: {stabilized_mean:.4f}")
    
    print("\n3. Extended Run Analysis:")
    extended_config = {**base_config, 'sim_time': 5000}
    env = simpy.Environment()
    hospital = HospitalSimulation(env, extended_config)
    monitor = Monitor(extended_config['check_interval'])
    
    env.process(hospital.generate_patients())
    env.process(monitor.run(hospital, env))
    
    # Run with warm-up
    env.run(until=extended_config['warm_time'])
    monitor.reset()
    
    # Main run
    env.run(until=extended_config['warm_time'] + extended_config['sim_time'])
    
    stats = monitor.get_statistics()
    print("\nExtended simulation statistics:")
    for metric, values in stats.items():
        print(f"\n{metric}:")
        for stat_name, stat_value in values.items():
            print(f"{stat_name}: {stat_value:.4f}")

if __name__ == "__main__":
    base_config = {
        'num_prep_rooms': 3,
        'num_recovery_rooms': 4,
        'mean_interarrival_time': 25,
        'mean_prep_time': 40,
        'mean_operation_time': 20,
        'mean_recovery_time': 40,
        'check_interval': 5,
        'warm_time': 1000,
        'sim_time': 1000
    }
    
    verify_simulation(base_config)