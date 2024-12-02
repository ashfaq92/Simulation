import random
import simpy
import numpy as np
from scipy.stats import t
from dataclasses import dataclass
from hospital import HospitalSimulation
from monitor import Monitor
from scipy.stats import sem

@dataclass
class SimulationResults:
    """Container for simulation results"""
    prep_queue_lengths: list
    op_blocking_prob: list
    recovery_full_prob: list
    
    def compute_statistics(self, confidence=0.95):
        """Compute mean and confidence intervals for all metrics"""
        stats_dict = {}
        for metric_name, values in {
            'prep_queue_length': self.prep_queue_lengths,
            'op_blocking_prob': self.op_blocking_prob,
            'recovery_full_prob': self.recovery_full_prob
        }.items():
            mean = np.mean(values)
            # Fix the stats call
            sem = np.std(values, ddof=1) / np.sqrt(len(values))
            t_value = t.ppf((1 + confidence) / 2, len(values) - 1)
            conf_int = (mean - t_value * sem, mean + t_value * sem)
            
            stats_dict[f'{metric_name}_mean'] = mean
            stats_dict[f'{metric_name}_ci'] = conf_int
        return stats_dict

def run_configuration(config, seeds):
    """Run multiple replications of a single configuration"""
    results = SimulationResults([], [], [])
    
    for seed in seeds:
        random.seed(seed)
        env = simpy.Environment()
        hospital = HospitalSimulation(env, config)
        monitor = Monitor(config['check_interval'])
        
        # Start processes
        env.process(hospital.generate_patients())
        env.process(monitor.run(hospital, env))
        
        # Warm-up period
        env.run(until=config['warm_time'])
        monitor.reset()
        
        # Main simulation
        env.run(until=config['warm_time'] + config['sim_time'])
        
        # Collect results
        queue_length, blocking_prob, recovery_full = monitor.get_results()
        results.prep_queue_lengths.append(queue_length)
        results.op_blocking_prob.append(blocking_prob)
        results.recovery_full_prob.append(recovery_full)
    
    return results

def compare_configurations(seeds):
    """Run and compare different configurations"""
    configs = [
        {'num_prep_rooms': 3, 'num_recovery_rooms': 4},
        {'num_prep_rooms': 3, 'num_recovery_rooms': 5},
        {'num_prep_rooms': 4, 'num_recovery_rooms': 5}
    ]
    
    base_config = {
        'mean_interarrival_time': 25,
        'mean_prep_time': 40,
        'mean_operation_time': 20,
        'mean_recovery_time': 40,
        'check_interval': 5,
        'warm_time': 1000,
        'sim_time': 1000
    }
    
    results = {}
    for i, config in enumerate(configs):
        full_config = {**base_config, **config}
        label = f"{config['num_prep_rooms']}p{config['num_recovery_rooms']}r"
        results[label] = run_configuration(full_config, seeds)
    
    return results

if __name__ == "__main__":
    # Set up seeds for reproducibility and paired comparison
    seeds = list(range(42, 62))  # 20 seeds for 20 replications
    
    # Run all configurations
    results = compare_configurations(seeds)
    
    # Print results for each configuration
    for config_name, config_results in results.items():
        stats = config_results.compute_statistics()
        print(f"\nResults for configuration {config_name}:")
        for metric, value in stats.items():
            if 'ci' in metric:
                print(f"{metric}: ({value[0]:.4f}, {value[1]:.4f})")
            else:
                print(f"{metric}: {value:.4f}")
    
    # Perform paired comparisons
    print("\nPaired Comparisons:")
    configs = list(results.keys())
    for i in range(len(configs)):
        for j in range(i+1, len(configs)):
            config1, config2 = configs[i], configs[j]
            
            # Calculate differences
            queue_diff = np.array(results[config1].prep_queue_lengths) - np.array(results[config2].prep_queue_lengths)
            block_diff = np.array(results[config1].op_blocking_prob) - np.array(results[config2].op_blocking_prob)
            
            # Compute confidence intervals for differences
            for metric_name, diff in [("Queue Length", queue_diff), ("Blocking Prob", block_diff)]:
                mean_diff = np.mean(diff)
                ci = t.interval(0.95, len(diff)-1, loc=mean_diff, scale=sem(diff))
                print(f"\n{config1} vs {config2} - {metric_name}")
                print(f"Mean difference: {mean_diff:.4f}")
                print(f"95% CI: ({ci[0]:.4f}, {ci[1]:.4f})")
                
                # Check if difference is significant (CI doesn't contain 0)
                significant = (ci[0] * ci[1] > 0)
                print(f"Significant difference: {significant}")