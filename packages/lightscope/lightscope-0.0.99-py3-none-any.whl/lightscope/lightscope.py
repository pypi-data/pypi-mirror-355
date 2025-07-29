#!/usr/bin/env python3
"""
LightScope Monitor
Ensures lightscope is installed, up-to-date, and running continuously.
"""
import sys
import time
import signal
import subprocess
import urllib.request
import json
import logging
import os
import threading
import psutil
import traceback
from importlib import metadata
from packaging.version import parse as parse_version
from datetime import datetime, timedelta

# --- Configuration ---
CHECK_INTERVAL = 15 * 60          # Check for updates every 15 minutes
HEALTH_CHECK_INTERVAL = 30        # Check process health every 30 seconds
RESTART_DELAY = 5                 # Wait 5 seconds before restarting
MAX_RESTART_ATTEMPTS = 5          # Max restarts within window
RESTART_WINDOW = 5 * 60           # 5-minute window for restarts
PYPI_JSON_URL = "https://pypi.org/pypi/lightscope/json"
LOG_FILE = os.path.expanduser("~/lightscope_monitor.log")

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# --- Handle shutdown signals ---
def _handle_exit(signum, frame):
    logger.info(f"Received signal {signum}, exiting monitor...")
    sys.exit(0)

signal.signal(signal.SIGINT, _handle_exit)
signal.signal(signal.SIGTERM, _handle_exit)

# --- Track restarts to avoid loops ---
class RestartTracker:
    def __init__(self):
        self.attempts = []
        self.max_attempts = MAX_RESTART_ATTEMPTS
        self.window = timedelta(seconds=RESTART_WINDOW)

    def can_restart(self):
        now = datetime.now()
        # purge old attempts
        self.attempts = [t for t in self.attempts if now - t < self.window]
        if len(self.attempts) >= self.max_attempts:
            logger.error(
                f"Too many restarts ({len(self.attempts)}) within {RESTART_WINDOW}s."
            )
            return False
        return True

    def record_restart(self):
        self.attempts.append(datetime.now())
        logger.info(
            f"Recorded restart (" 
            f"{len(self.attempts)}/{self.max_attempts} in window)."
        )

# --- Version checks ---
def get_installed_version():
    try:
        return metadata.version("lightscope")
    except metadata.PackageNotFoundError:
        logger.warning("lightscope not installed")
        return None
    except Exception as e:
        logger.error(f"Error getting installed version: {e}")
        return None


def get_latest_version():
    retries = 3
    for i in range(retries):
        try:
            with urllib.request.urlopen(PYPI_JSON_URL, timeout=30) as r:
                data = json.load(r)
            return data["info"]["version"]
        except Exception as e:
            logger.warning(f"Update check failed (attempt {i+1}): {e}")
            time.sleep(5 * (i+1))
    logger.error("Giving up checking PyPI after retries")
    return None

# --- Install or upgrade ---
def install_or_upgrade():
    retries = 3
    for i in range(retries):
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "lightscope"]
        logger.info(f"pip install (attempt {i+1}/{retries}): {' '.join(cmd)}")
        try:
            res = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300
            )
            if res.returncode == 0:
                logger.info("pip install succeeded")
                return True
            logger.error(f"pip install failed: {res.stderr.strip()}")
        except subprocess.TimeoutExpired:
            logger.error("pip install timed out")
        except Exception as e:
            logger.error(f"pip install error: {e}")
        time.sleep(10 * (i+1))
    return False

# --- Spawn or restart the application ---
def spawn_app():
    try:
        logger.info("Launching lightscope...")
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        proc = subprocess.Popen(
            [sys.executable, "-m", "lightscope"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env
        )
        logger.info(f"lightscope PID={proc.pid}")
        return proc
    except Exception as e:
        logger.error(f"Failed to launch lightscope: {e}")
        return None

# --- Health check ---
def is_process_healthy(proc):
    if proc is None:
        return False
    if proc.poll() is not None:
        logger.warning(f"Process {proc.pid} exited code={proc.returncode}")
        return False
    try:
        p = psutil.Process(proc.pid)
        if not p.is_running():
            return False
        # optional CPU check: p.cpu_percent()
        return True
    except psutil.NoSuchProcess:
        return False
    except Exception:
        return True

# --- Graceful shutdown ---
def graceful_shutdown(proc, timeout=30):
    if not proc:
        return
    pid = proc.pid
    logger.info(f"Stopping lightscope PID={pid}")
    try:
        proc.terminate()
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.warning("Terminate timed out; killing")
        proc.kill()
        proc.wait(timeout=10)
    except Exception as e:
        logger.error(f"Error stopping: {e}")

# --- Log application output ---
def output_reader(proc):
    try:
        for line in proc.stdout:
            logger.info("[lightscope] %s", line.strip())
    except Exception as e:
        logger.error(f"Output reader error: {e}")

# --- Main loop ---
def main():
    logger.info("=== LightScope Monitor Started ===")
    tracker = RestartTracker()

    # ensure install
    current = get_installed_version()
    if not current:
        if not install_or_upgrade():
            logger.critical("Initial install failed")
            sys.exit(1)
        current = get_installed_version() or current

    proc = None
    out_thr = None
    last_update = 0
    last_health = 0

    try:
        while True:
            now = time.time()

            # health
            if now - last_health >= HEALTH_CHECK_INTERVAL:
                if not is_process_healthy(proc):
                    logger.warning("Health check failed")
                    graceful_shutdown(proc)
                    if tracker.can_restart():
                        tracker.record_restart()
                        time.sleep(RESTART_DELAY)
                        proc = spawn_app()
                        if proc:
                            out_thr = threading.Thread(
                                target=output_reader, args=(proc,), daemon=True
                            )
                            out_thr.start()
                last_health = now

            # updates
            if now - last_update >= CHECK_INTERVAL:
                latest = get_latest_version()
                if latest and current and parse_version(latest) > parse_version(current):
                    logger.info(f"Upgrading: {current} -> {latest}")
                    graceful_shutdown(proc)
                    if install_or_upgrade():
                        current = get_installed_version() or current
                    proc = spawn_app()
                    if proc:
                        out_thr = threading.Thread(
                            target=output_reader, args=(proc,), daemon=True
                        )
                        out_thr.start()
                last_update = now

            # ensure running
            if not proc and tracker.can_restart():
                tracker.record_restart()
                proc = spawn_app()
                if proc:
                    out_thr = threading.Thread(
                        target=output_reader, args=(proc,), daemon=True
                    )
                    out_thr.start()

            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Interrupted, shutting down")
    except Exception:
        logger.error("Unexpected error", exc_info=True)
    finally:
        graceful_shutdown(proc, timeout=60)
        logger.info("Monitor exiting")

if __name__ == "__main__":
    main()
