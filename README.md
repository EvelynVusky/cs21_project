MAMMAL MANAGMENT

---------------- Overview ----------------
This project is a simulation of a ecosystem consisting of foxes, rabbits, and
plants. It uses concurrent programming techniques to process each as their
own thread. 


---------------- Features ----------------
- complex creature behaviors to seek food and flee predators
- evolution of rabbits within the simulation
- thread synchronization
- comprehenzive simulation data collection
- gui elements to view the simulation


---------------- Installation/Setup ----------------
1. Install Tkinter
    macOS: $ sudo apt-get install python3-tk
    Windows: $ pip install tk
2. Install Python (At minimum, Python 3.11 should be installed)
    Follow the directions on the offical Python website:
    https://www.python.org/downloads/
3. Clone the project
    $ git clone https://github.com/EvelynVusky/cs21_project.git
    $ cd cs21_project


---------------- Usage ----------------
$ python3 tkinter_exp.py [-h] [--plants PLANTS] [--rabbits RABBITS]
[--foxes FOXES] [--height HEIGHT] [--width WIDTH]

-h: shows the help information
--plants: sets the starting number of plants in the simulation
--rabbits: sets the starting number of rabbits in the simulation
--foxes: sets the starting number of foxes in the simulatiom
--height: sets the height of simulation in pixels
--width: sets the width of simulation in pixels

For example: python3 simulation.py --height 1000 --width 1500 --foxes 5


---------------- Additional Config ----------------
All of the stats which control the creatures behavior are in the file
"global_stuff.py" under the simulation parameters section and can be changed
to change how the creatures behave. 


---------------- File Overview ----------------

creature.py: defines the Creature class as well as the Plant, Rabbit and Fox
classes which each inherit from Creature. This file controls basically all of
the behavior for the creatures in the simulation. This file is used by any file
which needs to know about Creatures (simulation.py and stats_collector.py)

gene.py: defines the Gene class which is used to implement random mutation when
creatures (just rabbits for now) reproduce. 

global_stuff.py: handles argument parsing, defines global helper functions,
defines simulation starting parameters and creates global shared information to
allow threads to communicate. Most other files import everything from this
file.

output.csv: created by the stats_collector and lists the population trend over
time. The first column is the timestamp, then followed by plant, rabbit, and
fox population size in that order

README.md (this file): contains essential program documentation

simulation.py: is the main file of the program. It is responsible for drawing
the screen and showing the correct stats while the simulation is running. It
also spawns all of the threads including a listener to tell the program when
to stop

stats_collector.py: defines the StatCollector class which is responsible for
logging reported events and aggregating statistics about the simulation as it
runs. It then outputs a report of the population over time to output.csv


---------------- Contributors ----------------
Rusny Rahman
Charlie Bohnsack
Evelyn Vu
