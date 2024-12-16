from dataclasses import dataclass
from enum import Enum



class Severity(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'

@dataclass
class Patient:
    """Patient with service times and severity"""
    id: int
    arrival_time: float
    prep_time: float
    operation_time: float
    recovery_time: float
    severity: Severity = Severity.MEDIUM

    def adjust_service_times(self):
        """Adjust service times based on patient severity"""
        multipliers = {
            Severity.LOW: 0.8,
            Severity.MEDIUM: 1.0,
            Severity.HIGH: 1.3
        }
        multiplier = multipliers[self.severity]
        
        self.prep_time *= multiplier
        self.operation_time *= multiplier
        self.recovery_time *= multiplier


