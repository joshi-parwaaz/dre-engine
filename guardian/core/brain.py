"""
Gate Engine - The Brain of DRE Guardian
Implements the 4 Gate Analysis System
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from scipy.stats import beta
from scipy.integrate import quad
import numpy as np
from .schema import DREManifest, Assertion, PertDistribution

logger = logging.getLogger("DRE_Guardian.Brain")


class GateEngine:
    """
    The Brain: Implements 4-Gate Analysis
    - Gate 1: Freshness (Temporal Decay)
    - Gate 2: Stability (Distribution Overlap)
    - Gate 3: Collision (Conflict Detection)
    - Gate 4: Structure (Formula Hijack Detection)
    """
    
    def __init__(self, manifest: DREManifest):
        self.manifest = manifest
        self.stability_threshold = manifest.stability_threshold
        self.overlap_cutoff = manifest.overlap_integral_cutoff
    
    def get_human_narrative(self, gate_type: str, gate_result: Dict[str, Any], 
                           assertion_name: str = "Unknown") -> Dict[str, str]:
        """
        Translate technical gate results into human-friendly narratives.
        
        Args:
            gate_type: "gate_1", "gate_2", "gate_3", or "gate_4"
            gate_result: The raw gate result dictionary
            assertion_name: Logical name of the assertion
        
        Returns:
            Dict with 'title', 'message', and 'action' keys
        """
        status = gate_result.get("status", "UNKNOWN")
        
        if status == "PASS" or status == "SKIP":
            return {
                "title": "All Clear",
                "message": f"{assertion_name} is within acceptable parameters.",
                "action": "No action required."
            }
        
        # Gate 1: Freshness → Stale Anchor
        if gate_type == "gate_1":
            days = gate_result.get("days_since_update", 0)
            sla = gate_result.get("sla_days", 0)
            owner = gate_result.get("owner", "Unknown")
            
            return {
                "title": "⏰ Stale Data Alert",
                "message": f"{owner} has not updated '{assertion_name}' in {days} days (SLA: {sla} days).",
                "action": f"Request {owner} to refresh this data anchor immediately."
            }
        
        # Gate 2: Stability → Volatility Alert
        elif gate_type == "gate_2":
            current = gate_result.get("current_value", 0)
            dist = gate_result.get("distribution", {})
            pdf_ratio = gate_result.get("pdf_ratio_to_mode", 0)
            
            # Check if value is outside range
            if "reason" in gate_result and "outside" in gate_result["reason"].lower():
                return {
                    "title": "🚨 Critical Volatility",
                    "message": f"'{assertion_name}' shows value {current:.2f}, which falls completely outside the established range [{dist.get('min', 0):.2f} - {dist.get('max', 0):.2f}].",
                    "action": "Investigate source data immediately. This may indicate data corruption or fundamental business shift."
                }
            else:
                return {
                    "title": "📊 Volatility Alert",
                    "message": f"'{assertion_name}' current value ({current:.2f}) deviates significantly from baseline expectations (confidence: {pdf_ratio:.1%}).",
                    "action": "Review recent changes and validate whether this shift is intentional."
                }
        
        # Gate 3: Convergence → Logic Conflict
        elif gate_type == "gate_3":
            overlap = gate_result.get("overlap_integral", 0)
            a1 = gate_result.get("assertion1", {})
            a2 = gate_result.get("assertion2", {})
            owner1 = a1.get("owner", "Unknown")
            owner2 = a2.get("owner", "Unknown")
            name1 = a1.get("logical_name", "Unknown")
            name2 = a2.get("logical_name", "Unknown")
            severity = gate_result.get("severity", "MAJOR")
            
            if severity == "CRITICAL":
                return {
                    "title": "🔥 CRITICAL: Logic Conflict",
                    "message": f"Strategic consensus between {owner1} and {owner2} has completely collapsed (agreement: {overlap:.1%}).",
                    "action": f"Immediate reconciliation required between '{name1}' and '{name2}'. Escalate to decision authority."
                }
            else:
                return {
                    "title": "⚠️ Logic Conflict Detected",
                    "message": f"{owner1} and {owner2} have divergent views on reality (agreement: {overlap:.1%}).",
                    "action": f"Schedule alignment meeting to reconcile '{name1}' and '{name2}'."
                }
        
        # Gate 4: Structure → Integrity Alert
        elif gate_type == "gate_4":
            return {
                "title": "🔒 Formula Integrity Breach",
                "message": f"The calculation logic for '{assertion_name}' has been modified unexpectedly.",
                "action": "Review cell formula and audit trail. Verify change authorization."
            }
        
        # Fallback
        return {
            "title": "❓ Unknown Alert",
            "message": f"'{assertion_name}' triggered alert: {status}",
            "action": "Contact system administrator."
        }
    
    def _pert_to_beta(self, pert: PertDistribution) -> Tuple[float, float, float, float]:
        """
        Convert PERT distribution to Beta distribution parameters.
        
        Returns:
            (alpha, beta, loc, scale) for scipy.stats.beta
            loc = min, scale = max - min
        """
        # Handle edge case: zero range
        range_val = pert.max - pert.min
        if range_val == 0:
            # Degenerate distribution - all mass at a point
            # Return Beta(1,1) with zero scale (will be handled by caller)
            return 1.0, 1.0, pert.min, 0.0
        
        # PERT mean
        mean = (pert.min + 4 * pert.mode + pert.max) / 6
        
        # PERT variance (standard formula)
        variance = ((pert.max - pert.min) ** 2) / 36
        
        # Beta shape parameters using method of moments
        # For Beta on [0,1]: mean = α/(α+β), var = αβ/[(α+β)²(α+β+1)]
        # Map PERT to [0,1] then derive α,β
        
        mu = (mean - pert.min) / range_val  # Normalized mean
        
        # PERT approximation (modified Beta distribution)
        # Using the shape that gives PERT-like behavior
        alpha = 1 + 4 * (pert.mode - pert.min) / range_val
        beta_param = 1 + 4 * (pert.max - pert.mode) / range_val
        
        return alpha, beta_param, pert.min, range_val
    
    def _calculate_overlap(self, pert1: PertDistribution, pert2: PertDistribution) -> float:
        """
        Calculate overlap integral between two PERT distributions.
        
        Returns value in [0.0, 1.0]:
            1.0 = Perfect alignment (identical distributions)
            0.0 = Total conflict (no overlap)
        """
        # Convert both to Beta distributions
        alpha1, beta1, loc1, scale1 = self._pert_to_beta(pert1)
        alpha2, beta2, loc2, scale2 = self._pert_to_beta(pert2)
        
        # Handle degenerate cases
        if scale1 == 0 and scale2 == 0:
            # Both point masses - overlap if at same location
            return 1.0 if loc1 == loc2 else 0.0
        if scale1 == 0 or scale2 == 0:
            # One point mass, one distribution - minimal overlap
            return 0.01
        
        # Find common support range
        common_min = max(loc1, loc2)
        common_max = min(loc1 + scale1, loc2 + scale2)
        
        if common_min >= common_max:
            # No overlap in support
            return 0.0
        
        # Define integrand: min(pdf1(x), pdf2(x))
        def integrand(x):
            # PDF of Beta distribution: beta.pdf((x-loc)/scale) / scale
            pdf1 = beta.pdf((x - loc1) / scale1, alpha1, beta1) / scale1
            pdf2 = beta.pdf((x - loc2) / scale2, alpha2, beta2) / scale2
            return min(pdf1, pdf2)
        
        # Numerical integration
        try:
            overlap, error = quad(integrand, common_min, common_max, limit=100)
            # Clip to [0,1] to handle numerical errors
            overlap = np.clip(overlap, 0.0, 1.0)
            return float(overlap)
        except Exception as e:
            logger.warning(f"Overlap integral failed: {e}, returning 0.0")
            return 0.0
    
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
        Uses PDF probability density analysis - checks if current value
        falls within high-probability region of baseline PERT distribution.
        """
        if current_value is None:
            return {"status": "SKIP", "reason": "No current value"}
        
        dist = assertion.distribution
        
        # Convert PERT to Beta parameters
        alpha, beta_param, loc, scale = self._pert_to_beta(dist)
        
        if scale == 0:
            # Point mass distribution
            if abs(current_value - loc) < 1e-9:
                return {"status": "PASS", "reason": "Value matches point distribution"}
            else:
                return {
                    "status": "HALT",
                    "reason": "Value deviates from point distribution",
                    "current_value": current_value,
                    "expected_value": loc
                }
        
        # Normalize current value to [0,1]
        current_norm = (current_value - loc) / scale
        
        # Check if current value is outside distribution support
        if current_norm < 0 or current_norm > 1:
            return {
                "status": "HALT",
                "reason": "Value outside distribution range",
                "current_value": current_value,
                "distribution_range": [dist.min, dist.max],
                "pdf_probability": 0.0
            }
        
        # Calculate PDF at current value
        pdf_at_current = beta.pdf(current_norm, alpha, beta_param)
        
        # Calculate PDF at mode (peak probability)
        mode_norm = (dist.mode - loc) / scale
        pdf_at_mode = beta.pdf(mode_norm, alpha, beta_param)
        
        # Stability check: current PDF relative to peak PDF
        # If PDF drops below threshold × peak, value is in low-probability tail
        pdf_ratio = pdf_at_current / pdf_at_mode if pdf_at_mode > 0 else 0
        is_stable = pdf_ratio >= self.stability_threshold
        
        result = {
            "status": "PASS" if is_stable else "HALT",
            "current_value": current_value,
            "pdf_probability": float(pdf_at_current),
            "pdf_ratio_to_mode": float(pdf_ratio),
            "threshold": self.stability_threshold,
            "distribution": {"min": dist.min, "mode": dist.mode, "max": dist.max}
        }
        
        if not is_stable:
            logger.warning(
                f"Gate 2 HALT: {assertion.logical_name} - "
                f"PDF ratio {pdf_ratio:.2%} below threshold {self.stability_threshold:.2%} "
                f"(current={current_value}, mode={dist.mode})"
            )
        
        return result
    
    def gate_3_convergence(self, assertion1: Assertion, assertion2: Assertion) -> Dict[str, Any]:
        """
        Gate 3: Convergence Check
        Calculates overlap integral between two assertions' PERT distributions.
        HALT if overlap < overlap_integral_cutoff (conflict detected).
        
        Args:
            assertion1: First assertion in conflict pair
            assertion2: Second assertion in conflict pair
        
        Returns:
            Dict with status (PASS/HALT/CRITICAL), overlap_integral, and details
        """
        # Calculate overlap integral
        overlap = self._calculate_overlap(assertion1.distribution, assertion2.distribution)
        
        # Determine severity
        if overlap >= self.overlap_cutoff:
            status = "PASS"
            severity = "INFO"
        else:
            status = "HALT"
            # Critical if severe conflict (< 1% overlap)
            severity = "CRITICAL" if overlap < 0.01 else "MAJOR"
        
        result = {
            "status": status,
            "severity": severity,
            "overlap_integral": float(overlap),
            "threshold": self.overlap_cutoff,
            "assertion1": {
                "id": assertion1.id,
                "logical_name": assertion1.logical_name,
                "owner": assertion1.owner_role,
                "distribution": assertion1.distribution.dict()
            },
            "assertion2": {
                "id": assertion2.id,
                "logical_name": assertion2.logical_name,
                "owner": assertion2.owner_role,
                "distribution": assertion2.distribution.dict()
            }
        }
        
        if status == "HALT":
            logger.error(
                f"Gate 3 {severity} HALT: Conflict between {assertion1.logical_name} "
                f"and {assertion2.logical_name} - Overlap {overlap:.1%} below cutoff {self.overlap_cutoff:.1%}"
            )
        
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
