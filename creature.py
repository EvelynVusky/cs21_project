import tkinter as tk
import threading
from time import sleep
import random
import math
from global_stuff import *
from gene import *
from stats_collector import *



###################### Base Creature Class ######################

# Creature class has most of the functions used by more than one type of
# creature. Also defines each creature to have an poistion array
class Creature:
    def __init__(self, initial_pos):
        """
        Initializes a Creature class object

        """
        self.position = initial_pos
        random.seed()

    def getDistanceTo(self, otherCreature):
        """
        Calculates the Euclidean distance between this creature and another
        creature.

        Args:
        - otherCreature: The other creature.

        Returns:
        - float: The distance between the two creatures.

        """
        if (self == otherCreature):
            return 10000
        return math.sqrt(((self.position[0] - otherCreature.position[0]) ** 2)
                       + ((self.position[1] - otherCreature.position[1]) ** 2))

    def getDistanceToCoord(self, x, y):
        """
        Calculates the Euclidean distance between this creature and a
        specified point.

        Args:
        - x (float): The x-coordinate of the point.
        - y (float): The y-coordinate of the point.

        Returns:
        - float: The distance between the creature and the point.

        """
        return math.sqrt(((self.position[0] - x) ** 2) +
                         ((self.position[1] - y) ** 2))

    def findClosest(self, creatureList, lock):
        """
        Finds the closest creature to this creature from a list of creatures.

        Args:
        - creatureList (list): List of creatures to search.
        - lock (threading.Lock): Lock for thread-safe access to shared data.

        Returns:
        - The closest creature to this creature.

        """
        with lock:
            if (len(creatureList) == 0):
                return None
            return min(creatureList, key=self.getDistanceTo)

    # gets the closest creature of specific type to the location
    def findClosestCreatureTo(self, x, y, creatureList, lock):
        """
        Finds the closest creature to a specified point from a list of creatures.

        Args:
        - x (float): The x-coordinate of the point.
        - y (float): The y-coordinate of the point.
        - creatureList (list): List of creatures to search.
        - lock (threading.Lock): Lock for thread-safe access to shared data.

        Returns:
        - The closest creature to the specified point.

        """
        def dist(creature):
            return math.sqrt(((x - creature.position[0]) ** 2) +
                             ((y - creature.position[1]) ** 2))
        with lock:
            if (len(creatureList) == 0):
                return None
            return min(creatureList, key=dist)

    def checkDensity(self, x, y, creatureList, lock):
        """
        Checks the density of creatures around a specified point. Choose a
        point, creature type and returns the distance between the point
        and closest creature of that type

        Args:
        - x (float): The x-coordinate of the point.
        - y (float): The y-coordinate of the point.
        - creatureList (list): List of creatures to search.
        - lock (threading.Lock): Lock for thread-safe access to shared data.

        Returns:
        - float: The distance to the nearest creature from the specified point.

        """
        nearest = self.findClosestCreatureTo(x, y, creatureList, lock)
        return nearest.getDistanceToCoord(x, y)


    def findMovementVector(self, sizeStep, pointsOfInterest):
        """
        Finds the movement vector for the creature based on points of interest.

        Args:
        - sizeStep (float): The size step of the creature.
        - pointsOfInterest (list): List of points of interest (x, y, scale).

        Returns:
        - tuple: A tuple containing the movement vector (dx, dy).

        """
        totalDx = 0
        totalDy = 0
        for point in pointsOfInterest:
            x, y, scale = point
            # find the vector to the point
            dx = x - self.position[0]
            dy = y - self.position[1]
            # normalize the vector
            dxNorm, dyNorm, magnitude = normalize_vector(dx, dy)
            if magnitude == 0: continue
            # scale the vector based on the scale (which can be negative to
            # avoit a point of interest) and lessen the imact based on the
            # distance to a point so nearby points will be more important
            dxScaled = (dxNorm * scale) / magnitude
            dyScaled = (dyNorm * scale) / magnitude
            # add this vector to our results vector
            totalDx += dxScaled
            totalDy += dyScaled
        # dx, dy represents a vector with the direction we want to go but
        # not the right length so we normalize
        dx, dy = normalize_vector(totalDx, totalDy)[:2]
        # finally, we move one timestep in the direction dx, dy
        return dx * sizeStep, dy * sizeStep

    def waitForOtherThreads(self, plants, plant_lock, rabbits,
                            rabbit_lock, foxes, fox_lock):
        """
        Waits for other threads to arrive at a synchronization point.

        Args:
        - plants (list): List of plants.
        - plant_lock (threading.Lock): Lock for plant-related operations.
        - rabbits (list): List of rabbits.
        - rabbit_lock (threading.Lock): Lock for rabbit-related operations.
        - foxes (list): List of foxes.
        - fox_lock (threading.Lock): Lock for fox-related operations.

        """
        global semList
        notLast = True
        mySem = threading.Semaphore(value=0)
        # we need to aquire all of the locks so the number of creatures doesn't
        # change while we are checking if we are the last creature
        with semListLock:
            with plant_lock:
                with rabbit_lock:
                    with fox_lock:
                        # this could maybe be handled as just a count
                        numArrived = len(semList)
                        if (numArrived + 1 == (len(plants) +
                                               len(rabbits) +
                                               len(foxes))):
                            notLast = False
                            # Sleep for 0.01 seconds here to cap the framerate
                            # at 100fps
                            sleep(.01)
                            # release all of the waiting threads
                            for sem in semList:
                                sem.release()
                            # empty the list
                            semList = []
                        else:
                            semList.append(mySem)
  
        if notLast:
            mySem.acquire()

            
    def genNewPosition(self, minDist, maxDist, creatureList, lock):
        """
        Generates a new valid set of coordinates for a child for the given
        creature within a specified distance range.

        Args:
        - minDist (float): Minimum distance from current position.
        - maxDist (float): Maximum distance from current position.
        - creatureList (list): List of creatures to avoid.
        - lock (threading.Lock): Lock for thread-safe access to shared data.

        Returns:
        - tuple: A tuple containing the new x and y coordinates.

        """
        # use polar coordinates to pick a random point within a circular
        # distance from self.
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(minDist, maxDist)
        # translate to euclidean coordinates
        x = int(self.position[0] + distance * math.cos(angle))
        y = int(self.position[1] + distance * math.sin(angle))
        # we cap the number of tries to prevent an infinite loop if the
        # board becomes too dense.
        numTries = 10
        while numTries > 0:
            # assuming the point is within bounds and more than minDist from
            # any other creature of the same type it's a valid point
            if check_bounds(x,y) and (self.checkDensity(x,
                                                        y,
                                                        creatureList,
                                                        lock) > minDist):
                return x, y
            numTries -= 1
        # if no point can be found return none
        return None, None

    def generate_position(self):
        """
        Generates a new position for the creature by moving in a random
        direction. Used when creatures don't have any points of interest

        Returns:
        - tuple: A tuple containing the new x and y coordinates.

        """
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




###################### Fox Class ######################

class Fox(Creature, threading.Thread):
    def __init__(self, initial_pos, health): 
        """
        Initializes a Fox class object

        """
        Creature.__init__(self, initial_pos)
        threading.Thread.__init__(self)
        self.size_step = foxSpeed
        self.health = health
        self.target = None
        self.canvas_object = canvas.create_polygon([initial_pos[0] - 10,
                                                    initial_pos[1] - 10,  
                                                    initial_pos[0] + 10,
                                                    initial_pos[1] - 10,  
                                                    initial_pos[0],
                                                    initial_pos[1] + 10],    
                                                    fill="red",             
                                                    outline="")    

    # gets the closest edible creature
    def findClosestFood(self):
        """
        Wrapper for findClosest(rabbits, rabbit_lock)

        """
        return self.findClosest(rabbits, rabbit_lock)

    def findClosestPredator(self):
        """
        Wrapper for findClosest(foxes, fox_lock)

        """
        return self.findClosest(foxes, fox_lock)

    def moveForSurvival(self):
        """
        Moves the creature to survive by avoiding predators and seeking food.

        Returns:
        - tuple: A tuple containing the new x and y coordinates and the
        target creature.

        """
        # This code is very similar to our original rabbit code before
        # rewriting their movement and adding genetics. Foxes avoid
        # one another which is why they use the closest "predator"
        # even though they are also a predator
        food = self.findClosestFood()
        predator = self.findClosestPredator()

        # if nothing of interest, move randomly
        if not predator and not food:
            return self.position[0], self.position[1], None
        
        # get the distance to the closest food and predator
        distance_to_food = float('inf')
        distance_to_predator = float('inf')
        if food:
            distance_to_food = self.getDistanceTo(food)
        if predator:
            distance_to_predator = self.getDistanceTo(predator)

        # the avoidOthers parameter controls how much foxes care about other
        # foxes or food
        if (distance_to_food * avoidOthers) < (distance_to_predator *
                                              (1 - avoidOthers)):
            self.target = food
            # get vector towards the food
            dx = food.position[0] - self.position[0]
            dy = food.position[1] - self.position[1]
            
        elif predator:
            self.target = predator
            # get the vector away from the predator
            dx = self.position[0] - predator.position[0]
            dy = self.position[1] - predator.position[1]

        # find the length of the vector
        distance = math.sqrt(dx**2 + dy**2)
        # if it's farther than we can move, scale it to size_step
        if distance > self.size_step:
            dx = (dx / distance) * self.size_step
            dy = (dy / distance) * self.size_step
            # print(dx, dy)

        return self.position[0] + dx, self.position[1] + dy, self.target

    def reproduce(self):
        """
        Creates a new fox in a valid position if the population is below
        the maximum limit.

        """
        if len(foxes) < maxFoxes:
            x, y = self.genNewPosition(minFoxDistance, maxFoxDistance,
                                                        foxes, fox_lock)
            # if we found a valid point then make a new fox.
            # because we handle reproduction this way, there is a chance when
            # a fox "reproduces" it doesn't spawn a new fox because there were
            # too many other foxes nearby
            if (x and y):
                newFox = Fox([x, y], health)
                with fox_lock:
                    foxes.append(newFox)
                newFox.start()

    def run(self): 
        """
        Runs the behavior of the fox in the simulation.

        """
        # as long as it's alive and the simulation is running
        while self.health > 0 and not sim_done_event.is_set():
            # move the fox
            new_col, new_row, target = self.moveForSurvival()
            self.position[0] = clamp(new_col, 0, canvas_width)
            self.position[1] = clamp(new_row, stat_bottom, canvas_height)
            
            # if it's hunting a rabbit, is close enough and another fox didn't
            # get it earlier this timestep, then we can increase our health
            if isinstance(target, Rabbit):
                if (self.getDistanceTo(target) < 1 and target.getEaten()):
                    stats_collector.log_event('Rabbit was eaten',
                                            f'''Died at position
                                            ({self.position[0]:.3f},
                                             {self.position[1]:.3f})''', self)
                    self.health = max(self.health + foxMetabolism,
                                                    foxStomachSize)
            elif target == None:
                # move randomly
                new_col, new_row = self.generate_position()
                while(not check_bounds(new_col, new_row)):
                    new_col, new_row = self.generate_position()

                self.position[0] = clamp(new_col, 0, canvas_width)
                self.position[1] = clamp(new_row, stat_bottom, canvas_height)
            
            # update our visual position
            with canvas_lock:
                canvas.moveto(self.canvas_object, int(self.position[0]) - 10,
                                                  int(self.position[1]) - 10)
            
            # do reproduction
            if self.health > foxReproductionCutoff and random.random() < foxRate:
                stats_collector.log_event('New fox born',
                                f'''Born at position ({self.position[0]:.3f},
                                {self.position[1]:.3f})''', self)
                self.reproduce()

            self.health -= 1
            # wait for other threads to finsih this timestep
            self.waitForOtherThreads(plants, plant_lock, rabbits, rabbit_lock,
                                                         foxes, fox_lock)
        with fox_lock:
                stats_collector.log_event('Fox passed away',
                                f'''Died at position ({self.position[0]:.3f},
                                {self.position[1]:.3f})''', self)
                foxes.remove(self)
        with canvas_lock:
            canvas.delete(self.canvas_object)




###################### Rabbit Class ######################

class Rabbit(Creature, threading.Thread):    
    def __init__(self, initial_pos, genes):
        """
        Initializes a Rabbit class object

        """
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
                                                        fill=rgb_to_hex(
                                                            genes.color),
                                                        outline="")

    # we should make this detect if there is no food on the map
    def findClosestFood(self):
        """
        Wrapper for findClosest(plants, plant_lock)

        """
        return self.findClosest(plants, plant_lock)
    
    def findClosestPredator(self):
        """
        Wrapper for findClosest(foxes, fox_lock)

        """
        return self.findClosest(foxes, fox_lock)

    def findClosestRabbit(self):
        """
        Wrapper for findClosest(rabbits, rabbit_lock)

        """
        return self.findClosest(rabbits, rabbit_lock)
    
    def generatePriorityList(self):
        """
        Generates a list of priorities based on the closest food, predator,
        and rabbit.

        Returns:
        - list: List of tuples containing the x and y coordinates of each
        priority and its weight.

        """
        food = self.findClosestFood()
        predator = self.findClosestPredator()
        rabbit = self.findClosestRabbit()

        priorities = []

        # add each item to our priorities if it exists
        if food:
            priorities.append((food.position[0],
                               food.position[1],
                               self.genes.hungerFactor))

        # we make the fear factor negative to make rabbits afraid of foxes
        # this becomes the scale factor when calculating the movement vector
        if predator:
            priorities.append((predator.position[0],
                               predator.position[1],
                               self.genes.fearFactor * -1))

        # we also make rabbits avoid each other but only up to a certain point
        # this just prevents them from overlapping too much right now. 
        # we found that making the rabbit radius too large meant that spread
        # out too much and ended up not leaving space for food to spawn before
        # being immidietly eaten
        if rabbit:
            if self.getDistanceTo(rabbit) < rabbitRadius:
                priorities.append((rabbit.position[0],
                                   rabbit.position[1],
                                   self.genes.avoidOthersFactor * -1))

        return priorities

    def moveForSurvival(self):
        """
        Moves the rabbit for survival based on the generated priority list.

        Returns:
        - tuple: A tuple containing the new x and y coordinates and the
        closest food.

        """
        # we still look for the closest food here so we can check if we are
        # close enough to eat it
        food = self.findClosestFood()

        # see the findMovementVector and generatePriorityList functions
        dx, dy = self.findMovementVector(self.size_step,
                                         self.generatePriorityList())

        return self.position[0] + dx, self.position[1] + dy, food
    
    def getEaten(self):
        """
        Marks the rabbit as eaten.

        Returns:
        - bool: True if the rabbit was successfully eaten, False otherwise.

        """
        # we set the health to 0 for two reasons here. First, it prevents one
        # rabbit from being eaten multiple times in the same time step (if two
        # foxes had called this rabbits getEaten method at once). Second,
        # setting the health to 0 will cause the rabbit to die and remove
        # itself from the simulation on its next timestep. We originally
        # removed the rabbit both here and seperatly if it starved which ended
        # up causing a lot of problems so this was much cleaner.
        with rabbit_lock:
            if self.health > 0:
                self.health = 0
                return True
            else:
                return False

    def reproduce(self):
        """
        Creates a new rabbit at a valid location if the population is below
        the maximum limit.

        Returns:
        - int: The starting health of the new rabbit if reproduction is
        successful, 0 otherwise.

        """
        if len(rabbits) < maxRabbits:
            x, y = self.genNewPosition(minRabbitDistance, maxRabbitDistance,
                                                          rabbits, rabbit_lock)
            if (x and y):
                # since the above check can fail, there is a chance that a
                # rabbit won't produce a child even if it calls this function

                # mutate the parent genes to produce child genes
                newGenes = self.genes.childGene()

                # create and add a new rabbit
                newRabbit = Rabbit([x, y], newGenes)
                with rabbit_lock:
                    rabbits.append(newRabbit)
                newRabbit.start()

                # if a child is born the parent loses some food/health
                # proportional to the amount the child was born with.
                # this currently isn't very important because rabbit birth-rate
                # currently doesn't evolve. However, if we allowed that gene
                # to mutate and didn't penalize rabbits for having children
                # the rabbits would keep evolving a higher reproduction rate
                # with no tradeoff
                return newGenes.startingHealth
        # if no child was produced the rabbit is not penalized
        return 0

    def run(self): 
        """
        Runs the behavior of the rabbit in the simulation.

        """
        while (self.health > 0 and not sim_done_event.is_set()):
            new_col, new_row, target = self.moveForSurvival()
            self.position[0] = clamp(new_col, 0, canvas_width)
            self.position[1] = clamp(new_row, stat_bottom, canvas_height)

            # eat a plant if it's close enough
            if isinstance(target, Plant):
                if ((self.getDistanceTo(target) < 5) and target.getEaten()):
                    self.health = max(self.health + rabbitMetabolism,
                                                    rabbitStomachSize)
                
            with canvas_lock:
                canvas.moveto(self.canvas_object, int(self.position[0]) - 7,
                                                  int(self.position[1]) - 7)

            # do reproduction
            if (self.health > rabbitReproductionCutoff
                            and random.random() < rabbitRate):
                cost = self.reproduce()
                if cost > 0:
                    stats_collector.log_event('New rabbit born',
                                                    f'''Born at position
                                                    ({self.position[0]:.3f},
                                                    {self.position[1]:.3f})''',
                                                     self)
                # lose half the health we give to child
                self.health -= (cost / 2)

            # decriment our health each timestep to represent starvation
            self.health -= 1

            # wait for other threads
            self.waitForOtherThreads(plants, plant_lock, rabbits, rabbit_lock,
                                                         foxes, fox_lock)
        with rabbit_lock:
            if self in rabbits:
                stats_collector.log_event('Rabbit passed away',
                                        f'''Died at position
                                        ({self.position[0]:.3f},
                                         {self.position[1]:.3f})''', self)
                rabbits.remove(self)
        with canvas_lock:
            canvas.delete(self.canvas_object)





###################### Plant Class ######################

class Plant(Creature, threading.Thread):
    def __init__(self, initial_pos, health, reproduceRate): 
        """
        Initializes a Plant class object

        """
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
        """
        Creates a new plant at a valid location if the population is below
        the maximum limit.

        """
        if len(plants) < maxPlants:
            x, y = self.genNewPosition(minPlantDistance, maxPlantDistance,
                                                         plants, plant_lock)
            if (x and y):
                # plant reproduction is the same as rabbits and foxes although
                # the restriction on density is much more important since it
                # effectivly caps the number of plants that can exist in an
                # area
                newPlant = Plant([x, y], foodValue, plantRate)
                stats_collector.log_event('New plant born',
                            f'''Born at position ({newPlant.position[0]:.3f},
                            {newPlant.position[1]:.3f})''', newPlant)
                with plant_lock:
                    plants.append(newPlant)
                newPlant.start()

    def run(self):
        """
        Runs the behavior of the plant in the simulation.

        """
        while self.foodValue > 0 and not sim_done_event.is_set():
            # plants just reproduce and can be eaten
            if random.random() < self.reproduceRate:
                self.reproduce()
            self.waitForOtherThreads(plants, plant_lock, rabbits, rabbit_lock,
                                                         foxes, fox_lock)

    def getEaten(self):
        """
        Marks the plant as eaten.

        Returns:
        - bool: True if the plant was successfully eaten, False otherwise.

        """
        # We built in the ability for plants to have more than bite taken
        # out of them but found it cause rabbits to bunch up more than
        # we liked so we kept it at 1 most of the time.
        if (self.foodValue > 0):
            self.foodValue -= 1
            if (self.foodValue == 0):
                with plant_lock:
                    stats_collector.log_event('plant eaten',
                                f'''Died at position ({self.position[0]:.3f},
                                {self.position[1]:.3f})''', self)
                    plants.remove(self)
                with canvas_lock:
                    canvas.delete(self.canvas_object)
            return True
        else:
            return False
