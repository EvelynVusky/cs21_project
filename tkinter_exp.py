import tkinter as tk
import threading
from time import sleep
import random
import sys
import math

canvas_height = 500
canvas_width = 500
canvas_lock = threading.Lock()

window = tk.Tk() 
window.title("Rabbits + Plants Simulation")
canvas = tk.Canvas(window, width=canvas_width, height=canvas_height, bg="white")
canvas.pack()

rabbits = []
plants = []
foxes = []

rabbit_lock = threading.Lock()
plant_lock = threading.Lock()
fox_lock = threading.Lock()

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

class Fox(Creature, threading.Thread):
    def __init__(self, initial_pos, total_moves): 
        Creature.__init__(self, initial_pos)
        threading.Thread.__init__(self)
        self.size_step = 10
        self.total_moves = total_moves
        self.canvas_object = canvas.create_oval(initial_pos[0],
                                                        initial_pos[1],
                                                        initial_pos[0]+20,
                                                        initial_pos[1]+20, 
                                                        fill="red")   
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

    # finds the distance between this creature and another (float)
    def getDistanceTo(self, otherCreature):
        return math.sqrt(((self.position[0] - otherCreature.position[0]) ** 2) + ((self.position[1] - otherCreature.position[1]) ** 2))

    # we should make this detect if there is no food on the map
    def findClosestFood(self):
        # filtered_plants = [x for x in plants if hasValue(x)]
        with rabbit_lock:
            if (len(rabbits) == 0):
                return None
            return min(rabbits, key=self.getDistanceTo)

    # find the closest food item and moves towards it
    def moveTowardsClosestFood(self):
        food = self.findClosestFood()
        if (not food):
            return self.position[0], self.position[1], 0, 0, None

        dx = food.position[0] - self.position[0]
        dy = food.position[1] - self.position[1]

        if self.getDistanceTo(food) > self.size_step:
            dx = int((dx / self.getDistanceTo(food)) * self.size_step)
            dy = int((dy / self.getDistanceTo(food)) * self.size_step)

        return self.position[0] + dx, self.position[1] + dy, dx, dy, food

    def run(self): 
        while self.total_moves > 0:
            new_col, new_row, dx, dy, food = self.moveTowardsClosestFood()
            if (not food):
                new_col, new_row, dx, dy = self.generate_position()
                while(not check_bounds(new_col, new_row)):
                    new_col, new_row, dx, dy = (self.generate_position()) 

                self.position[0], self.position[1] = new_col, new_row
                with canvas_lock:
                    canvas.move(self.canvas_object, dx, dy)
                    canvas.update()
            else:
                self.position[0], self.position[1] = new_col, new_row
                with canvas_lock:
                    if ((self.getDistanceTo(food) < 1)):
                        # alternativly we could make this setting the value instead of increasing
                        food.getEaten()
                        self.total_moves += 10

                    canvas.move(self.canvas_object, dx, dy)
                    canvas.update()

            self.total_moves -= 1
            # print(self.total_moves)
            sleep(1)
            # Some kind of barrier here to prevent rabbits from taking more
            # than one "turn" before other rabbits due to thread sleep
            # print("rabbit moved")
        with fox_lock:
                foxes.remove(self)
        with canvas_lock:
            canvas.delete(self.canvas_object)
            canvas.update()
        print("fox is done")


class Rabbit(Creature, threading.Thread):    
    def __init__(self, initial_pos, total_moves): 
        Creature.__init__(self, initial_pos)
        threading.Thread.__init__(self)
        self.size_step = 10
        self.total_moves = total_moves
        self.canvas_object = canvas.create_oval(initial_pos[0],
                                                        initial_pos[1],
                                                        initial_pos[0]+15,
                                                        initial_pos[1]+15, 
                                                        fill="blue")
    
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

    # finds the distance between this creature and another (float)
    def getDistanceTo(self, otherCreature):
        return math.sqrt(((self.position[0] - otherCreature.position[0]) ** 2) + ((self.position[1] - otherCreature.position[1]) ** 2))

    # we should make this detect if there is no food on the map
    def findClosestFood(self):
        # filtered_plants = [x for x in plants if hasValue(x)]
        with plant_lock:
            if (len(plants) == 0):
                return None
            return min(plants, key=self.getDistanceTo)

    # find the closest food item and moves towards it
    def moveTowardsClosestFood(self):
        food = self.findClosestFood()
        if (not food):
            return self.position[0], self.position[1], 0, 0, None

        dx = food.position[0] - self.position[0]
        dy = food.position[1] - self.position[1]

        if self.getDistanceTo(food) > self.size_step:
            dx = int((dx / self.getDistanceTo(food)) * self.size_step)
            dy = int((dy / self.getDistanceTo(food)) * self.size_step)

        return self.position[0] + dx, self.position[1] + dy, dx, dy, food

    def getEaten(self):
        with rabbit_lock:
            rabbits.remove(self)
        canvas.delete(self.canvas_object)
        canvas.update()

        
    def run(self): 
        while self.total_moves > 0:
            new_col, new_row, dx, dy, food = self.moveTowardsClosestFood()
            if (not food):
                new_col, new_row, dx, dy = self.generate_position()
                while(not check_bounds(new_col, new_row)):
                    new_col, new_row, dx, dy = (self.generate_position()) 

                self.position[0], self.position[1] = new_col, new_row
                with canvas_lock:
                    canvas.move(self.canvas_object, dx, dy)
                    canvas.update()
            else:
                self.position[0], self.position[1] = new_col, new_row
                with canvas_lock:
                    if ((self.getDistanceTo(food) < 1)):
                        # alternativly we could make this setting the value instead of increasing
                        food.getEaten()
                        self.total_moves += 10

                    canvas.move(self.canvas_object, dx, dy)
                    canvas.update()

            self.total_moves -= 1
            # print(self.total_moves)
            sleep(1)
            # Some kind of barrier here to prevent rabbits from taking more
            # than one "turn" before other rabbits due to thread sleep
            # print("rabbit moved")
        with rabbit_lock:
                if self in rabbits:
                    rabbits.remove(self)
        with canvas_lock:
            canvas.delete(self.canvas_object)
            canvas.update()
        print("rabbit is done")



#PLANTS
class Plant(Creature):
    def __init__(self, initial_pos): 
        Creature.__init__(self, initial_pos)
        self.foodValue = 5
        self.canvas_object = canvas.create_rectangle(initial_pos[0],
                                                        initial_pos[1],
                                                        initial_pos[0]+10,
                                                        initial_pos[1]+10, 
                                                        fill="green")

    def getEaten(self):
        if (self.foodValue > 0):
            self.foodValue -= 1
            if (self.foodValue == 0):
                # if we only call this function while holding the lock do we
                # need to care here?
                with plant_lock:
                    plants.remove(self)
                canvas.delete(self.canvas_object)
                canvas.update()
            return True
        else:
            return False


def main():
    # if we move this stuff to be global variables we can get rid of each creature
    # having its own representation of canvas internally

    all_initial_pos = set()
    n_rabbits = 10
    n_plants = 10
    n_foxes = 10
    total_moves = 20
            
    def initialize_start_positions(creatures, n_creatures, creature_class):
            for _ in range(n_creatures): 
                initial_pos = [random.randint(0, canvas_width-1), random.randint(0, canvas_height-1)]
                while tuple(initial_pos) in all_initial_pos:
                    initial_pos = [random.randint(0, canvas_width-1), random.randint(0, canvas_height-1)]
                all_initial_pos.add(tuple(initial_pos))

                # print(initial_pos)
                if creature_class == Plant:
                    creature = creature_class(initial_pos)
                else:
                    creature = creature_class(initial_pos, total_moves)
                creatures.append(creature)

    initialize_start_positions(foxes, n_foxes, Fox)
    initialize_start_positions(rabbits, n_rabbits, Rabbit)
    initialize_start_positions(plants, n_plants, Plant)

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