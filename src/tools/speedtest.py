#!/usr/bin/env python3

import subprocess
import re
import json
import shutil
import threading
from typing import Dict, Any, Optional, Callable, List
from utils.logger import LogLevel, Logger

class SpeedtestResult:
    """Class to hold speedtest results"""
    def __init__(self):
        self.download: float = 0.0  # Mbps
        self.upload: float = 0.0    # Mbps
        self.ping: float = 0.0      # ms
        self.jitter: float = 0.0    # ms
        self.isp: str = ""
        self.server_name: str = ""
        self.server_location: str = ""
        self.timestamp: str = ""
        self.error: Optional[str] = None
        self.progress: int = 0      # 0-100%

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "download": self.download,
            "upload": self.upload,
            "ping": self.ping,
            "jitter": self.jitter,
            "isp": self.isp,
            "server_name": self.server_name,
            "server_location": self.server_location,
            "timestamp": self.timestamp,
            "error": self.error,
            "progress": self.progress
        }

class SpeedtestRunner:
    """Class to run speedtest"""
    def __init__(self, logging: Logger):
        self.logging = logging
        self.current_test: Optional[subprocess.Popen] = None
        self.is_running: bool = False
        self.latest_result = SpeedtestResult()
        self._callbacks: List[Callable[[SpeedtestResult], None]] = []
        self._progress_callbacks: List[Callable[[int, str], None]] = []

    def speedtest_available(self) -> bool:
        """Check if speedtest-cli is available"""
        return shutil.which("speedtest") is not None

    def register_callback(self, callback: Callable[[SpeedtestResult], None]) -> None:
        """Register callback for test completion"""
        self._callbacks.append(callback)

    def register_progress_callback(self, callback: Callable[[int, str], None]) -> None:
        """Register callback for test progress"""
        self._progress_callbacks.append(callback)

    def _notify_callbacks(self, result: SpeedtestResult) -> None:
        """Notify all callbacks with result"""
        for callback in self._callbacks:
            try:
                callback(result)
            except Exception as e:
                self.logging.log(LogLevel.Error, f"Error in speedtest callback: {e}")

    def _notify_progress(self, progress: int, stage: str) -> None:
        """Notify all progress callbacks"""
        for callback in self._progress_callbacks:
            try:
                callback(progress, stage)
            except Exception as e:
                self.logging.log(LogLevel.Error, f"Error in speedtest progress callback: {e}")

    def cancel_test(self) -> None:
        """Cancel an ongoing test"""
        if self.current_test and self.is_running:
            try:
                self.current_test.terminate()
                self.current_test.wait(timeout=2)
                if self.current_test.poll() is None:
                    self.current_test.kill()
                self.is_running = False
                result = SpeedtestResult()
                result.error = "Test cancelled"
                self._notify_callbacks(result)
                self.logging.log(LogLevel.Info, "Speedtest cancelled")
            except Exception as e:
                self.logging.log(LogLevel.Error, f"Error cancelling speedtest: {e}")

    def run_test(self, server_id: Optional[str] = None) -> None:
        """Start a speedtest in a background thread"""
        if self.is_running:
            self.logging.log(LogLevel.Warn, "Speedtest already in progress")
            return

        def run_test_thread():
            try:
                self.is_running = True
                result = SpeedtestResult()

                # Initial progress notification
                self._notify_progress(0, "Starting speedtest...")

                # Build command
                # Use --json instead of --format=json for broader compatibility
                cmd = ["speedtest", "--json"]
                if server_id:
                    cmd.append(f"--server-id={server_id}")

                # Start process
                self.logging.log(LogLevel.Info, f"Starting speedtest with command: {' '.join(cmd)}")
                self.current_test = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )

                # Poll for output
                stdout_lines = []
                progress_pattern = re.compile(r"Testing (\w+)(?: speed)?: (\d+)%")
                
                # Track progress stages
                last_stage = ""
                
                while True:
                    # Check stderr for progress updates
                    if self.current_test.stderr:
                        line = self.current_test.stderr.readline()
                        if line:
                            match = progress_pattern.search(line)
                            if match:
                                stage = match.group(1).lower()
                                progress = int(match.group(2))
                                
                                # Map stage to overall progress
                                # We split progress: 10% initial, 45% download, 45% upload
                                if stage == "download":
                                    overall_progress = 10 + int(progress * 0.45)
                                    stage_desc = "Testing download speed"
                                elif stage == "upload":
                                    overall_progress = 55 + int(progress * 0.45)
                                    stage_desc = "Testing upload speed"
                                else:
                                    overall_progress = 5
                                    stage_desc = "Selecting server"
                                
                                if stage != last_stage or progress % 10 == 0:
                                    self._notify_progress(overall_progress, stage_desc)
                                    last_stage = stage
                                    
                            self.logging.log(LogLevel.Debug, f"Speedtest stderr: {line.strip()}")
                    
                    # Check for available stdout
                    if self.current_test.stdout:
                        line = self.current_test.stdout.readline()
                        if not line:
                            break
                        stdout_lines.append(line)
                
                # Wait for process to complete with timeout
                try:
                    # allow more time for slower connections
                    self.current_test.wait(timeout=120)
                except subprocess.TimeoutExpired:
                    self.logging.log(LogLevel.Error, "Speedtest timed out after 120 seconds")
                    self.current_test.kill()
                    result.error = "Speedtest timed out"
                    self._notify_callbacks(result)
                    self.is_running = False
                    self.current_test = None
                    return

                # Get remaining output
                if self.current_test.stdout:
                    stdout_lines.extend(self.current_test.stdout.readlines())

                # Handle result or error
                if self.current_test.returncode == 0 and stdout_lines:
                    try:
                        # Try to parse the JSON output
                        json_output = "".join(stdout_lines)
                        data = json.loads(json_output)

                        if not isinstance(data, dict):
                            raise ValueError(f"Unexpected JSON output: {data}")

                        # Parse download/upload unchanged...
                        result.download = float(data.get("download", 0)) * 8 / 1000000
                        result.upload = float(data.get("upload", 0)) * 8 / 1000000

                        # parse ping and jitter (ping may be float or dict)
                        ping_val = data.get("ping", 0)
                        if isinstance(ping_val, dict):
                            result.ping = float(ping_val.get("latency", 0))
                            result.jitter = float(ping_val.get("jitter", 0))
                        else:
                            result.ping = float(ping_val)
                            result.jitter = 0.0

                        result.isp = data.get("isp", "")
                        result.server_name = data.get("server", {}).get("name", "")
                        result.server_location = data.get("server", {}).get("location", "")
                        result.timestamp = data.get("timestamp", "")
                        result.progress = 100
                        
                        self.logging.log(LogLevel.Info, f"Speedtest completed: {result.download:.2f}Mbps down, {result.upload:.2f}Mbps up, {result.ping:.2f}ms ping")
                    except Exception as e:
                        self.logging.log(LogLevel.Error, f"Error parsing speedtest results: {e}")
                        result.error = f"Error parsing results: {e}"
                else:
                    stderr = ""
                    if self.current_test.stderr:
                        stderr = self.current_test.stderr.read()
                    
                    self.logging.log(LogLevel.Error, f"Speedtest failed with code {self.current_test.returncode}: {stderr}")
                    result.error = f"Test failed: {stderr}"
                
                # Notify progress completion
                self._notify_progress(100, "Test completed")
                
                # Save and notify result
                self.latest_result = result
                self._notify_callbacks(result)
            
            except Exception as e:
                self.logging.log(LogLevel.Error, f"Error running speedtest: {e}")
                result = SpeedtestResult()
                result.error = str(e)
                self._notify_callbacks(result)
            
            finally:
                self.is_running = False
                self.current_test = None

        # Start the test thread
        threading.Thread(target=run_test_thread, daemon=True).start()

    def get_server_list(self) -> List[Dict[str, Any]]:
        """Get list of speedtest servers"""
        servers = []
        try:
            result = subprocess.run(
                ["speedtest", "--servers", "--format=json"],
                capture_output=True,
                text=True,
                check=True
            )
            data = json.loads(result.stdout)
            servers = data.get("servers", [])
            self.logging.log(LogLevel.Info, f"Got {len(servers)} speedtest servers")
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Error getting speedtest servers: {e}")
        
        return servers

def install_speedtest_cli(logging: Logger) -> bool:
    """Try to install speedtest-cli"""
    try:
        logging.log(LogLevel.Info, "Attempting to install speedtest-cli...")
        
        # Try with pip first
        try:
            subprocess.run(
                ["pip", "install", "speedtest-cli"],
                check=True,
                capture_output=True
            )
            logging.log(LogLevel.Info, "Installed speedtest-cli with pip")
            return True
        except subprocess.CalledProcessError:
            logging.log(LogLevel.Warn, "Failed to install with pip, trying package managers...")
        
        # Check distribution and use appropriate package manager
        os_release = {}
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        os_release[key] = value.strip('"')
        except:
            pass
        
        os_id = os_release.get("ID", "").lower()
        
        # Try package managers based on distro
        if os_id in ["ubuntu", "debian", "pop", "mint"]:
            subprocess.run(
                ["apt", "update"],
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["apt", "install", "-y", "speedtest-cli"],
                check=True,
                capture_output=True
            )
            logging.log(LogLevel.Info, "Installed speedtest-cli with apt")
            return True
        elif os_id in ["fedora", "rhel", "centos"]:
            subprocess.run(
                ["dnf", "install", "-y", "speedtest-cli"],
                check=True,
                capture_output=True
            )
            logging.log(LogLevel.Info, "Installed speedtest-cli with dnf")
            return True
        elif os_id in ["arch", "manjaro"]:
            subprocess.run(
                ["pacman", "-Sy", "--noconfirm", "speedtest-cli"],
                check=True,
                capture_output=True
            )
            logging.log(LogLevel.Info, "Installed speedtest-cli with pacman")
            return True
        else:
            logging.log(LogLevel.Error, f"Unsupported distribution: {os_id}")
            return False
            
    except Exception as e:
        logging.log(LogLevel.Error, f"Failed to install speedtest-cli: {e}")
        return False