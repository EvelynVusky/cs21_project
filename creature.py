import tkinter as tk
import threading
from time import sleep
import random
import math
from global_stuff import *
from gene import *
from stats_collector import *


class Creature:
    def __init__(self, initial_pos):
        self.position = initial_pos
        random.seed()

    # finds the distance between this creature and another (float)
    def getDistanceTo(self, otherCreature):
        if (self == otherCreature):
            return 10000
        return math.sqrt(((self.position[0] - otherCreature.position[0]) ** 2) + ((self.position[1] - otherCreature.position[1]) ** 2))

    def getDistanceToCoord(self, x, y):
        return math.sqrt(((self.position[0] - x) ** 2) + ((self.position[1] - y) ** 2))

    # gets the closest creature of given type
    def findClosest(self, creatureList, lock):
        with lock:
            if (len(creatureList) == 0):
                return None
            return min(creatureList, key=self.getDistanceTo)

    # gets the closest creature of specific type to the location
    def findClosestCreatureTo(self, x, y, creatureList, lock):
        def dist(creature):
            return math.sqrt(((x - creature.position[0]) ** 2) + ((y - creature.position[1]) ** 2))
        with lock:
            if (len(creatureList) == 0):
                return None
            return min(creatureList, key=dist)

    # choose a point, creature type and returns the distance between the point
    # and closest creature of that type
    def checkDensity(self, x, y, creatureList, lock):
        nearest = self.findClosestCreatureTo(x, y, creatureList, lock)
        return nearest.getDistanceToCoord(x, y)


    def findMovementVector(self, sizeStep, pointsOfInterest):
        totalDx = 0
        totalDy = 0
        for point in pointsOfInterest:
            x, y, scale = point
            dx = x - self.position[0]
            dy = y - self.position[1]
            dxNorm, dyNorm, magnitude = normalize_vector(dx, dy)
            if magnitude == 0: continue
            # decide how much we want each point to contribute to our final direction
            dxScaled = (dxNorm * scale) / magnitude
            dyScaled = (dyNorm * scale) / magnitude
            totalDx += dxScaled
            totalDy += dyScaled
        dx, dy = normalize_vector(totalDx, totalDy)[:2]
        return dx * sizeStep, dy * sizeStep

    def waitForOtherThreads(self, plants, plant_lock, rabbits, rabbit_lock, foxes, fox_lock):
        global semList
        notLast = True
        mySem = threading.Semaphore(value=0)
        with semListLock:
            with plant_lock:
                with rabbit_lock:
                    with fox_lock:
                        numArrived = len(semList)
                        if (numArrived + 1 == (len(plants) + len(rabbits) + len(foxes))):
                            notLast = False
                            sleep(.01)
                            for sem in semList:
                                sem.release()
                            semList = []
                        else:
                            semList.append(mySem)
  
        if notLast:
            mySem.acquire()

            
    # for reproduction, generates a new point
    def genNewPosition(self, minDist, maxDist, creatureList, lock):
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(minDist, maxDist)
        x = int(self.position[0] + distance * math.cos(angle))
        y = int(self.position[1] + distance * math.sin(angle))
        numTries = 10
        while numTries > 0:
            if check_bounds(x,y) and (self.checkDensity(x, y, creatureList, lock) > minDist):
                return x, y
            numTries -= 1
        return None, None

    def generate_position(self):
        dx, dy = 0, 0
        direction = random.randint(1, 4)
        if (direction == 1): ## above
            dy = -self.size_step
        elif (direction == 2): ## right
            dx = self.size_step
        elif (direction == 3): ## left
            dx = -self.size_step
        else: ## below
            dy = self.size_step
        return self.position[0] + dx, self.position[1] + dy


class Fox(Creature, threading.Thread):
    def __init__(self, initial_pos, health): 
        Creature.__init__(self, initial_pos)
        threading.Thread.__init__(self)
        self.size_step = foxSpeed
        self.health = health
        self.target = None
        self.canvas_object = canvas.create_polygon([initial_pos[0] - 10, initial_pos[1] - 10,  
                                                initial_pos[0] + 10, initial_pos[1] - 10,  
                                                initial_pos[0], initial_pos[1] + 10],    
                                               fill="red",             
                                               outline="")    

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
        while self.health > 0 and not sim_done_event.is_set():
            new_col, new_row, target = self.moveForSurvival()
            self.position[0], self.position[1] = clamp(new_col, 0, canvas_width), clamp(new_row, count_bottom, canvas_height)
            
            if isinstance(target, Rabbit):
                if (self.getDistanceTo(target) < 1 and target.getEaten()):
                    stats_collector.log_event('Rabbit was eaten', f'Died at position ({self.position[0]:.3f}, {self.position[1]:.3f})', self)
                    self.health = max(self.health + foxMetabolism, foxStomachSize)
            elif target == None:
                new_col, new_row = self.generate_position()
                while(not check_bounds(new_col, new_row)):
                    new_col, new_row = self.generate_position()

                self.position[0], self.position[1] = clamp(new_col, 0, canvas_width), clamp(new_row, count_bottom, canvas_height)
            
            with canvas_lock:
                canvas.moveto(self.canvas_object, int(self.position[0]) - 10, int(self.position[1]) - 10)
            
            # do reproduction
            if self.health > foxReproductionCutoff and random.random() < foxRate:
                stats_collector.log_event('New fox born', f'Born at position ({self.position[0]:.3f}, {self.position[1]:.3f})', self)
                self.reproduce()

            self.health -= 1
            # print(self.health)
            self.waitForOtherThreads(plants, plant_lock, rabbits, rabbit_lock, foxes, fox_lock)
        with fox_lock:
                stats_collector.log_event('Fox passed away', f'Died at position ({self.position[0]:.3f}, {self.position[1]:.3f})', self)
                foxes.remove(self)
        with canvas_lock:
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
                                                        fill=rgb_to_hex(genes.color), 
                                                        outline="")

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
                # print("My new mutation rate: ", newRabbit.genes.mutationRate)
                with rabbit_lock:
                    rabbits.append(newRabbit)
                newRabbit.start()
                return newGenes.startingHealth
        return 0

    def run(self): 
        while self.health > 0 and self in rabbits and not sim_done_event.is_set():
            new_col, new_row, target = self.moveForSurvival()
            self.position[0], self.position[1] = clamp(new_col, 0, canvas_width), clamp(new_row, count_bottom, canvas_height)

            if isinstance(target, Plant):
                if ((self.getDistanceTo(target) < 5) and target.getEaten()):
                    self.health = max(self.health + rabbitMetabolism, rabbitStomachSize)
            # elif target == None:
            #     new_col, new_row = self.generate_position()
            #     while(not check_bounds(new_col, new_row)):
            #         new_col, new_row = self.generate_position()

            #     self.position[0], self.position[1] = clamp(new_col, 0, canvas_width), clamp(new_row, count_bottom, canvas_height)
                
            with canvas_lock:
                canvas.moveto(self.canvas_object, int(self.position[0]) - 7, int(self.position[1]) - 7)

            # do reproduction
            if self.health > rabbitReproductionCutoff and random.random() < rabbitRate:
                cost = self.reproduce()
                if cost > 0:
                    stats_collector.log_event('New rabbit born', f'Born at position ({self.position[0]:.3f}, {self.position[1]:.3f})', self)
                # lose half the health we give to child
                self.health -= (cost / 2)

            self.health -= 1
            # print(self.health)
            self.waitForOtherThreads(plants, plant_lock, rabbits, rabbit_lock, foxes, fox_lock)
        with rabbit_lock:
            if self in rabbits:
                stats_collector.log_event('Rabbit passed away', f'Died at position ({self.position[0]:.3f}, {self.position[1]:.3f})', self)
                rabbits.remove(self)
        with canvas_lock:
            canvas.delete(self.canvas_object)

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
                                                        fill="green",
                                                        outline="")

    def reproduce(self):
        if len(plants) < maxPlants:
            x, y = self.genNewPosition(minPlantDistance, maxPlantDistance, plants, plant_lock)
            if (x and y):
                # print("new plant")
                newPlant = Plant([x, y], foodValue, plantRate)
                stats_collector.log_event('New plant born', f'Born at position ({newPlant.position[0]:.3f}, {newPlant.position[1]:.3f})', newPlant)
                with plant_lock:
                    plants.append(newPlant)
                newPlant.start()

    def run(self):
        while self.foodValue > 0 and not sim_done_event.is_set():
            if random.random() < self.reproduceRate:
                self.reproduce()
            self.waitForOtherThreads(plants, plant_lock, rabbits, rabbit_lock, foxes, fox_lock)
        # print("plant done")

    def getEaten(self):
        if (self.foodValue > 0):
            self.foodValue -= 1
            if (self.foodValue == 0):
                with plant_lock:
                    stats_collector.log_event('plant eaten', f'Died at position ({self.position[0]:.3f}, {self.position[1]:.3f})', self)
                    plants.remove(self)
                with canvas_lock:
                    canvas.delete(self.canvas_object)
            return True
        else:
            return False