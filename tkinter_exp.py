import tkinter as tk
import threading
from time import sleep
import random
import math
from global_stuff import *
from creature import *
from gene import *
import sys

def draw_count(x1, y1, x2, y2, color, number):
    square = canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
    text = canvas.create_text((x1 + x2) / 2,
                              (y1 + y2) / 2,
                              text=str(number),
                              fill="black",
                              font=("Arial", int(count_height/6)))
    return square, text

def draw_count(x1, y1, x2, y2, color, number):
    square = canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
    text = canvas.create_text((x1 + x2) / 2,
                              (y1 + y2) / 2,
                              text=str(number),
                              fill="black",
                              font=("Arial", int(count_height/6)))
    return square, text

def get_rabbit_stats():
    if (len(rabbits) > 0):
        stats = []
        speeds = [getattr(rabbit, 'size_step', None) for rabbit in rabbits]
        avg_speed = sum(speeds) // len(speeds)
        stats.append(avg_speed)

        health = [getattr(rabbit, 'health', None) for rabbit in rabbits]
        avg_health = sum(health) // len(health)   
        stats.append(avg_health)
    else: 
        stats = [0, 0]

    stats = [str(stat) for stat in stats]
    return stats

def update_count(plant_cnt, rabbit_cnt, fox_cnt): 
    ## get stats
    stats = get_rabbit_stats()
    plant_stats = "PLANTS\n" \
                    + "population: " + str(len(plants))
    rabbit_stats = "RABBITS\n" \
                    + "population: " + str(len(rabbits)) \
                    + "\n avg speed: " + str(stats_collector.average_rabbit_speed) \
                    + "\n avg health: " + stats[1]
    fox_stats = "FOXES\n" \
                + "population: " + str(len(foxes))

    canvas.itemconfig(plant_cnt, text=plant_stats)
    canvas.itemconfig(rabbit_cnt, text=rabbit_stats)
    canvas.itemconfig(fox_cnt, text=fox_stats)

    global after_id
    ## TODO: specify how long to update the counters?
    after_id = canvas.after(1000, update_count, plant_cnt, rabbit_cnt, fox_cnt)

    if sim_done:
        canvas.after_cancel(after_id)

def listen_to_user_input():
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
    global stats_collector

    all_initial_pos = set()
            
    def initialize_start_positions(creatures, n_creatures, creature_class):
            for _ in range(n_creatures): 
                initial_pos = [random.randint(0, canvas_width-1), random.randint(count_bottom, canvas_height-1)]
                while tuple(initial_pos) in all_initial_pos:
                    initial_pos = [random.randint(0, canvas_width-1), random.randint(count_bottom, canvas_height-1)]
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

    ## draw count boxes
    stats = get_rabbit_stats()
    plant_stats = "PLANTS\n" \
                    + "population: " + str(len(plants))
    rabbit_stats = "RABBITS\n" \
                    + "population: " + str(len(rabbits)) \
                    + "\n avg speed: " + str(rabbitSpeed) \
                    + "\n avg health: " + stats[1]
    fox_stats = "FOXES\n" \
                + "population: " + str(len(foxes))
    plant_square, plant_cnt = draw_count(0, 0, canvas_width / 3, count_height, plant_color, plant_stats)
    rabbit_square, rabbit_cnt = draw_count(canvas_width / 3, 0, canvas_width * 2 / 3, count_height, rabbit_color, rabbit_stats)
    fox_square, fox_cnt = draw_count(canvas_width * 2 / 3, 0, canvas_width+3, count_height, fox_color, fox_stats)

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