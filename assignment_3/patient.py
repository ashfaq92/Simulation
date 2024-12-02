from dataclasses import dataclass

@dataclass
class Patient:
    """Patient with service times"""
    id: int
    arrival_time: float
    prep_time: float
    operation_time: float
    recovery_time: float