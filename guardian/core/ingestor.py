import time
import openpyxl
import hashlib
import logging
from typing import Dict, Any
from .schema import DREManifest

logger = logging.getLogger("DREIngestor")

class ExcelIngestor:
    def __init__(self, manifest: DREManifest):
        self.manifest = manifest
        self.target_path = manifest.target_file

    def _get_formula_hash(self, formula: str) -> str:
        """Generates a fingerprint of the cell logic to detect hijacking."""
        if not formula or not str(formula).startswith('='):
            return "static_value"
        return hashlib.sha256(str(formula).encode()).hexdigest()

    def read_data(self, retries=5, delay=0.5) -> Dict[str, Any]:
        """
        Reads the target file with backoff logic to handle file locks.
        Fulfills FR5 (Resilience) and Edge Case A.
        """
        for i in range(retries):
            try:
                # PASS A: Get Values
                wb_data = openpyxl.load_workbook(
                    self.target_path, data_only=True, read_only=True
                )
                # PASS B: Get Formulas (for hijack detection)
                wb_logic = openpyxl.load_workbook(
                    self.target_path, data_only=False, read_only=True
                )
                
                results = {}
                sheet_data = wb_data.active
                sheet_logic = wb_logic.active

                for assertion in self.manifest.assertions:
                    cell_coord = assertion.binding.cell
                    
                    val = sheet_data[cell_coord].value
                    formula = sheet_logic[cell_coord].value
                    current_hash = self._get_formula_hash(formula)

                    results[assertion.id] = {
                        "value": val,
                        "formula_hash": current_hash,
                        "logical_name": assertion.logical_name
                    }
                
                return results

            except PermissionError:
                logger.warning(f"File locked by Excel. Retry {i+1}/{retries}...")
                time.sleep(delay * (2 ** i)) # Exponential backoff
            except Exception as e:
                raise RuntimeError(f"Ingestion Failure: {str(e)}")

        raise PermissionError("Could not bypass Excel lock after multiple attempts.")