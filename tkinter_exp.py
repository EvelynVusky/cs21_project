import tkinter as tk
import threading
from time import sleep
import random
import math
from global_stuff import *
from creature import *
from gene import *
import sys

def draw_count(creature_name):
    """
    Draws a stats box on the canvas.

    Args:
    - creature_name (str): name of species stat box to draw on canvas

    Returns:
    - tuple: A tuple containing IDs of the rectangle and text objects created.

    """
    if (creature_name == "plant") :
        string = "PLANTS\n" \
                    + "population: " + str(len(plants))
        frac_of_screen_x1 = 0
        frac_of_screen_x2 = 1 / 3
        color = plant_color
    elif (creature_name == "rabbit") :
        string = "RABBITS\n" \
                        + "population: " + str(len(rabbits)) \
                        + "\n avg speed: " + str(rabbitSpeed) \
                        + "\n avg health: " + str(get_avg_rabbit_health())
        frac_of_screen_x1 = 1 / 3
        frac_of_screen_x2 = 2 / 3
        color = rabbit_color
    else : 
        string = "FOXES\n" \
                + "population: " + str(len(foxes))
        frac_of_screen_x1 = 2 / 3
        frac_of_screen_x2 = 1
        color = fox_color
    
    x1 = canvas_width * frac_of_screen_x1
    x2 = canvas_width * frac_of_screen_x2
    y1 = 0
    y2 = stat_height
    square = canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
    text = canvas.create_text((x1 + x2) / 2,
                              (y1 + y2) / 2,
                              text=str(string),
                              fill="black",
                              font=("Arial", int(stat_height/6)))
    return square, text


def get_avg_rabbit_health():
    """
    Calculates average health for rabbits.

    If there are rabbits present, calculates the average health
    of all rabbits. Otherwise, returns 0 as default average health.

    Returns:
    - An int representing the average health of rabbits. If there are no 
        rabbits, returns 0.

    """
    if (len(rabbits) > 0):
        health = [getattr(rabbit, 'health', None) for rabbit in rabbits]
        return sum(health) // len(health)   
    return 0

def update_count(plant_cnt, rabbit_cnt, fox_cnt): 
    """
    Updates the count display for plants, rabbits, and foxes on the canvas.

    Retrieves statistics for rabbits, constructs strings representing the 
    population and average attributes for plants, rabbits, and foxes, 
    updates the count labels on the canvas, and schedules the next update.

    """
    plant_stats = "PLANTS\n" \
                    + "population: " + str(len(plants))
    rabbit_stats = "RABBITS\n" \
                + "population: " + str(len(rabbits)) \
                + "\n avg speed: " + str(stats_collector.average_rabbit_speed) \
                + "\n avg health: " + str(get_avg_rabbit_health())
    fox_stats = "FOXES\n" \
                + "population: " + str(len(foxes))

    canvas.itemconfig(plant_cnt, text=plant_stats)
    canvas.itemconfig(rabbit_cnt, text=rabbit_stats)
    canvas.itemconfig(fox_cnt, text=fox_stats)

    global after_id
    after_id = canvas.after(1000, update_count, plant_cnt, rabbit_cnt, fox_cnt)

    if sim_done:
        canvas.after_cancel(after_id)

def listen_to_user_input():
    """
    Listens to user input from the command line.

    If the user enters 'q', the function sets the global variable 'sim_done' to True,
    signals the 'sim_done_event', releases all semaphores in 'semList', and terminates.

    """
    global sim_done
    global semList
    while True:
        # Apparently tkinter and the input() function don't work together
        # when multi-threading so we used readline()
        user_input = sys.stdin.readline().strip()
        if user_input == "q":
            print("killing creatures")
            sim_done = True
            sim_done_event.set()
            with semListLock:
                for sem in semList:
                    sem.release()
                semList = []
            break

def main():
    """
    Main function for running the simulation.

    Initializes starting positions for creatures (foxes, rabbits, plants), 
    draw stats boxes for each population, updates count information, 
    starts input listener thread, starts threads for each creature type,
    runs the simulation, prints statistics, and outputs run data.

    """
    global stats_collector

    all_initial_pos = set()
            
    def initialize_start_positions(creatures, n_creatures, creature_class):
            for _ in range(n_creatures): 
                initial_pos = [random.randint(0, canvas_width-1), 
                                random.randint(stat_bottom, canvas_height-1)]
                while tuple(initial_pos) in all_initial_pos:
                    initial_pos = [random.randint(0, canvas_width-1), 
                                random.randint(stat_bottom, canvas_height-1)]
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

    ## draw stat boxes
    plant_square, plant_cnt = draw_count("plant")
    rabbit_square, rabbit_cnt = draw_count("rabbit")
    fox_square, fox_cnt = draw_count("fox")
    update_count(plant_cnt, rabbit_cnt, fox_cnt)

    input_thread = threading.Thread(target=listen_to_user_input)
    input_thread.start()

    for plant in plants:
        plant.start()

    for rabbit in rabbits:
        rabbit.start()

    for fox in foxes:
        fox.start()

    window.mainloop()

    stats_collector.print_stats()
    stats_collector.output_run_data()

    print("Simulation Completed.")



if __name__ == "__main__":
    main()