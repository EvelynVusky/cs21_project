import threading
from datetime import datetime

class StatsCollector:
    def __init__(self):
        self.events = []
        self.lock = threading.Lock()
        self.total_foxes_born = 0
        self.total_foxes_died = 0
        self.total_rabbits_born = 0
        self.total_rabbits_died = 0
        self.total_rabbits_eaten = 0
        self.total_rabbit_generations = 0
        self.average_rabbit_speed = 0
        self.average_fox_speed = 0
                
    def log_event(self, event_type, details, creature):
        with self.lock:
            event_info = {
                'timestamp': datetime.now().time(),
                'event_type': event_type,
                'details': details
            }
            self.collect_stats(event_type, creature)
            self.events.append(event_info)
            print(f"Logged: {event_type} at {event_info['timestamp']}: {details}")
    
    def collect_stats(self, event_type, creature):
        # generations = []
            if event_type == 'New fox born':
                self.total_foxes_born += 1
            elif event_type == 'New rabbit born':
                self.total_rabbits_born += 1
            elif event_type == 'Fox passed away':
                self.total_foxes_died += 1
                self.average_fox_speed += creature.size_step
            elif event_type == 'Rabbit passed away':
                self.total_rabbits_died += 1
                self.average_rabbit_speed += creature.size_step
            elif event_type == 'Rabbit was eaten':
                self.total_rabbits_eaten += 1
                self.average_rabbit_speed += creature.size_step
    
    def print_stats(self):
        print("FINAL STATS FOR THIS SIMULATION: ")
        print("Total Foxes Born: ", self.total_foxes_born)
        print("Total Foxes Died: ", self.total_foxes_died)
        print("Total Rabbits Born: ", self.total_rabbits_born)
        print("Total Rabbits Eaten: ", self.total_rabbits_eaten)
        print("Total Rabbits Died of Natural Causes: ", self.total_rabbits_died)
        avg_rabbit_speed = self.average_rabbit_speed / (self.total_rabbits_eaten + self.total_rabbits_died)
        print("Average Rabbit speed: ", avg_rabbit_speed)
        avg_fox_speed = self.average_fox_speed / self.total_foxes_died
        print("Average Fox speed: ", avg_fox_speed)