import tkinter as tk
import threading
import argparse

def clamp(value, min_val, max_val):
    return max(min(value, max_val), min_val)

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

n_plants = args.plants
n_rabbits = args.rabbits
n_foxes = args.foxes


# Simulation Parameters
health = 200 # starting health of rabbits and foxes

# Plant info
foodValue = 1 # number of times food can be eated before destruction
plantRate = 0.015 # likelyhood that any plant will reproduce each time step
maxPlants = 500 # max number of plants
minPlantDistance = 30 # minimum distance plants must be from each other
maxPlantDistance = 500 # maximum distance plants can be from their parent

# rabbit info
rabbitMetabolism = 50 # amount of health that rabbits get back per food
rabbitStomachSize = 300 # max amount of health a rabbit can have
rabbitSpeed = 1
rabbitRate = 0.008 # likelyhood that any healthy rabbit will reproduce each time step
fearFactor = 0.5
maxRabbits = 100 # max number of plants
minRabbitDistance = 30 # minimum distance plants must be from each other
maxRabbitDistance = 50 # maximum distance plants can be from their parent

# fox info
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

window = tk.Tk() 
window.title("Foxes, Rabbits, & Plants Simulation")
canvas = tk.Canvas(window, width=canvas_width, height=canvas_height, bg="white")
canvas.pack()

canvas_lock = threading.Lock()

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