import tkinter as tk
import threading
import math
import argparse
from stats_collector import *


###################### Helper Functions ######################

def clamp(value, min_val, max_val):
    return max(min(value, max_val), min_val)

def rgb_to_hex(rgb):
    r, g, b  = rgb
    return f'#{int(r):02x}{int(g):02x}{int(b):02x}'

def normalize_vector(x, y):
    """
    Normalizes a 2D vector.

    Args:
    - x (float): The x-component of the vector.
    - y (float): The y-component of the vector.

    Returns:
    - tuple: A tuple containing the normalized x-component,
    normalized y-component, and the magnitude of the original vector.

    """
    magnitude = math.sqrt(x**2 + y**2)
    if magnitude == 0:
        return (0, 0, 0)  # To avoid division by zero
    else:
        normalized_x = x / magnitude
        normalized_y = y / magnitude
        return (normalized_x, normalized_y, magnitude)

def check_bounds(col, row): 
    """
    Checks if a given column and row are within the bounds of the canvas.

    Args:
    - col (int): Column value.
    - row (int): Row value.

    Returns:
    - bool: True if the column and row are within the bounds, False otherwise.

    """
    if col < 1 or col > canvas_width:
        return False
    elif row < count_bottom or row > canvas_height:
        return False
    else:
        return True

def capped_int(value, cap):
    """
    Converts a value to an integer and checks if it is within a specified
    limit.

    Args:
    - value: The value to convert and check.
    - cap: The upper limit.

    Returns:
    - int: The value as an integer if it is within the limit.

    Raises:
    - argparse.ArgumentTypeError: If the value is not a positive integer
    or exceeds the limit.

    """
    ivalue = int(value)

    if ivalue <= 0:
        raise argparse.ArgumentTypeError("%s is an invalid int value" % value)
    elif ivalue > cap:
        raise argparse.ArgumentTypeError(
                            '''%s exceeds the limit of %s''' % (value, cap))
    
    return ivalue






###################### Argument Parsing ######################

parser = argparse.ArgumentParser(description=
                                    "Parse simulation start configurations.")

parser.add_argument('--plants', metavar='PLANTS', type=lambda x:
                                        capped_int(x, 400), default=200,
                    help="""Number of plants at the start of the simulation;
                            Max number of plants to start with is 400""")
parser.add_argument('--rabbits', metavar='RABBITS', type=lambda x:
                                        capped_int(x, 300), default=100,
                    help="""Number of rabbits at the start of the simulation;
                            Max number of rabbits to start with is 300""")
parser.add_argument('--foxes', metavar='FOXES', type=lambda x:
                                        capped_int(x, 300), default=0,
                    help="""Number of foxes at the start of the simulation;
                            Max number of foxes to start with is 300""")
parser.add_argument('--height', metavar='HEIGHT', type=lambda x:
                                        capped_int(x, 1000), default=500,
                    help='Height of the canvas; Max height is 1000')
parser.add_argument('--width', metavar='WIDTH', type=lambda x:
                                        capped_int(x, 1500), default=500,
                    help='Width of the canvas; Max width is 1500')

args = parser.parse_args()

n_plants = args.plants
n_rabbits = args.rabbits
n_foxes = args.foxes





###################### Simulation Parameters ######################

health = 200 # starting health of rabbits and foxes

# Plant info
foodValue = 1 # number of times food can be eated before destruction
plantRate = 0.13 # likelyhood that any plant will reproduce each time step
maxPlants = 500 # max number of plants
minPlantDistance = 30 # minimum distance plants must be from each other
maxPlantDistance = 6000 # maximum distance plants can be from their parent

# rabbit info
rabbitMutationRate = 0.2
rabbitMetabolism = 60 # amount of health that rabbits get back per food
rabbitStomachSize = 300 # max amount of health a rabbit can have
rabbitSpeed = 1.2
rabbitRate = 0.004 # likelyhood that any healthy rabbit will reproduce
rabbitReproductionCutoff = 100
fearFactor = 1
hungerFactor = 1
generation = 1
avoidOthersFactor = 0.1
rabbitRadius = 10
rabbitColor = (50, 50, 200)
rabbitHealth = 100
maxRabbits = 150 # max number of rabbits
minRabbitDistance = 30 # minimum distance rabbits must be from each other
maxRabbitDistance = 50 # maximum distance rabbits can be from their parent

rabbitStartingGenes = [rabbitMutationRate, rabbitMetabolism,
                        rabbitStomachSize, rabbitSpeed, rabbitRate,
                        rabbitReproductionCutoff, fearFactor, hungerFactor,
                        avoidOthersFactor, rabbitColor, rabbitHealth,
                        generation]

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





###################### Stat Block Information ######################

canvas_height = args.height
canvas_width = args.width
count_height = int(canvas_height * .1)
count_bottom = int(count_height + 10) # y-coord of bottom count boxes
fox_color = "#ff8585"
rabbit_color = "#7c9feb"
plant_color = "#91c795"





###################### Tkinter Canvas Info ######################

window = tk.Tk() 
window.title("Foxes, Rabbits, & Plants Simulation")
canvas = tk.Canvas(window, width=canvas_width,
                           height=canvas_height,
                           bg="white")
canvas.pack()

canvas_lock = threading.Lock()




###################### Global Shared Information ######################

rabbits = []
plants = []
foxes = []

rabbit_lock = threading.Lock()
plant_lock = threading.Lock()
fox_lock = threading.Lock()

semList = []
semListLock = threading.Lock()

sim_done = False
sim_done_event = threading.Event()

stats_collector = StatsCollector(n_plants, n_plants, n_foxes,
                                 rabbitSpeed, fearFactor, hungerFactor)