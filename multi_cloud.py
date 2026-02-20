# multi_cloud.py
import os
import time
from datetime import datetime

class MultiCloudManager:
    def __init__(self):
        self.backends = [
            {
                "name": "render",
                "url": os.environ.get("RENDER_URL", "https://aurora-mulher-segura.onrender.com"),
                "healthy": True,
                "failures": 0,
                "active": True
            },
            {
                "name": "flyio", 
                "url": os.environ.get("FLYIO_URL", "https://aurora-backup.fly.dev"),
                "healthy": True,
                "failures": 0,
                "active": False
            }
        ]
        self.current_backend = 0
        self.stats = {
            "total_switches": 0,
            "total_requests": 0,
            "failed_requests": 0
        }
    
    def get_active_backend(self):
        return self.backends[self.current_backend]
    
    def get_active_url(self):
        self.stats["total_requests"] += 1
        return self.backends[self.current_backend]["url"]
    
    def report_failure(self, backend_name=None):
        self.stats["failed_requests"] += 1
    
    def get_status(self):
        return {
            "current": self.backends[self.current_backend]["name"],
            "backends": [
                {
                    "name": b["name"],
                    "healthy": b["healthy"],
                    "failures": b["failures"],
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