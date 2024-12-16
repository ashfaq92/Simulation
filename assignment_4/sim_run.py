import random
import simpy
import numpy as np
from scipy.stats import t
from dataclasses import dataclass
from hospital import HospitalSimulation
from monitor import Monitor
from scipy.stats import sem
import pandas as pd
from sklearn.linear_model import LinearRegression
from itertools import combinations
from patient import Severity  # Add this import


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
            std_err = sem(values)
            t_val = t.ppf((1 + confidence) / 2, len(values) - 1)
            ci = (mean - t_val * std_err, mean + t_val * std_err)
            
            stats_dict[f'{metric_name}_mean'] = mean
            stats_dict[f'{metric_name}_ci'] = ci
        return stats_dict

def generate_factorial_design():
    """Generate 2^(6-3) factorial design"""
    # Basic factors:
    # A: Arrival distribution (0=exp(25), 1=exp(22.5))
    # B: Arrival distribution type (0=exp, 1=unif)
    # C: Prep time distribution (0=exp(40), 1=unif(30,50))
    # D: Recovery time distribution (0=exp(40), 1=unif(30,50))
    # E: Number of prep units (0=4, 1=5)
    # F: Number of recovery units (0=4, 1=5)
    
    # Generate full factorial design for first 3 factors
    base_design = [[i >> j & 1 for j in range(3)] for i in range(8)]
    
    # Generate other factors based on defining relations
    full_design = []
    for row in base_design:
        # Example defining relations (can be modified):
        D = (row[0] + row[1]) % 2
        E = (row[0] + row[2]) % 2
        F = (row[1] + row[2]) % 2
        full_design.append(row + [D, E, F])
    
    return full_design

def interpret_results(regression_results, correlations):
    print("\nInterpretation of Results:")
    print("\nFactor Effects (ordered by magnitude):")
    coeffs = regression_results['coefficients']
    sorted_coeffs = sorted(coeffs, key=lambda x: abs(x[1]), reverse=True)
    
    for factor, coef in sorted_coeffs:
        effect = "increases" if coef > 0 else "decreases"
        print(f"Factor {factor} {effect} queue length by {abs(coef):.4f}")
    
    print("\nSerial Correlation Interpretation:")
    print(f"Short-term correlation (lag 1): {correlations[0]:.4f}")
    print(f"Medium-term correlation (lag 4): {correlations[3]:.4f}")
    if len(correlations) > 6:
        print(f"Long-term correlation (lag 7): {correlations[6]:.4f}")

def analyze_serial_correlation(config, seeds, n_runs=10, n_samples=8):
    """Analyze serial correlation with error handling and confidence intervals"""
    results = []
    
    try:
        for seed in seeds[:n_runs]:
            random.seed(seed)
            env = simpy.Environment()
            hospital = HospitalSimulation(env, config)
            monitor = Monitor(config['check_interval'])
            
            env.process(hospital.generate_patients())
            env.process(monitor.run(hospital, env))
            
            samples = []
            sample_interval = config['sim_time'] / n_samples
            
            with np.errstate(divide='ignore', invalid='ignore'):
                for i in range(n_samples):
                    env.run(until=(i+1)*sample_interval)
                    current_length = monitor.current_queue_length()
                    if not np.isnan(current_length):
                        samples.append(current_length)
            
            if len(samples) >= n_samples:
                results.append(samples)
        
        correlations = []
        confidence_intervals = []
        
        for lag in range(1, n_samples-1):
            lag_corrs = []
            for run in results:
                series = pd.Series(run)
                if len(series) > lag + 1:
                    with np.errstate(divide='ignore', invalid='ignore'):
                        lag_corr = series.autocorr(lag=lag)
                        if not np.isnan(lag_corr):
                            lag_corrs.append(lag_corr)
            
            if lag_corrs:
                mean_corr = np.mean(lag_corrs)
                std_err = sem(lag_corrs)
                t_val = t.ppf(0.975, len(lag_corrs)-1)
                ci = (mean_corr - t_val * std_err, mean_corr + t_val * std_err)
                
                correlations.append(mean_corr)
                confidence_intervals.append(ci)
            else:
                correlations.append(np.nan)
                confidence_intervals.append((np.nan, np.nan))
        
        return correlations, confidence_intervals
    
    except Exception as e:
        print(f"Error in serial correlation analysis: {str(e)}")
        return [], []

def create_config_from_factors(factors):
    config = {
        'mean_operation_time': 20,
        'check_interval': 5,
        'warm_time': 3000,
        'sim_time': 10000,
        'severity_distribution': {
            Severity.LOW: 0.3,    # 30% low severity
            Severity.MEDIUM: 0.5, # 50% medium severity
            Severity.HIGH: 0.2    # 20% high severity
        },
        'warm_up_window': 100,
        'warm_up_threshold': 0.01,
        'target_utilization': 0.8  # 80% target utilization
    }
    
    # Even bigger difference in arrival rates
    if factors[0] == 0:
        config['mean_interarrival_time'] = 40
    else:
        config['mean_interarrival_time'] = 10
    
    # Distribution types
    config['arrival_dist'] = 'exp' if factors[1] == 0 else 'unif'
    config['prep_dist'] = 'exp' if factors[2] == 0 else 'unif'
    config['recovery_dist'] = 'exp' if factors[3] == 0 else 'unif'
    
    # Even bigger difference in number of units
    config['num_prep_rooms'] = 2 if factors[4] == 0 else 7
    config['num_recovery_rooms'] = 2 if factors[5] == 0 else 7
    
    return config

def run_factorial_experiment(seeds):
    """Run the factorial experiment"""
    design = generate_factorial_design()
    results = []
    
    for factors in design:
        config = create_config_from_factors(factors)
        sim_results = run_configuration(config, seeds)
        stats = sim_results.compute_statistics()
        results.append({
            'factors': factors,
            'queue_length': stats['prep_queue_length_mean']
        })
    
    return results

def perform_regression_analysis(results):
    """Perform regression analysis with confidence intervals"""
    X = np.array([r['factors'] for r in results])
    y = np.array([r['queue_length'] for r in results])
    
    # Scale the response variable
    y = (y - np.mean(y)) / np.std(y)
    
    # Fit model
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate confidence intervals
    n = len(y)
    p = X.shape[1]
    dof = n - p - 1
    mse = np.sum((y - model.predict(X)) ** 2) / dof
    
    # Standard errors for coefficients
    X_pinv = np.linalg.pinv(X)
    var_coef = np.diagonal(mse * (X_pinv @ X_pinv.T))
    std_errs = np.sqrt(var_coef)
    
    # 95% confidence intervals
    t_val = t.ppf(0.975, dof)
    ci_lower = model.coef_ - t_val * std_errs
    ci_upper = model.coef_ + t_val * std_errs
    
    # Combine results
    coefficients = []
    for i, (name, coef, ci_l, ci_u) in enumerate(zip(
        ['A', 'B', 'C', 'D', 'E', 'F'], 
        model.coef_, 
        ci_lower, 
        ci_upper
    )):
        coefficients.append({
            'factor': name,
            'coef': coef,
            'ci': (ci_l, ci_u)
        })
    
    return {
        'coefficients': coefficients,
        'intercept': model.intercept_,
        'r_squared': model.score(X, y)
    }

def run_configuration(config, seeds):
    """Run multiple simulations with given configuration and seeds"""
    prep_queue_lengths = []
    op_blocking_probs = []
    recovery_full_probs = []
    
    for seed in seeds:
        random.seed(seed)
        env = simpy.Environment()
        hospital = HospitalSimulation(env, config)
        monitor = Monitor(config['check_interval'])
        
        env.process(hospital.generate_patients())
        env.process(monitor.run(hospital, env))
        
        # Increase simulation time and warm-up period
        config['warm_time'] = 2000  # Double the warm-up time
        config['sim_time'] = 5000   # Increase simulation time
        
        # Run simulation
        env.run(until=config['warm_time'] + config['sim_time'])
        
        # Collect statistics
        prep_queue_lengths.append(monitor.current_queue_length())
        op_blocking_probs.append(monitor.operation_blocking_probability())
        recovery_full_probs.append(monitor.recovery_full_probability())
    
    return SimulationResults(
        prep_queue_lengths=prep_queue_lengths,
        op_blocking_prob=op_blocking_probs,
        recovery_full_prob=recovery_full_probs
    )


def run_simulation(config, seed=None):
    """Enhanced simulation run with warm-up detection"""
    env = simpy.Environment()
    hospital = HospitalSimulation(env, config)
    monitor = Monitor(config['check_interval'])
    
    # Add monitor process
    env.process(monitor.run(hospital, env))
    
    # Run initial warm-up period
    env.run(until=config['warm_time'])
    
    # Check for steady state
    steady_state_time = monitor.detect_steady_state(
        window=config['warm_up_window'],
        threshold=config['warm_up_threshold']
    )
    
    # Reset statistics after warm-up
    monitor.reset()
    
    # Continue simulation for main data collection
    env.run(until=config['sim_time'])
    
    # Calculate final metrics
    results = {
        'queue_length': monitor.current_queue_length(),
        'theater_utilization': hospital.calculate_theater_utilization(),
        'blocking_probability': monitor.operation_blocking_probability(),
        'recovery_full_probability': monitor.recovery_full_probability(),
        'warm_up_time': steady_state_time
    }
    
    return results


if __name__ == "__main__":
    seeds = list(range(42, 242))  # Increase to 200 replications
    
    # Run factorial experiment
    results = run_factorial_experiment(seeds)
    
    # Perform regression analysis
    regression_results = perform_regression_analysis(results)
    
    # Analyze serial correlation
    base_config = create_config_from_factors([0, 0, 0, 0, 0, 0])
    correlations, correlation_cis = analyze_serial_correlation(base_config, seeds)
    
    # Print detailed results
    print("\nRegression Analysis Results:")
    print(f"R-squared: {regression_results['r_squared']:.4f}")
    print("\nCoefficients with 95% Confidence Intervals:")
    for coef in regression_results['coefficients']:
        print(f"Factor {coef['factor']}: {coef['coef']:.4f} ({coef['ci'][0]:.4f}, {coef['ci'][1]:.4f})")
    print(f"Intercept: {regression_results['intercept']:.4f}")
    
    print("\nSerial Correlation Analysis:")
    for lag, (corr, ci) in enumerate(zip(correlations, correlation_cis), 1):
        if not np.isnan(corr):
            print(f"Lag {lag}: {corr:.4f} ({ci[0]:.4f}, {ci[1]:.4f})")
    
    # Interpret results
    print("\nSignificant Factors (p < 0.05):")
    for coef in regression_results['coefficients']:
        if coef['ci'][0] * coef['ci'][1] > 0:  # CI doesn't include 0
            effect = "increases" if coef['coef'] > 0 else "decreases"
            print(f"Factor {coef['factor']} significantly {effect} queue length")
    
    print("\nDetailed Analysis:")
    print("\nFactor Effects (ordered by magnitude):")
    sorted_coeffs = sorted(regression_results['coefficients'], 
                         key=lambda x: abs(x['coef']), 
                         reverse=True)
    
    for coef in sorted_coeffs:
        effect = "increases" if coef['coef'] > 0 else "decreases"
        print(f"\nFactor {coef['factor']}:")
        print(f"  Effect: {effect} queue length by {abs(coef['coef']):.4f}")
        print(f"  95% CI: ({coef['ci'][0]:.4f}, {coef['ci'][1]:.4f})")
        print(f"  Significant: {'Yes' if coef['ci'][0] * coef['ci'][1] > 0 else 'No'}")