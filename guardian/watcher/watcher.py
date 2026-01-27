import time
import os
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Timer, Lock

# Configure logging for a background daemon
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [GUARDIAN] - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DREWatcher")

class DREWatcher(FileSystemEventHandler):
    def __init__(self, callback, target_file, debounce_seconds=0.9):
        self.callback = callback
        # Normalize to absolute path to prevent fragility
        self.target_file = os.path.abspath(target_file)
        self.debounce_seconds = debounce_seconds
        self._timer = None
        self._lock = Lock()  # Mutex to protect against overlapping callbacks

    def on_modified(self, event):
        # Ignore directory changes, temporary Excel files, and audit logs
        if event.is_directory or "~$" in event.src_path or "audit_log.jsonl" in event.src_path:
            return

        # Check if the modified file is our specific target
        event_path = os.path.abspath(event.src_path)
        if event_path == self.target_file:
            if self._timer:
                self._timer.cancel()
            
            # Reset debounce timer
            self._timer = Timer(self.debounce_seconds, self._safe_callback, [event_path])
            self._timer.start()

    def _safe_callback(self, filepath):
        """
        Executes the callback with a mutex lock and exception handling.
        This ensures the 'Gate Engine' doesn't crash the entire watcher.
        """
        if self._lock.locked():
            logger.warning(f"Processing in progress. Ignoring concurrent event for {filepath}")
            return

        with self._lock:
            try:
                if os.path.exists(filepath):
                    logger.info(f"File stable: {os.path.basename(filepath)}. Triggering check...")
                    self.callback(filepath)
                else:
                    logger.warning(f"File vanished before processing: {filepath}")
            except Exception as e:
                # This fulfills the 'no crash' maturity requirement
                logger.error(f"Logic failure in Gate Engine callback: {str(e)}")

def run_gate_logic(filepath):
    """
    Placeholder for Phase 3 logic.
    """
    print(f">>> GATE ENGINE: Analyzing {filepath}")

if __name__ == "__main__":
    # In Phase 3, these values will be pulled dynamically from manifest.json
    TARGET = "../../project_space/model.xlsx"
    WATCH_DIR = "../../project_space/"
    
    event_handler = DREWatcher(callback=run_gate_logic, target_file=TARGET)
    observer = Observer()
    observer.schedule(event_handler, os.path.abspath(WATCH_DIR), recursive=False)
    
    logger.info(f"DRE Engine Online. Monitoring: {os.path.abspath(TARGET)}")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Guardian shutting down...")
        observer.stop()
    observer.join()