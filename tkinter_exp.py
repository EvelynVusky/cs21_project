import tkinter as tk
import threading
from time import sleep
import random
import math
import argparse

def capped_int(value, cap):
    ivalue = int(value)

    if ivalue <= 0:
        raise argparse.ArgumentTypeError("%s is an invalid int value" % value)
    elif ivalue > cap:
        raise argparse.ArgumentTypeError("%s exceeds the limit of %s" % (value, cap))
    
    return ivalue

parser = argparse.ArgumentParser(description="Parse simulation start configurations.")

parser.add_argument('--plants', metavar='PLANTS', type=lambda x: capped_int(x, 400), default=60,
                    help='Number of plants at the start of the simulation; Max number of foxes to start with is 400')
parser.add_argument('--rabbits', metavar='RABBITS', type=lambda x: capped_int(x, 300), default=20,
                    help='Number of rabbits at the start of the simulation; Max number of rabbits to start with is 300')
parser.add_argument('--foxes', metavar='FOXES', type=lambda x: capped_int(x, 300), default=4,
                    help='Number of foxes at the start of the simulation; Max number of foxes to start with is 300')
parser.add_argument('--height', metavar='HEIGHT', type=lambda x: capped_int(x, 1000), default=500,
                    help='Height of the canvas; Max height is 500')
parser.add_argument('--width', metavar='WIDTH', type=lambda x: capped_int(x, 1500), default=500,
                    help='Width of the canvas; Max width is 500')

args = parser.parse_args()


# Simulation Parameters
health = 200 # starting health of rabbits and foxes

# Plant info
n_plants = args.plants
foodValue = 1 # number of times food can be eated before destruction
plantRate = 0.015 # likelyhood that any plant will reproduce each time step
maxPlants = 500 # max number of plants
minPlantDistance = 30 # minimum distance plants must be from each other
maxPlantDistance = 50 # maximum distance plants can be from their parent

# rabbit info
n_rabbits = args.rabbits
rabbitMetabolism = 50 # amount of health that rabbits get back per food
rabbitStomachSize = 300 # max amount of health a rabbit can have
rabbitSpeed = 1
rabbitRate = 0.008 # likelyhood that any healthy rabbit will reproduce each time step
fearFactor = 0.5
maxRabbits = 100 # max number of plants
minRabbitDistance = 30 # minimum distance plants must be from each other
maxRabbitDistance = 50 # maximum distance plants can be from their parent

# fox info
n_foxes = args.foxes
foxMetabolism = 50 # amount of health that rabbits get back per food
foxStomachSize = 300 # max amount of health a rabbit can have
foxSpeed = 2
foxRate = 0.0013 # likelyhood that any healthy rabbit will reproduce each time step
avoidOthers = 0.3
maxFoxes = 50 # max number of plants
minFoxDistance = 30 # minimum distance plants must be from each other
maxFoxDistance = 50 # maximum distance plants can be from their parent

canvas_height = args.height
canvas_width = args.width

canvas_lock = threading.Lock()

window = tk.Tk() 
window.title("Foxes, Rabbits, & Plants Simulation")
canvas = tk.Canvas(window, width=canvas_width, height=canvas_height, bg="white")
canvas.pack()

rabbits = []
plants = []
foxes = []

rabbit_lock = threading.Lock()
plant_lock = threading.Lock()
fox_lock = threading.Lock()

semList = []
semListLock = threading.Lock()


def check_bounds(col, row): 
    if col < 10 or col >= canvas_width-10:
        return False
    elif row < 10 or row >= canvas_height-10:
        return False
    else:
        return True

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

    def waitForOtherThreads(self):
        global semList
        notLast = True
        mySem = threading.Semaphore(value=0)
        with semListLock:
            with plant_lock:
                with rabbit_lock:
                    with fox_lock:
                        numArrived = len(semList)
                        # print(numArrived, "/", (len(plants) + len(rabbits) + len(foxes)))
                        if (numArrived + 1 == (len(plants) + len(rabbits) + len(foxes))):
                            notLast = False
                            # print("here")
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
        x = self.position[0] + int(distance * math.cos(angle))
        y = self.position[1] + int(distance * math.sin(angle))
        numTries = 10
        while numTries > 0:
            if check_bounds(x,y) and (self.checkDensity(x, y, creatureList, lock) > minDist):
                return x, y
            numTries -= 1
        return None, None

    def generate_position(self):
        col, row = self.position[0], self.position[1]
        dx, dy = 0, 0
        direction = random.randint(1, 4)
        if (direction == 1): ## above
            row -= self.size_step
            dy = -self.size_step
        elif (direction == 2): ## right
            col += self.size_step
            dx = self.size_step
        elif (direction == 3): ## left
            col -= self.size_step
            dx = -self.size_step
        else: ## below
            row += self.size_step
            dy = self.size_step
        return col, row, dx, dy

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
            self.waitForOtherThreads()
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
            self.waitForOtherThreads()
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
            self.waitForOtherThreads()
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