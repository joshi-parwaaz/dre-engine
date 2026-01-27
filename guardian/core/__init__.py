"""
DRE Core - The Brain of the Guardian System
"""
from .loader import ManifestLoader
from .ingestor import ExcelIngestor
from .brain import GateEngine
from .schema import DREManifest

__all__ = ['ManifestLoader', 'ExcelIngestor', 'GateEngine', 'DREManifest']
