import tkinter as tk
import threading
from time import sleep
import random
import math
from global_stuff import *
from creature import *
from gene import *
from stats_collector import *

class Fox(Creature, threading.Thread):
    def __init__(self, initial_pos, health): 
        Creature.__init__(self, initial_pos)
        threading.Thread.__init__(self)
        self.size_step = foxSpeed
        self.health = health
        self.target = None
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
            return self.position[0], self.position[1], None
        
        distance_to_food = float('inf') if food is None else self.getDistanceTo(food)
        distance_to_predator = float('inf') if predator is None else self.getDistanceTo(predator)

        if (distance_to_food * avoidOthers) < (distance_to_predator * (1 - avoidOthers)):
            self.target = food
            dx = food.position[0] - self.position[0]
            dy = food.position[1] - self.position[1]
            
        elif predator:
            self.target = predator
            dx = self.position[0] - predator.position[0]
            dy = self.position[1] - predator.position[1]

        distance = math.sqrt(dx**2 + dy**2)
        if distance > self.size_step:
            dx = (dx / distance) * self.size_step
            dy = (dy / distance) * self.size_step
            # print(dx, dy)

        return self.position[0] + dx, self.position[1] + dy, self.target

    def reproduce(self):
        if len(foxes) < maxFoxes:
            x, y = self.genNewPosition(minFoxDistance, maxFoxDistance, foxes, fox_lock)
            if (x and y):
                newFox = Fox([x, y], health)
                with fox_lock:
                    foxes.append(newFox)
                newFox.start()

    def run(self): 
        while self.health > 0:
            new_col, new_row, target = self.moveForSurvival()
            self.position[0], self.position[1] = clamp(new_col, 0, canvas_width), clamp(new_row, 0, canvas_height)
            
            if isinstance(target, Rabbit):
                if (self.getDistanceTo(target) < 1 and target.getEaten()):
                    self.health = max(self.health + foxMetabolism, foxStomachSize)
            elif target == None:
                new_col, new_row = self.generate_position()
                while(not check_bounds(new_col, new_row)):
                    new_col, new_row = self.generate_position()

                self.position[0], self.position[1] = clamp(new_col, 0, canvas_width), clamp(new_row, 0, canvas_height)
            
            with canvas_lock:
                canvas.moveto(self.canvas_object, int(self.position[0]) - 10, int(self.position[1]) - 10)
            
            # do reproduction
            if self.health > foxReproductionCutoff and random.random() < foxRate:
                self.reproduce()

            self.health -= 1
            # print(self.health)
            self.waitForOtherThreads(plants, plant_lock, rabbits, rabbit_lock, foxes, fox_lock)
        with fox_lock:
                foxes.remove(self)
        with canvas_lock:
            stats_collector.log_event('Rabbit Died', 'died at position {self.position}')
            canvas.delete(self.canvas_object)



class Rabbit(Creature, threading.Thread):    
    def __init__(self, initial_pos, genes):
        Creature.__init__(self, initial_pos)
        threading.Thread.__init__(self)
        self.genes = genes
        self.size_step = genes.speed
        self.health = genes.startingHealth
        self.target = None
        self.canvas_object = canvas.create_oval(initial_pos[0]-7,
                                                        initial_pos[1]-7,
                                                        initial_pos[0]+7,
                                                        initial_pos[1]+7, 
                                                        fill=rgb_to_hex(genes.color))

    # we should make this detect if there is no food on the map
    def findClosestFood(self):
        return self.findClosest(plants, plant_lock)
    
    def findClosestPredator(self):
        return self.findClosest(foxes, fox_lock)

    def findClosestRabbit(self):
        return self.findClosest(rabbits, rabbit_lock)
    
    def generatePriorityList(self):
        food = self.findClosestFood()
        predator = self.findClosestPredator()
        rabbit = self.findClosestRabbit()

        priorities = []

        if food:
            priorities.append((food.position[0], food.position[1], self.genes.hungerFactor))

        if predator:
            priorities.append((predator.position[0], predator.position[1], self.genes.fearFactor * -1))

        if rabbit:
            if self.getDistanceTo(rabbit) < rabbitRadius:
                priorities.append((rabbit.position[0], rabbit.position[1], self.genes.fearFactor * -1))

        return priorities


    # find the closest food item and moves towards it, move away from predators
    def moveForSurvival(self):
        food = self.findClosestFood()
        # if not predator and not food:
        #     return self.position[0], self.position[1], None
        
        # distance_to_food = float('inf') if food is None else self.getDistanceTo(food)
        # distance_to_predator = float('inf') if predator is None else self.getDistanceTo(predator)

        dx, dy = self.findMovementVector(self.size_step, self.generatePriorityList())

        # dx = math.cos(self.findAngle(food, predator, rabbit)) * self.size_step
        # dy = math.sin(self.findAngle(food, predator, rabbit)) * self.size_step

        # if (distance_to_food * fearFactor) < (distance_to_predator * (1 - fearFactor)):
        #     self.target = food
        #     dx = food.position[0] - self.position[0]
        #     dy = food.position[1] - self.position[1]
            
        # elif predator:
        #     self.target = predator
        #     dx = self.position[0] - predator.position[0]
        #     dy = self.position[1] - predator.position[1]

        # distance = math.sqrt(dx**2 + dy**2)
        # if distance > self.size_step:
        #     dx = (dx / distance) * self.size_step
        #     dy = (dy / distance) * self.size_step
        #     # print(dx, dy)

        return self.position[0] + dx, self.position[1] + dy, food
    
    def getEaten(self):
        with rabbit_lock:
            if self.health > 0:
                self.health = 0
                return True
            else:
                return False

    def reproduce(self):
        if len(rabbits) < maxRabbits:
            x, y = self.genNewPosition(minRabbitDistance, maxRabbitDistance, rabbits, rabbit_lock)
            if (x and y):
                newGenes = self.genes.childGene()
                newRabbit = Rabbit([x, y], newGenes)
                with rabbit_lock:
                    rabbits.append(newRabbit)
                newRabbit.start()
                return newGenes.startingHealth
        return 0

    def run(self): 
        while self.health > 0 and self in rabbits:
            new_col, new_row, target = self.moveForSurvival()
            self.position[0], self.position[1] = clamp(new_col, 0, canvas_width), clamp(new_row, 0, canvas_height)

            if isinstance(target, Plant):
                if ((self.getDistanceTo(target) < 5) and target.getEaten()):
                    self.health = max(self.health + rabbitMetabolism, rabbitStomachSize)
            # elif target == None:
            #     new_col, new_row = self.generate_position()
            #     while(not check_bounds(new_col, new_row)):
            #         new_col, new_row = self.generate_position()

            #     self.position[0], self.position[1] = clamp(new_col, 0, canvas_width), clamp(new_row, 0, canvas_height)
                
            with canvas_lock:
                canvas.moveto(self.canvas_object, int(self.position[0]) - 7, int(self.position[1]) - 7)

            # do reproduction
            if self.health > rabbitReproductionCutoff and random.random() < rabbitRate:
                cost = self.reproduce()
                # lose half the health we give to child
                self.health -= (cost / 2)

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
                elif creature_class == Rabbit:
                    creature = creature_class(initial_pos, Gene(rabbitStartingGenes))
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