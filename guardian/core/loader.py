"""
Manifest Loader - Loads and validates the DRE contract (manifest.json)
"""
import json
from pathlib import Path
from typing import Dict, Any
from .schema import DREManifest
import logging

logger = logging.getLogger("DRE_Guardian.Loader")


class ManifestLoader:
    """Loads and parses the manifest.json contract file"""
    
    @staticmethod
    def load(filepath: str) -> DREManifest:
        """
        Load and parse the manifest.json file
        
        Args:
            filepath: Path to the manifest.json file
            
        Returns:
            DREManifest object with parsed contract data
        """
        try:
            path = Path(filepath)
            if not path.exists():
                raise FileNotFoundError(f"Manifest file not found: {filepath}")
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse into Pydantic model for validation
            manifest = DREManifest(**data)
            
            # Resolve target_file path relative to manifest location
            if not Path(manifest.target_file).is_absolute():
                manifest_dir = path.parent
                target_file = manifest_dir / manifest.target_file
                manifest.target_file = str(target_file.resolve())
            
            logger.info(f"Loaded manifest with {len(manifest.assertions)} assertions")
            return manifest
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in manifest: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load manifest: {e}")
            raise
