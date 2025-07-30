"""
Useful object definitions
"""

from dataclasses import dataclass


@dataclass
class ExperimentMeta:
    id: str
    scenario: str
