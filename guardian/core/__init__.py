"""
DRE Core - The Brain of the Guardian System
"""
from .loader import ManifestLoader
from .ingestor import ExcelIngestor
from .brain import GateEngine
from .schema import DREManifest
from .config import Config, get_config, reset_config

__all__ = [
    'ManifestLoader', 
    'ExcelIngestor', 
    'GateEngine', 
    'DREManifest',
    'Config',
    'get_config',
    'reset_config'
]
