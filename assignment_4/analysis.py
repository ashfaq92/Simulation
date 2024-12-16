import numpy as np
from scipy import stats
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class ExperimentAnalyzer:
    def __init__(self, results):
        self.results = results
        self.factor_names = ['Arrival Rate', 'Arrival Dist', 'Prep Dist', 
                           'Recovery Dist', 'Prep Units', 'Recovery Units']

    def create_effects_matrix(self):
        """Create matrix of main effects and interactions"""
        X = np.array([r['factors'] for r in self.results])
        y = np.array([r['queue_length'] for r in self.results])
        return X, y

    def plot_main_effects(self):
        """Plot main effects of each factor"""
        X, y = self.create_effects_matrix()
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        for i, (ax, name) in enumerate(zip(axes, self.factor_names)):
            low_mean = np.mean(y[X[:, i] == 0])
            high_mean = np.mean(y[X[:, i] == 1])
            
            ax.plot([0, 1], [low_mean, high_mean], 'bo-')
            ax.set_title(f'Main Effect of {name}')
            ax.set_xticks([0, 1])
            ax.set_xticklabels(['Low', 'High'])
            ax.set_ylabel('Average Queue Length')
        
        plt.tight_layout()
        return fig

    def plot_correlation_analysis(self, correlations):
        """Plot serial correlation analysis"""
        plt.figure(figsize=(10, 6))
        plt.plot(range(1, len(correlations) + 1), correlations, 'bo-')
        plt.xlabel('Lag')
        plt.ylabel('Correlation')
        plt.title('Serial Correlation Analysis')
        plt.grid(True)
        return plt.gcf()

    def analyze_significance(self):
        """Analyze statistical significance of factors"""
        X, y = self.create_effects_matrix()
        results = []
        
        for i, name in enumerate(self.factor_names):
            effect = np.mean(y[X[:, i] == 1]) - np.mean(y[X[:, i] == 0])
            t_stat, p_value = stats.ttest_ind(y[X[:, i] == 1], y[X[:, i] == 0])
            
            results.append({
                'Factor': name,
                'Effect': effect,
                'P-value': p_value,
                'Significant': p_value < 0.05
            })
        
        return pd.DataFrame(results)
    
    def analyze_utilization(self, results):
        """
        Analyze operating theater utilization across experiments
        
        Args:
            results (list): List of simulation results
            
        Returns:
            dict: Utilization analysis including:
                - Mean utilization
                - Confidence intervals
                - Distance from target (80%)
        """
        utilizations = [r['theater_utilization'] for r in results]
        mean_util = np.mean(utilizations)
        std_err = sem(utilizations)
        
        # 95% confidence interval
        ci = t.interval(0.95, len(utilizations)-1, mean_util, std_err)
        
        # Distance from target
        target_gap = mean_util - 0.8  # 0.8 is 80% target
        
        return {
            'mean_utilization': mean_util,
            'confidence_interval': ci,
            'target_gap': target_gap,
            'meets_target': mean_util >= 0.8
        }