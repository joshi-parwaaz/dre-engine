"""
DRE Guardian - Startup Script
Runs both the API Bridge and the Watcher
"""
import logging
import asyncio
from api.bridge import app
import uvicorn
from threading import Thread

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
)

logger = logging.getLogger("DRE_Startup")

def run_api():
    """Run FastAPI server in separate thread"""
    logger.info("Starting API Bridge on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

def run_watcher():
    """Run file watcher for Excel monitoring"""
    from watcher.watcher import DREWatcher
    from main import run_governance_cycle
    import time
    from watchdog.observers import Observer
    
    logger.info("Starting File Watcher...")
    
    # TODO: Configure target file from manifest
    target_file = "../project_space/your_model.xlsx"
    
    watcher = DREWatcher(
        callback=run_governance_cycle,
        target_file=target_file,
        debounce_seconds=0.9
    )
    
    observer = Observer()
    observer.schedule(watcher, path="../project_space", recursive=False)
    observer.start()
    
    logger.info(f"Watching: {target_file}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("DRE GUARDIAN - Data Reliability Engine")
    logger.info("=" * 60)
    logger.info("Architecture: Sidecar")
    logger.info("Components: Brain + Watcher + Bridge + Dashboard")
    logger.info("=" * 60)
    
    # Start API in background thread
    api_thread = Thread(target=run_api, daemon=True)
    api_thread.start()
    
    # Give API time to start
    import time
    time.sleep(2)
    
    logger.info("API Bridge: ✓ Running")
    logger.info("Dashboard: Start with 'npm run dev' in dashboard/")
    logger.info("=" * 60)
    
    # Run watcher in main thread
    try:
        run_watcher()
    except KeyboardInterrupt:
        logger.info("\nShutting down Guardian...")
