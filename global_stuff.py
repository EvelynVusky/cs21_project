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

parser.add_argument('--plants', metavar='PLANTS', type=lambda x: capped_int(x, 400), default=200,
                    help='Number of plants at the start of the simulation; Max number of foxes to start with is 400')
parser.add_argument('--rabbits', metavar='RABBITS', type=lambda x: capped_int(x, 300), default=100,
                    help='Number of rabbits at the start of the simulation; Max number of rabbits to start with is 300')
parser.add_argument('--foxes', metavar='FOXES', type=lambda x: capped_int(x, 300), default=0,
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
plantRate = 0.1 # likelyhood that any plant will reproduce each time step
maxPlants = 500 # max number of plants
minPlantDistance = 30 # minimum distance plants must be from each other
maxPlantDistance = 6000 # maximum distance plants can be from their parent

# rabbit info
rabbitMetabolism = 60 # amount of health that rabbits get back per food
rabbitStomachSize = 400 # max amount of health a rabbit can have
rabbitSpeed = 1.2
rabbitRate = 0.003 # likelyhood that any healthy rabbit will reproduce each time step
rabbitReproductionCutoff = 100
fearFactor = 0.75
maxRabbits = 150 # max number of rabbits
minRabbitDistance = 30 # minimum distance rabbits must be from each other
maxRabbitDistance = 50 # maximum distance rabbits can be from their parent

# fox info
foxMetabolism = 50 # amount of health that fox get back per food
foxStomachSize = 350 # max amount of health a fox can have
foxSpeed = 2
foxRate = 0.001 # likelyhood that any healthy fox will reproduce each time step
foxReproductionCutoff = 100
avoidOthers = 0.3
maxFoxes = 50 # max number of foxes
minFoxDistance = 30 # minimum distance foxes must be from each other
maxFoxDistance = 50 # maximum distance foxes can be from their parent

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
    if col < 1 or col > canvas_width:
        return False
    elif row < 1 or row > canvas_height:
        return False
    else:
        return True