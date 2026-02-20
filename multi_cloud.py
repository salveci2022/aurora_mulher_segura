# multi_cloud.py
import os
import requests
import threading
import time
from datetime import datetime

class MultiCloudManager:
    def __init__(self):
        self.backends = [
            {
                "name": "render",
                "url": os.environ.get("RENDER_URL", "https://aurora-mulher-segura.onrender.com"),
                "healthy": True,
                "last_check": None,
                "failures": 0,
                "response_time": 0,
                "active": True
            },
            {
                "name": "flyio", 
                "url": os.environ.get("FLYIO_URL", "https://aurora-backup.fly.dev"),
                "healthy": True,
                "last_check": None,
                "failures": 0,
                "response_time": 0,
                "active": False
            }
        ]
        self.current_backend = 0
        self.stats = {
            "total_switches": 0,
            "last_switch": None,
            "total_requests": 0,
            "failed_requests": 0
        }
        self.lock = threading.Lock()
    
    def get_active_backend(self):
        with self.lock:
            return self.backends[self.current_backend]
    
    def get_active_url(self):
        with self.lock:
            self.stats["total_requests"] += 1
            return self.backends[self.current_backend]["url"]
    
    def report_failure(self, backend_name=None):
        with self.lock:
            self.stats["failed_requests"] += 1
    
    def monitor_loop(self):
        while True:
            time.sleep(30)
    
    def get_status(self):
        with self.lock:
            return {
                "current": self.backends[self.current_backend]["name"],
                "backends": [
                    {
                        "name": b["name"],
                        "url": b["url"],
                        "healthy": b["healthy"],
                        "failures": b["failures"],
                        "response_time": b.get("response_time", "N/A"),
                        "last_check": b["last_check"].isoformat() if b["last_check"] else None,
                        "active": (i == self.current_backend)
                    }
                    for i, b in enumerate(self.backends)
                ],
                "stats": self.stats
            }

cloud_manager = MultiCloudManager()

def get_active_backend():
    return cloud_manager.get_active_backend()

def get_active_url():
    return cloud_manager.get_active_url()