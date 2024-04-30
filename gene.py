import random
import math
from global_stuff import *



def _mutateValue(value, rate, min_val, max_val):
    """
    Mutates a value within a specified range.

    Args:
    - value (float): The original value.
    - rate (float): The mutation rate.
    - min_val (float): The minimum value allowed.
    - max_val (float): The maximum value allowed.

    Returns:
    - float: The mutated value.

    """
    newValue = value * (1 - random.uniform(-rate, rate))
    return clamp(newValue, min_val, max_val)

# this needs to be a different function because these values are linked
# when speed increases efficency should decrease and vice versa. This is to
# prevent speed from increasing without restriction through evolution.
# also I didn't add allow min/max parameters because that's a lot of params
def _mutateEnergyBudget(metabolism, stomachSize, speed, rate):
    """
    Mutates the energy budget parameters.

    Args:
    - metabolism (float): The metabolism parameter.
    - stomachSize (float): The stomach size parameter.
    - speed (float): The speed parameter.
    - rate (float): The mutation rate.

    Returns:
    - tuple: A tuple containing the mutated metabolism, stomach size,
    and speed parameters.

    """
    m = random.uniform(-rate, rate)
    # when speed increases, metabolism decreases and vice versa
    sChange = (1 - m)
    eChange = (1 + (5*m))
    metabolism = clamp(metabolism * eChange, 0, 3000)
    stomachSize = clamp(stomachSize * eChange, 0, 10000)
    speed = clamp(speed * sChange, 0, 1.9)
    return metabolism, stomachSize, speed

class Gene:
    def __init__(self, startingGenes):
        """
        Initializes a Gene class object

        """
        # We take in an array of starting genetics. This is effectivly the
        # genome of the rabbit
        self.mutationRate = startingGenes[0]
        self.metabolism = startingGenes[1]
        self.stomachSize = startingGenes[2]
        self.speed = startingGenes[3]
        self.reproduceRate = startingGenes[4]
        self.reproduceCutoff = startingGenes[5]
        self.fearFactor = startingGenes[6]
        self.hungerFactor = startingGenes[7]
        self.avoidOthersFactor = startingGenes[8]
        self.color = startingGenes[9]
        self.startingHealth = startingGenes[10]
        self.generation = startingGenes[11]

    def childGene(self):
        """
        Generates a child gene by mutating the current gene.

        Returns:
        - Gene: The child gene.

        """
        m = self.mutationRate
        meta, ssize, speed = _mutateEnergyBudget(self.metabolism,
                                                 self.stomachSize,
                                                 self.speed, m)
        rate = self.reproduceRate
        cutoff = self.reproduceCutoff
        fear = _mutateValue(self.fearFactor, m, 0, 100)
        hunger = _mutateValue(self.hungerFactor, m, 0, 100)
        avoid = _mutateValue(self.avoidOthersFactor, m, 0, 100)
        r, g, b = self.color
        color = (_mutateValue(r, 0.5, 0, 255), _mutateValue(g, 0.5, 0, 255),
                 _mutateValue(b, 0.5, 0, 255))
        # the starting health can't exceed the reproduction cutoff of the
        # parent. This prevents parents from giving birth to too large
        # children
        health = _mutateValue(r, m, 0, cutoff)
        generation = self.generation + 1
        # generate the array of genes for the child
        return Gene([m, meta, ssize, speed, rate, cutoff, fear,
                     hunger, avoid, color, health, generation])
        