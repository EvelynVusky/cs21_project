import tkinter as tk
import threading
from time import sleep
import random
import math
from global_stuff import *
from creature import *

class Fox(Creature, threading.Thread):
    def __init__(self, initial_pos, health): 
        Creature.__init__(self, initial_pos)
        threading.Thread.__init__(self)
        self.size_step = foxSpeed
        self.health = health
        self.canvas_object = canvas.create_oval(initial_pos[0]-10,
                                                        initial_pos[1]-10,
                                                        initial_pos[0]+10,
                                                        initial_pos[1]+10, 
                                                        fill="red")   

    # gets the closest edible creature
    def findClosestFood(self):
        return self.findClosest(rabbits, rabbit_lock)

    def findClosestPredator(self):
        return self.findClosest(foxes, fox_lock)

    def moveForSurvival(self):
        food = self.findClosestFood()
        predator = self.findClosestPredator()

        if not predator and not food:
            return self.position[0], self.position[1], 0, 0, None
        
        distance_to_food = float('inf') if food is None else self.getDistanceTo(food)
        distance_to_predator = float('inf') if predator is None else self.getDistanceTo(predator)

        if (distance_to_food * avoidOthers) < (distance_to_predator * (1 - avoidOthers)):
            dx = food.position[0] - self.position[0]
            dy = food.position[1] - self.position[1]
            
        elif predator:
            dx = self.position[0] - predator.position[0]
            dy = self.position[1] - predator.position[1]

        distance = math.sqrt(dx**2 + dy**2)
        if distance > self.size_step:
            dx = (dx / distance) * self.size_step
            dy = (dy / distance) * self.size_step
            # print(dx, dy)

        return self.position[0] + dx, self.position[1] + dy, dx, dy, food

    # find the closest food item and moves towards it
    def movetowardsClosestFood(self):
        food = self.findClosestFood()
        if (not food):
            return self.position[0], self.position[1], 0, 0, None

        dx = food.position[0] - self.position[0]
        dy = food.position[1] - self.position[1]

        if self.getDistanceTo(food) > self.size_step:
            dx = (dx / self.getDistanceTo(food) * self.size_step)
            dy = (dy / self.getDistanceTo(food) * self.size_step)
            # print(dx, dy)

        return self.position[0] + dx, self.position[1] + dy, dx, dy, food

    def reproduce(self):
        if len(foxes) < maxFoxes:
            x, y = self.genNewPosition(minFoxDistance, maxFoxDistance, foxes, fox_lock)
            if (x and y):
                # print("new fox")
                newFox = Fox([x, y], health)
                with fox_lock:
                    foxes.append(newFox)
                newFox.start()

    def run(self): 
        while self.health > 0:
            new_col, new_row, dx, dy, food = self.moveForSurvival()
            if (not food):
                new_col, new_row, dx, dy = self.generate_position()
                while(not check_bounds(new_col, new_row)):
                    new_col, new_row, dx, dy = (self.generate_position()) 

                self.position[0], self.position[1] = new_col, new_row
                with canvas_lock:
                    canvas.moveto(self.canvas_object, int(self.position[0] + dx) - 10, int(self.position[1] + dy) - 10)
            else:
                self.position[0], self.position[1] = new_col, new_row
                if (self.getDistanceTo(food) < 1 and food.getEaten()):
                    self.health = max(self.health + foxMetabolism, foxStomachSize)
                with canvas_lock:
                    canvas.moveto(self.canvas_object, int(self.position[0] + dx) - 10, int(self.position[1] + dy) - 10)

            # do reproduction
            if self.health > 10 and random.random() < foxRate:
                self.reproduce()

            self.health -= 1
            # print(self.health)
            self.waitForOtherThreads(plants, plant_lock, rabbits, rabbit_lock, foxes, fox_lock)
            # Some kind of barrier here to prevent rabbits from taking more
            # than one "turn" before other rabbits due to thread sleep
            # print("rabbit moved")
        with fox_lock:
                foxes.remove(self)
        with canvas_lock:
            canvas.delete(self.canvas_object)
        # print("fox is done")


class Rabbit(Creature, threading.Thread):    
    def __init__(self, initial_pos, health): 
        Creature.__init__(self, initial_pos)
        threading.Thread.__init__(self)
        self.size_step = rabbitSpeed
        self.health = health
        self.canvas_object = canvas.create_oval(initial_pos[0]-7,
                                                        initial_pos[1]-7,
                                                        initial_pos[0]+7,
                                                        initial_pos[1]+7, 
                                                        fill="blue")

    # we should make this detect if there is no food on the map
    def findClosestFood(self):
        return self.findClosest(plants, plant_lock)
    
    def findClosestPredator(self):
        return self.findClosest(foxes, fox_lock)

    # find the closest food item and moves towards it, move away from predators
    def moveForSurvival(self):
        food = self.findClosestFood()
        predator = self.findClosestPredator()

        if not predator and not food:
            return self.position[0], self.position[1], 0, 0, None
        
        distance_to_food = float('inf') if food is None else self.getDistanceTo(food)
        distance_to_predator = float('inf') if predator is None else self.getDistanceTo(predator)

        if (distance_to_food * fearFactor) < (distance_to_predator * (1 - fearFactor)):
            dx = food.position[0] - self.position[0]
            dy = food.position[1] - self.position[1]
            
        elif predator:
            dx = self.position[0] - predator.position[0]
            dy = self.position[1] - predator.position[1]

        distance = math.sqrt(dx**2 + dy**2)
        if distance > self.size_step:
            dx = (dx / distance) * self.size_step
            dy = (dy / distance) * self.size_step
            # print(dx, dy)

        return self.position[0] + dx, self.position[1] + dy, dx, dy, food

    def getEaten(self):
        with rabbit_lock:
            if self in rabbits:
                rabbits.remove(self)
                with canvas_lock:
                    canvas.delete(self.canvas_object)
                return True
            else:
                return False

    def reproduce(self):
        if len(rabbits) < maxRabbits:
            print("rabbiting")
            x, y = self.genNewPosition(minRabbitDistance, maxRabbitDistance, rabbits, rabbit_lock)
            if (x and y):
                # print("new rabbit")
                newRabbit = Rabbit([x, y], health)
                with rabbit_lock:
                    rabbits.append(newRabbit)
                newRabbit.start()

    def run(self): 
        while self.health > 0 and self in rabbits:
            new_col, new_row, dx, dy, food = self.moveForSurvival()
            if (not food):
                new_col, new_row, dx, dy = self.generate_position()
                while(not check_bounds(new_col, new_row)):
                    new_col, new_row, dx, dy = (self.generate_position()) 

                self.position[0], self.position[1] = new_col, new_row
                with canvas_lock:
                    canvas.moveto(self.canvas_object, int(self.position[0] + dx) - 7, int(self.position[1] + dy) - 7)
            else:
                self.position[0], self.position[1] = new_col, new_row
                if ((self.getDistanceTo(food) < 1) and food.getEaten()):
                    self.health = max(self.health + rabbitMetabolism, rabbitStomachSize)
                with canvas_lock:
                    canvas.moveto(self.canvas_object, int(self.position[0] + dx) - 7, int(self.position[1] + dy) - 7)

            # do reproduction
            if self.health > 10 and random.random() < rabbitRate:
                self.reproduce()

            self.health -= 1
            # print(self.health)
            self.waitForOtherThreads(plants, plant_lock, rabbits, rabbit_lock, foxes, fox_lock)
            # Some kind of barrier here to prevent rabbits from taking more
            # than one "turn" before other rabbits due to thread sleep
            # print("rabbit moved")
        with rabbit_lock:
            if self in rabbits:
                rabbits.remove(self)
        with canvas_lock:
            canvas.delete(self.canvas_object)
        # print("rabbit is done")


#PLANTS
class Plant(Creature, threading.Thread):
    def __init__(self, initial_pos, health, reproduceRate): 
        Creature.__init__(self, initial_pos)
        threading.Thread.__init__(self)
        self.foodValue = health
        self.reproduceRate = reproduceRate
        self.canvas_object = canvas.create_rectangle(initial_pos[0]-5,
                                                        initial_pos[1]-5,
                                                        initial_pos[0]+5,
                                                        initial_pos[1]+5, 
                                                        fill="green")

    def reproduce(self):
        if len(plants) < maxPlants:
            x, y = self.genNewPosition(minPlantDistance, maxPlantDistance, plants, plant_lock)
            if (x and y):
                # print("new plant")
                newPlant = Plant([x, y], foodValue, plantRate)
                with plant_lock:
                    plants.append(newPlant)
                newPlant.start()

    def run(self):
        while self.foodValue > 0:
            if random.random() < self.reproduceRate:
                self.reproduce()
            self.waitForOtherThreads(plants, plant_lock, rabbits, rabbit_lock, foxes, fox_lock)
        # print("plant done")

    def getEaten(self):
        if (self.foodValue > 0):
            self.foodValue -= 1
            if (self.foodValue == 0):
                with plant_lock:
                    plants.remove(self)
                with canvas_lock:
                    canvas.delete(self.canvas_object)
            return True
        else:
            return False


def main():

    all_initial_pos = set()
            
    def initialize_start_positions(creatures, n_creatures, creature_class):
            for _ in range(n_creatures): 
                initial_pos = [random.randint(0, canvas_width-1), random.randint(0, canvas_height-1)]
                while tuple(initial_pos) in all_initial_pos:
                    initial_pos = [random.randint(0, canvas_width-1), random.randint(0, canvas_height-1)]
                all_initial_pos.add(tuple(initial_pos))

                if creature_class == Plant:
                    creature = creature_class(initial_pos, foodValue, plantRate)
                else:
                    creature = creature_class(initial_pos, health)
                creatures.append(creature)

    initialize_start_positions(foxes, n_foxes, Fox)
    initialize_start_positions(rabbits, n_rabbits, Rabbit)
    initialize_start_positions(plants, n_plants, Plant)

    for plant in plants:
        plant.start()

    for rabbit in rabbits:
        rabbit.start()

    for fox in foxes:
        fox.start()
    
    window.mainloop() ## this must be between the .start() and .join() function calls
    window.quit()

    for rabbit in rabbits: 
        rabbit.join()

    for fox in foxes:
        fox.join()


    # this does not print for some reason?
    print("Simulation Completed.")


if __name__ == "__main__":
    main()