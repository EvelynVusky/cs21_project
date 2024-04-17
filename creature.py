import tkinter as tk
import threading
from time import sleep
import random
import math
from global_stuff import *
from gene import *


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

    # def findAngle(self, food, predator, rabbit):
    #     distance_to_food = float('inf') if food is None else self.getDistanceTo(food)
    #     distance_to_rabbit = float('inf') if rabbit is None else self.getDistanceTo(rabbit)
    #     # print(f"{distance_to_rabbit =}")
    #     distance_to_predator = float('inf') if predator is None else self.getDistanceTo(predator)
    #     foodAngle = 0 if food is None else math.atan2(food.position[1] - self.position[1], food.position[0] - self.position[0])
    #     rabbitAngle = 0 if rabbit is None else math.atan2(rabbit.position[1] - self.position[1], rabbit.position[0] - self.position[0])
    #     # make Positive
    #     rabbitAngle = rabbitAngle if rabbitAngle >= 0 else rabbitAngle + (math.pi * 2)
    #     # assert(rabbitAngle >= 0)
    #     rabbitAngle = (rabbitAngle + math.pi) % (math.pi * 2)
    #     # print(rabbitAngle)
    #     # print("me: ", self.position[0], self.position[1], " them: ", rabbit.position[0], rabbit.position[1], " angle: ", rabbitAngle)
    #     predAngle = 0 if predator is None else math.atan2(predator.position[1] - self.position[1], predator.position[0] - self.position[0])
    #     predAngle = (predAngle + math.pi) % (math.pi * 2)

    #     foodFactor = 1 / (distance_to_food)
    #     predFactor = 1 / (distance_to_predator)
    #     rabbbitFactor = 1 / (distance_to_rabbit)
    #     totalFactor = foodFactor + predFactor + rabbbitFactor
    #     foodFactor = foodFactor / totalFactor
    #     predFactor = predFactor / totalFactor
    #     rabbbitFactor = rabbbitFactor / totalFactor
    #     # print(foodFactor + predFactor + rabbbitFactor)

    #     totalAngle = foodAngle * foodFactor + predAngle * predFactor + rabbitAngle * rabbbitFactor
    #     # print(totalAngle)
    #     return totalAngle

    def waitForOtherThreads(self, plants, plant_lock, rabbits, rabbit_lock, foxes, fox_lock):
        global semList
        notLast = True
        mySem = threading.Semaphore(value=0)
        with semListLock:
            with plant_lock:
                with rabbit_lock:
                    with fox_lock:
                        numArrived = len(semList)
                        # print("rabbits: ", len(rabbits))
                        # print("foxes: ", len(foxes))
                        # print(numArrived, "/", (len(plants) + len(rabbits) + len(foxes)))
                        if (numArrived + 1 == (len(plants) + len(rabbits) + len(foxes))):
                            notLast = False
                            # print("here")
                            sleep(.01)
                            # print("releasing ", len(semList))
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