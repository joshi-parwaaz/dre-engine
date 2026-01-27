"""
Gate Engine - The Brain of DRE Guardian
Implements the 4 Gate Analysis System
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from scipy.stats import beta
import numpy as np
from .schema import DREManifest, Assertion, PertDistribution

logger = logging.getLogger("DRE_Guardian.Brain")


class GateEngine:
    """
    The Brain: Implements 4-Gate Analysis
    - Gate 1: Freshness (Temporal Decay)
    - Gate 2: Stability (Distribution Overlap)
    - Gate 3: Convergence (Rate of Change)
    - Gate 4: Structure (Formula Hijack Detection)
    """
    
    def __init__(self, manifest: DREManifest):
        self.manifest = manifest
        self.stability_threshold = manifest.stability_threshold
        self.overlap_cutoff = manifest.overlap_integral_cutoff
    
    def gate_1_freshness(self, assertion: Assertion) -> Dict[str, Any]:
        """
        Gate 1: Freshness Check
        Enforces the Principle of Decay - data must be updated within SLA
        """
        from datetime import timezone
        
        # Ensure both datetimes are timezone-aware
        now = datetime.now(timezone.utc)
        last_updated = assertion.last_updated
        if last_updated.tzinfo is None:
            # If naive, assume UTC
            last_updated = last_updated.replace(tzinfo=timezone.utc)
        
        days_since_update = (now - last_updated).days
        sla_breached = days_since_update > assertion.sla_days
        
        result = {
            "status": "HALT" if sla_breached else "PASS",
            "days_since_update": days_since_update,
            "sla_days": assertion.sla_days,
            "owner": assertion.owner_role
        }
        
        if sla_breached:
            logger.warning(
                f"Gate 1 HALT: {assertion.logical_name} - "
                f"{days_since_update} days old (SLA: {assertion.sla_days})"
            )
        
        return result
    
    def gate_2_stability(self, assertion: Assertion, current_value: float) -> Dict[str, Any]:
        """
        Gate 2: Stability Check
        Uses PERT distribution overlap to detect significant drift
        """
        if current_value is None or assertion.baseline_value is None:
            return {"status": "SKIP", "reason": "No baseline or current value"}
        
        # Convert PERT to Beta distribution parameters
        dist = assertion.distribution
        
        # PERT -> Beta conversion
        mean = (dist.min + 4 * dist.mode + dist.max) / 6
        range_val = dist.max - dist.min
        
        if range_val == 0:
            return {"status": "SKIP", "reason": "Invalid distribution (zero range)"}
        
        # Beta parameters (simplified PERT approximation)
        alpha = 1 + 4 * (dist.mode - dist.min) / range_val
        beta_param = 1 + 4 * (dist.max - dist.mode) / range_val
        
        # Normalize current and baseline to [0, 1] range
        baseline_norm = (assertion.baseline_value - dist.min) / range_val
        current_norm = (current_value - dist.min) / range_val
        
        # Clip to valid range
        baseline_norm = np.clip(baseline_norm, 0, 1)
        current_norm = np.clip(current_norm, 0, 1)
        
        # Calculate overlap integral (simplified)
        # In practice, you'd compute the actual distribution overlap
        drift = abs(current_norm - baseline_norm)
        
        # Simple stability check: if drift > threshold, HALT
        is_stable = drift <= self.stability_threshold
        
        result = {
            "status": "PASS" if is_stable else "HALT",
            "drift": float(drift),
            "threshold": self.stability_threshold,
            "current_value": current_value,
            "baseline_value": assertion.baseline_value
        }
        
        if not is_stable:
            logger.warning(
                f"Gate 2 HALT: {assertion.logical_name} - "
                f"Drift {drift:.2%} exceeds threshold {self.stability_threshold:.2%}"
            )
        
        return result
    
    def gate_3_convergence(self, assertion: Assertion, historical_values: list) -> Dict[str, Any]:
        """
        Gate 3: Convergence Check
        Monitors rate of change - rapid changes indicate instability
        (Placeholder for future implementation)
        """
        if len(historical_values) < 2:
            return {"status": "SKIP", "reason": "Insufficient historical data"}
        
        # Calculate rate of change
        rates = []
        for i in range(1, len(historical_values)):
            if historical_values[i-1] != 0:
                rate = abs((historical_values[i] - historical_values[i-1]) / historical_values[i-1])
                rates.append(rate)
        
        if not rates:
            return {"status": "PASS", "reason": "No significant changes"}
        
        avg_rate = np.mean(rates)
        max_acceptable_rate = 0.20  # 20% change threshold
        
        result = {
            "status": "PASS" if avg_rate <= max_acceptable_rate else "HALT",
            "avg_rate_of_change": float(avg_rate),
            "threshold": max_acceptable_rate
        }
        
        return result
    
    def gate_4_structure(self, stored_hash: str, current_hash: str) -> Dict[str, Any]:
        """
        Gate 4: Structural Integrity
        Detects formula hijacking - formula hash must match
        """
        # Handle None/missing hashes
        if stored_hash is None or current_hash is None:
            return {
                "status": "SKIP",
                "reason": "No formula hash available"
            }
        
        is_intact = stored_hash == current_hash
        
        result = {
            "status": "PASS" if is_intact else "HALT",
            "stored_hash": stored_hash[:16] + "...",
            "current_hash": current_hash[:16] + "..."
        }
        
        if not is_intact:
            logger.error("Gate 4 HALT: Formula hijack detected!")
        
        return result
