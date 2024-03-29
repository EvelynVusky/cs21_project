import tkinter as tk
import threading
from time import sleep
import random
import sys
import math

canvas_height = 500
canvas_width = 500
movement_height = 300 ## subcanvas within rabbits are spawned
movement_width = 300 ## subcanvas within rabbits are spawned
canvas_lock = threading.Lock()
rabbit_lock = threading.Lock()
plant_lock = threading.Lock()
rabbits = []
plants = []


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

class Rabbit(Creature, threading.Thread):    
    def __init__(self, initial_pos, total_moves, canvas): 
        Creature.__init__(self, initial_pos)
        threading.Thread.__init__(self)
        self.size_step = 10
        self.total_moves = total_moves
        self.canvas = canvas
        self.canvas_object = self.canvas.create_oval(initial_pos[0],
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

    def run(self): 
        while self.total_moves > 0:
            new_col, new_row, dx, dy, food = self.moveTowardsClosestFood()
            if (not food): break
            self.position[0], self.position[1] = new_col, new_row
            with canvas_lock:
                # new_col, new_row, dx, dy = self.generate_position()
                # while(not check_bounds(new_col, new_row)):
                #     new_col, new_row, dx, dy = (self.generate_position())

                if ((self.getDistanceTo(food) < 1) and food.getEaten()):
                    # alternativly we could make this setting the value instead of increasing
                    self.total_moves += 10

                self.canvas.move(self.canvas_object, dx, dy)
                self.canvas.update()

            self.total_moves -= 1
            # print(self.total_moves)
            sleep(1)
            # Some kind of barrier here to prevent rabbits from taking more
            # than one "turn" before other rabbits due to thread sleep
            # print("rabbit moved")
        with rabbit_lock:
                rabbits.remove(self)
        with canvas_lock:
            self.canvas.delete(self.canvas_object)
            self.canvas.update()
        print("rabbit is done")

class Plant(Creature):
    def __init__(self, initial_pos, canvas): 
        Creature.__init__(self, initial_pos)
        self.canvas = canvas
        self.foodValue = 5
        self.canvas_object = self.canvas.create_rectangle(initial_pos[0],
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
                self.canvas.delete(self.canvas_object)
                self.canvas.update()
            return True
        else:
            return False


def main():
    # if we move this stuff to be global variables we can get rid of each creature
    # having its own representation of canvas internally
    window = tk.Tk() 
    window.title("Rabbits + Plants Simulation")
    canvas = tk.Canvas(window, width=canvas_width, height=canvas_height, bg="white")
    canvas.pack()

    n_rabbits = 10
    n_plants = 10
    total_moves = 20
            
    for _ in range(n_rabbits): 
        initial_pos = [random.randint(0, movement_width-1), random.randint(0, movement_height-1)]
        # print(initial_pos)
        rabbit = Rabbit(initial_pos, total_moves, canvas)
        rabbits.append(rabbit)

    for _ in range(n_plants): 
        initial_pos = [random.randint(0, canvas_width-1), random.randint(0, canvas_height-1)]
        plant = Plant(initial_pos, canvas)
        plants.append(plant)

    for rabbit in rabbits:
        rabbit.start()
    
    window.mainloop() ## this must be between the .start() and .join() function calls
    window.quit()

    for rabbit in rabbits: 
        rabbit.join()


    # this does not print for some reason?
    print("Simulation Completed.")


if __name__ == "__main__":
    main()