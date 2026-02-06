"""
Production Configuration for DRE Guardian
Centralized path resolution for both script execution and PyInstaller .exe bundles
"""
import os
import sys
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger("DRE_Guardian.Config")


class Config:
    """
    Centralized configuration for DRE Guardian.
    Automatically detects whether running as script or .exe and resolves paths accordingly.
    """
    
    def __init__(self, manifest_path: Optional[str] = None):
        """
        Initialize configuration with automatic path detection.
        
        Args:
            manifest_path: Optional override for manifest.json location
        """
        # Detect if running as PyInstaller bundle
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running as compiled .exe
            self.is_frozen = True
            # _MEIPASS is the temp folder where PyInstaller extracts bundled files
            self.bundle_dir = Path(sys._MEIPASS)
            # The .exe location (user-accessible directory)
            self.app_dir = Path(sys.executable).parent
        else:
            # Running as Python script
            self.is_frozen = False
            # guardian/core/config.py -> guardian/
            self.bundle_dir = Path(__file__).resolve().parent.parent
            # guardian/ -> project root
            self.app_dir = self.bundle_dir.parent
        
        # User data directory (always external, never bundled)
        # This is where manifest.json, Excel files, and audit logs live
        # CRITICAL: Create this NEXT TO the executable, not in current working directory
        # This ensures portability - user can run from Desktop, Downloads, anywhere
        self.project_space = self.app_dir / "project_space"
        
        # Template directory (for dre init command)
        # In frozen mode, this is the bundled template in _MEIPASS
        # In script mode, this is the project_space/ directory itself
        if self.is_frozen:
            self.template_dir = self.bundle_dir / "project_space_template"
        else:
            self.template_dir = self.project_space
        
        # Dashboard directory (contains React build)
        # In frozen mode, dashboard is bundled in _MEIPASS
        # In script mode, dashboard is in project root
        if self.is_frozen:
            self.dashboard_dir = self.bundle_dir / "dashboard"
        else:
            self.dashboard_dir = self.app_dir / "dashboard"
        
        # Logs directory (created at runtime)
        self.logs_dir = self.project_space / "logs"
        
        # Archives directory (for compressed audit logs)
        self.archives_dir = self.project_space / "archives"
        
        # Manifest path (user-editable)
        if manifest_path:
            self.manifest_path = Path(manifest_path)
        else:
            self.manifest_path = self.project_space / "manifest.json"
        
        # Audit log (append-only ledger)
        self.audit_log_path = self.project_space / "audit_log.jsonl"
        
        # Main log file for DRE Guardian
        self.log_file = self.logs_dir / "dre.log"
        
        # Note: Directories created on-demand, not at startup
        # This prevents surprise filesystem side effects before init
    
    def ensure_project_space(self):
        """Create project_space directory if it doesn't exist
        
        Raises:
            OSError: If directory cannot be created due to permissions or other issues
        """
        try:
            self.project_space.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured project_space exists: {self.project_space}")
        except Exception as e:
            logger.error(f"Failed to create project_space at {self.project_space}: {e}")
            raise OSError(f"Cannot create project directory at {self.project_space}. "
                         f"Check permissions or choose a different location.") from e
    
    def ensure_logs_dir(self):
        """Create logs directory if it doesn't exist"""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def get_excel_path(self, filename: Optional[str] = None) -> Optional[Path]:
        """
        Resolve Excel file path from manifest or explicit filename.
        
        Args:
            filename: Optional Excel filename to search for
            
        Returns:
            Path to Excel file or None if not found
        """
        if filename:
            excel_path = self.project_space / filename
            return excel_path if excel_path.exists() else None
        
        # Try to read from manifest
        if self.manifest_path.exists():
            try:
                import json
                with open(self.manifest_path, 'r', encoding='utf-8') as f:
                    manifest_data = json.load(f)
                    target_file = manifest_data.get('target_file')
                    if target_file:
                        # Resolve relative to project_space
                        excel_path = self.project_space / Path(target_file).name
                        return excel_path if excel_path.exists() else None
            except Exception as e:
                logger.warning(f"Could not parse manifest for Excel path: {e}")
        
        return None
    
    def setup_logging(self, level: str = "INFO"):
        """
        Configure logging for production deployment.
        Logs to both file and console (console only if not frozen).
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        # Ensure logs directory exists
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler (always active)
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
        
        # Console handler (only if running as script, not .exe)
        if not self.is_frozen:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_formatter = logging.Formatter(
                '%(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        logger.info(f"DRE Guardian initialized in {'frozen' if self.is_frozen else 'script'} mode")
        logger.info(f"App directory: {self.app_dir}")
        logger.info(f"Project space: {self.project_space}")
    
    def validate_environment(self) -> dict:
        """
        Validate that all critical files and directories exist.
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            'project_space_exists': self.project_space.exists(),
            'logs_dir_exists': self.logs_dir.exists(),
            'manifest_exists': self.manifest_path.exists(),
            'audit_log_exists': self.audit_log_path.exists(),
            'dashboard_exists': self.dashboard_dir.exists(),
            'excel_file': self.get_excel_path() is not None
        }
        
        # Log warnings for missing components
        if not validation['manifest_exists']:
            logger.warning(f"Manifest not found at {self.manifest_path}")
        if not validation['excel_file']:
            logger.warning("Excel target file not found in project_space")
        if not validation['dashboard_exists']:
            logger.warning(f"Dashboard directory not found at {self.dashboard_dir}")
        
        return validation
    
    def create_default_manifest(self) -> bool:
        """
        Create a default manifest.json template if it doesn't exist.
        
        Returns:
            True if created successfully, False otherwise
        """
        if self.manifest_path.exists():
            logger.info("Manifest already exists, skipping creation")
            return False
        
        try:
            default_manifest = {
                "target_file": "Strategic-Model.xlsx",
                "project_name": "DRE Guardian Project",
                "assertions": [
                    {
                        "id": "ast-001",
                        "logical_name": "revenue_forecast",
                        "owner_role": "VP of Sales",
                        "sla_days": 7,
                        "distribution": {
                            "min": 800,
                            "mode": 1000,
                            "max": 1200
                        },
                        "binding": {
                            "cell": "B5"
                        }
                    }
                ]
            }
            
            import json
            with open(self.manifest_path, 'w', encoding='utf-8') as f:
                json.dump(default_manifest, f, indent=2)
            
            logger.info(f"Created default manifest at {self.manifest_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create default manifest: {e}")
            return False
    
    def copy_template_to(self, destination: Path) -> bool:
        """
        Copy the project_space template to a new location.
        Used by the 'dre init' command to scaffold new projects.
        
        Args:
            destination: Target directory path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import shutil
            
            destination = Path(destination)
            if destination.exists():
                logger.warning(f"Destination already exists: {destination}")
                return False
            
            # Create destination directory
            destination.mkdir(parents=True, exist_ok=True)
            
            # Copy template files (manifest.json, model.xlsx, README.md)
            template_files = ['manifest.json', 'model.xlsx', 'README.md']
            for filename in template_files:
                src = self.template_dir / filename
                dst = destination / filename
                if src.exists():
                    shutil.copy2(src, dst)
                    logger.info(f"Copied template file: {filename}")
                else:
                    logger.warning(f"Template file not found: {filename}")
            
            # Create subdirectories with .gitkeep
            subdirs = ['logs', 'archives']
            for subdir in subdirs:
                subdir_path = destination / subdir
                subdir_path.mkdir(parents=True, exist_ok=True)
                
                # Copy .gitkeep if it exists in template
                gitkeep_src = self.template_dir / subdir / '.gitkeep'
                if gitkeep_src.exists():
                    gitkeep_dst = subdir_path / '.gitkeep'
                    shutil.copy2(gitkeep_src, gitkeep_dst)
            
            logger.info(f"Successfully initialized project at {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy template: {e}", exc_info=True)
            return False
    
    def __repr__(self) -> str:
        return (
            f"Config(frozen={self.is_frozen}, "
            f"app_dir={self.app_dir}, "
            f"manifest={self.manifest_path})"
        )


# Global config instance (singleton pattern)
_config_instance: Optional[Config] = None


def get_config(manifest_path: Optional[str] = None) -> Config:
    """
    Get or create the global configuration instance.
    
    Args:
        manifest_path: Optional override for manifest location.
                      If provided and different from existing config, will reinitialize.
        
    Returns:
        Config instance
    """
    global _config_instance
    
    # If manifest_path is provided and config exists, check if we need to reinitialize
    if manifest_path is not None and _config_instance is not None:
        # Convert both to Path for comparison
        from pathlib import Path
        new_manifest = Path(manifest_path).resolve()
        existing_manifest = _config_instance.manifest_path.resolve()
        
        # Reinitialize if manifest path changed
        if new_manifest != existing_manifest:
            logger.info(f"Reinitializing config with new manifest path: {manifest_path}")
            _config_instance = Config(manifest_path)
    elif _config_instance is None:
        # First time initialization
        _config_instance = Config(manifest_path)
    
    return _config_instance


def reset_config():
    """Reset the global config instance (mainly for testing)"""
    global _config_instance
    _config_instance = None
