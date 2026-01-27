from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Optional, Union

class PertDistribution(BaseModel):
    min: float
    mode: float
    max: float

    @field_validator('max')
    @classmethod
    def check_distribution(cls, v, info):
        # Enforcing the Principle of Uncertainty: Ranges must be logical
        values = info.data
        if 'min' in values and 'mode' in values:
            if not (values['min'] <= values['mode'] <= v):
                raise ValueError("Distribution violation: Must satisfy min <= mode <= max")
        return v

class DataBinding(BaseModel):
    cell: str
    named_range: Optional[str] = None
    formula_hash: Optional[str] = None

class Assertion(BaseModel):
    id: str = Field(..., description="Stable UUID for the assertion")
    logical_name: str
    binding: DataBinding
    owner_role: str # The Principle of Attribution
    last_updated: datetime # The Principle of Decay
    sla_days: int
    baseline_value: Optional[float] = None
    distribution: PertDistribution

class DREManifest(BaseModel):
    """Main DRE Contract - Governance rules and assertions"""
    project_id: str
    target_file: str
    stability_threshold: float = 0.15
    overlap_integral_cutoff: float = 0.05
    assertions: List[Assertion]

# Alias for backward compatibility
Manifest = DREManifest