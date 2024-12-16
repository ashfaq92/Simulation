import random
import numpy as np
import simpy
from hospital import HospitalSimulation
from monitor import Monitor
from scipy.stats import t, sem
from collections import defaultdict

def verify_distributions(config, seed, n_samples=10000):
    """Verify that distributions are generating correct values"""
    random.seed(seed)
    hospital = HospitalSimulation(simpy.Environment(), config)
    
    samples = {
        'interarrival': [],
        'prep': [],
        'operation': [],
        'recovery': []
    }
    
    for _ in range(n_samples):
        samples['interarrival'].append(hospital.generate_interarrival_time())
        samples['prep'].append(hospital.generate_prep_time())
        samples['operation'].append(hospital.generate_operation_time())
        samples['recovery'].append(hospital.generate_recovery_time())
    
    results = {}
    for name, data in samples.items():
        results[name] = {
            'mean': np.mean(data),
            'std': np.std(data),
            'min': np.min(data),
            'max': np.max(data)
        }
    
    return results

def verify_factorial_design():
    """Verify that factorial design is properly balanced"""
    from sim_run import generate_factorial_design
    
    design = generate_factorial_design()
    
    # Check number of experiments
    assert len(design) == 8, "Design should have 8 experiments"
    
    # Check balance for each factor
    for factor in range(6):
        zeros = sum(1 for row in design if row[factor] == 0)
        ones = sum(1 for row in design if row[factor] == 1)
        assert zeros == ones == 4, f"Factor {factor} is not balanced"
    
    return True

def verify_serial_correlation(config, seed):
    """Verify serial correlation in queue lengths"""
    from sim_run import analyze_serial_correlation
    
    correlations = analyze_serial_correlation(config, [seed])
    return correlations

if __name__ == "__main__":
    base_config = {
        'num_prep_rooms': 4,
        'num_recovery_rooms': 4,
        'mean_interarrival_time': 25,
        'mean_prep_time': 40,
        'mean_operation_time': 20,
        'mean_recovery_time': 40,
        'arrival_dist': 'exp',
        'prep_dist': 'exp',
        'recovery_dist': 'exp',
        'check_interval': 5,
        'warm_time': 1000,
        'sim_time': 1000
    }
    
    print("Verifying distributions...")
    dist_results = verify_distributions(base_config, 42)
    for dist_name, stats in dist_results.items():
        print(f"\n{dist_name.capitalize()} distribution:")
        for stat_name, value in stats.items():
            print(f"{stat_name}: {value:.4f}")
    
    print("\nVerifying factorial design...")
    try:
        verify_factorial_design()
        print("Factorial design is properly balanced")
    except AssertionError as e:
        print(f"Factorial design verification failed: {e}")
    
    print("\nVerifying serial correlation...")
    correlations = verify_serial_correlation(base_config, 42)
    for lag, corr in enumerate(correlations, 1):
        print(f"Lag {lag}: {corr:.4f}")