class Monitor:
    def __init__(self, check_interval):
        self.check_interval = check_interval
        self.queue_length_history = []
        self.reset()
    
    def reset(self):
        """Reset all counters"""
        self.queue_length_sum = 0
        self.operation_blocked_time = 0
        self.recovery_full_time = 0
        self.num_checks = 0
    
    def current_queue_length(self):
        """Get current queue length"""
        return self.queue_length_sum / self.num_checks if self.num_checks > 0 else 0

    def run(self, hospital, env):
        """Monitor the hospital system"""
        while True:
            # Record current state
            self.queue_length_sum += hospital.get_current_queue_length()
            self.operation_blocked_time += 1 if hospital.is_operation_blocked() else 0
            self.recovery_full_time += 1 if hospital.is_recovery_full() else 0
            self.num_checks += 1
            
            # Wait for next check
            yield env.timeout(self.check_interval)

    def operation_blocking_probability(self):
        """Calculate the probability that operations were blocked"""
        return self.operation_blocked_time / self.num_checks if self.num_checks > 0 else 0

    def recovery_full_probability(self):
        """Calculate the probability that recovery was full"""
        return self.recovery_full_time / self.num_checks if self.num_checks > 0 else 0
    
    def get_results(self):
        """Get average results"""
        if self.num_checks == 0:
            return 0, 0, 0
        
        avg_queue_length = self.queue_length_sum / self.num_checks
        blocking_probability = self.operation_blocked_time / self.num_checks
        recovery_full_probability = self.recovery_full_time / self.num_checks
        
        return avg_queue_length, blocking_probability, recovery_full_probability
    
    def detect_steady_state(self, window=100, threshold=0.01):
        """
        Detect when system reaches steady state based on queue length stability
        
        Args:
            window (int): Rolling window size for mean calculation
            threshold (float): Maximum allowed difference between consecutive means
        
        Returns:
            int: Time index where steady state is detected
        """
        if len(self.queue_length_history) < window * 2:
            return 0
            
        series = pd.Series(self.queue_length_history)
        rolling_mean = series.rolling(window=window).mean()
        rolling_std = series.rolling(window=window).std()
        
        # Check for stability in both mean and standard deviation
        stable_point = np.where(
            (rolling_mean.diff().abs() < threshold) & 
            (rolling_std.diff().abs() < threshold)
        )[0]
        
        return stable_point[0] if len(stable_point) > 0 else 0

    def record_queue_length(self, length):
        """Record queue length for warm-up detection"""
        self.queue_length_history.append(length)