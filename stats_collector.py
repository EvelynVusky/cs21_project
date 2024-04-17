import threading
from datetime import datetime

class StatsCollector:
    def __init__(self):
        self.events = []
        self.lock = threading.Lock()
    
    def log_event(self, event_type, details):
        with self.lock:
            event_info = {
                'timestagmp': datetime.now(),
                'event_type': event_type,
                'details': details
            }
            self.events.append(event_info)
            print(f"Logged: {event_type} at {event_info['timestamp']}: {details}")
    
    def get_stats(self):
        with self.lock:
            return self.events.copy()