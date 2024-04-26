import threading
from global_stuff import *
from datetime import datetime, time

class StatsCollector:
    def __init__(self, n_rabbits, n_plants, n_foxes, rabbitSpeed, fearFactor, hungerFactor):
        self.events = []
        self.lock = threading.Lock()
        self.total_foxes_born = 0
        self.total_foxes_died = 0
        self.total_rabbits_born = 0
        self.total_rabbits_died = 0
        self.total_rabbits_eaten = 0
        self.total_rabbit_generations = 0
        self.initial_num_rabbit = n_rabbits
        self.initial_num_plants = n_plants
        self.initial_num_foxes = n_foxes
        self.total_rabbit_speed = n_rabbits * rabbitSpeed
        self.average_rabbit_speed = 0
        self.total_rabbit_fear = n_rabbits * fearFactor
        self.total_rabbit_hunger = n_rabbits * hungerFactor
        self.average_fox_speed = 0
        self.startTime = datetime.now().time()
                
    def log_event(self, event_type, details, creature):
        with self.lock:
            event_info = {
                'timestamp': datetime.now().time(),
                'event_type': event_type,
                'details': details
            }
            self.collect_stats(event_type, creature)
            self.events.append(event_info)
            # print(f"Logged: {event_type} at {event_info['timestamp']}: {details}")
    
    def collect_stats(self, event_type, creature):
        # generations = []
            if event_type == 'New fox born':
                self.total_foxes_born += 1
            elif event_type == 'New rabbit born':
                self.total_rabbits_born += 1
                rabbit_generation = creature.genes.generation
                if rabbit_generation > self.total_rabbit_generations:
                    self.total_rabbit_generations = rabbit_generation
                self.total_rabbit_speed += creature.size_step
                self.average_rabbit_speed = self.total_rabbit_speed / (self.initial_num_rabbit + self.total_rabbits_born)
            elif event_type == 'Fox passed away':
                self.total_foxes_died += 1
                self.average_fox_speed += creature.size_step
            elif event_type == 'Rabbit passed away':
                self.total_rabbits_died += 1
            elif event_type == 'Rabbit was eaten':
                self.total_rabbits_eaten += 1
    
    def time_difference_in_seconds(self, start_time, end_time):
        # Convert time objects to datetime objects for calculation
        start_datetime = datetime.combine(datetime.today(), start_time)
        end_datetime = datetime.combine(datetime.today(), end_time)

        # Calculate the difference
        time_difference = end_datetime - start_datetime

        # Extract the difference in seconds
        difference_seconds = time_difference.total_seconds()
        
        return difference_seconds

    def output_run_data(self):
        plant_pop = self.initial_num_plants
        rabbit_pop = self.initial_num_rabbit
        fox_pop =self.initial_num_foxes
        file_path = 'output.csv'
        with open(file_path, 'w') as file:
            for event in self.events:
                if event['event_type'] == 'New rabbit born':
                    rabbit_pop += 1
                elif event['event_type'] == 'Rabbit passed away':
                    rabbit_pop -= 1
                elif event['event_type'] == 'New plant born':
                    plant_pop += 1
                elif event['event_type'] == 'plant eaten':
                    plant_pop -= 1
                elif event['event_type'] == 'New fox born':
                    fox_pop += 1
                elif event['event_type'] == 'Fox passed away':
                    fox_pop -= 1
                file.write(str(self.time_difference_in_seconds(self.startTime, event['timestamp'])) + "," + str(plant_pop) + "," + str(rabbit_pop) + "," + str(fox_pop) + "\n")
        
    
    def print_stats(self):
        print("FINAL STATS FOR THIS SIMULATION: ")
        print("Total Foxes Born: ", self.total_foxes_born)
        print("Total Foxes Died: ", self.total_foxes_died)
        print("Total Rabbits Born: ", self.total_rabbits_born)
        print("Total Rabbits Eaten: ", self.total_rabbits_eaten)
        print("Total Rabbits Died of Natural Causes: ", self.total_rabbits_died - self.total_rabbits_eaten)
        print("Total Rabbit Deaths: ", self.total_rabbits_died)
        print("Average Rabbit speed: ", self.average_rabbit_speed)
        if (self.total_foxes_died > 0):
            avg_fox_speed = self.average_fox_speed / self.total_foxes_died
            print("Average Fox speed: ", avg_fox_speed)
        print("Total Rabbit Generations: ", self.total_rabbits_eaten, self.total_rabbit_generations)