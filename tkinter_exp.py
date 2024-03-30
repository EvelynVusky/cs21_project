import tkinter as tk
import threading
from time import sleep
import random
import sys

canvas_height = 500
canvas_width = 500
movement_height = 300 ## subcanvas within rabbits/foxes are spawned
movement_width = 300 ## subcanvas within rabbits/foxes are spawned
canvas_lock = threading.Lock()

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

    def run(self): 
        while self.total_moves > 0:
            with canvas_lock:
                new_col, new_row, dx, dy = self.generate_position()
                while(not check_bounds(new_col, new_row)):
                    new_col, new_row, dx, dy = (self.generate_position())
                self.position[0], self.position[1] = new_col, new_row

                self.canvas.move(self.canvas_object, dx, dy)
                self.canvas.update()
                # print(self.position)

            self.total_moves -= 1
            sleep(1)
            # print("rabbit moved")
        print("fox is done")


class Rabbit(Creature, threading.Thread):    
    def __init__(self, initial_pos, total_moves, canvas): 
        Creature.__init__(self, initial_pos)
        threading.Thread.__init__(self)
        self.size_step = 10
        self.total_moves = total_moves
        self.canvas = canvas
        self.canvas_object = self.canvas.create_oval(initial_pos[0],
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

    def run(self): 
        while self.total_moves > 0:
            with canvas_lock:
                new_col, new_row, dx, dy = self.generate_position()
                while(not check_bounds(new_col, new_row)):
                    new_col, new_row, dx, dy = (self.generate_position())
                self.position[0], self.position[1] = new_col, new_row

                self.canvas.move(self.canvas_object, dx, dy)
                self.canvas.update()
                # print(self.position)

            self.total_moves -= 1
            sleep(1)
            # print("rabbit moved")
        print("rabbit is done")


class Plant(Creature):
    def __init__(self, initial_pos, canvas): 
        Creature.__init__(self, initial_pos)
        self.canvas = canvas
        self.canvas_object = self.canvas.create_rectangle(initial_pos[0],
                                                        initial_pos[1],
                                                        initial_pos[0]+10,
                                                        initial_pos[1]+10, 
                                                        fill="green")


def main():
    window = tk.Tk() 
    window.title("Rabbits + Plants Simulation")
    canvas = tk.Canvas(window, width=canvas_width, height=canvas_height, bg="white")
    canvas.pack()

    all_initial_pos = set()
    foxes, n_foxes = [], 10
    rabbits, n_rabbits = [], 10
    plants, n_plants = [], 10
    total_moves = 10

    #intialize start positions for all creatures, no two creatures should have
    #the same start position
    def initialize_start_positions(creatures, n_creatures, creature_class):
            for _ in range(n_creatures): 
                initial_pos = [random.randint(0, movement_width-1), random.randint(0, movement_height-1)]
                while tuple(initial_pos) in all_initial_pos:
                    initial_pos = [random.randint(0, movement_width-1), random.randint(0, movement_height-1)]
                all_initial_pos.add(tuple(initial_pos))

                # print(initial_pos)
                if creature_class == Plant:
                    creature = creature_class(initial_pos, canvas)
                else:
                    creature = creature_class(initial_pos, total_moves, canvas)
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