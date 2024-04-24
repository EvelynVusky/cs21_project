import random
import math
from global_stuff import *



def _mutateValue(value, rate, min_val, max_val):
    newValue = value * (1 - random.uniform(-rate, rate))
    return clamp(newValue, min_val, max_val)

def _mutateColor(value, rate, min_val, max_val):
    newValue = value * (1 - random.uniform(-rate, rate))
    return clamp(newValue, min_val, max_val)

# this needs to be a different function because these values are linked
# when speed increases efficency should decrease and vice versa
# also I didn't add allow min/max parameters because that's a lot of params
def _mutateEnergyBudget(metabolism, stomachSize, speed, rate):
    m = random.uniform(-rate, rate)
    sChange = (1 - m)
    eChange = (1 + m)
    metabolism = clamp(metabolism * eChange, 0, 300)
    stomachSize = clamp(stomachSize * eChange, 0, 1000)
    speed = clamp(speed * sChange, 0, 10)
    return metabolism, stomachSize, speed

class Gene:
    def __init__(self, startingGenes):
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

    def childGene(self):
        m = self.mutationRate
        meta, ssize, speed = _mutateEnergyBudget(self.metabolism, self.stomachSize, self.speed, m)
        # meta = self.metabolism
        # ssize = self.stomachSize
        # speed = self.speed
        rate = self.reproduceRate
        cutoff = self.reproduceCutoff
        fear = _mutateValue(self.fearFactor, m, 0, 100)
        hunger = _mutateValue(self.hungerFactor, m, 0, 100)
        avoid = _mutateValue(self.avoidOthersFactor, m, 0, 100)
        r, g, b = self.color
        color = (_mutateValue(r, 0.5, 0, 255), _mutateValue(g, 0.5, 0, 255), _mutateValue(b, 0.5, 0, 255))
        #print(speed)
        health = _mutateValue(r, m, 0, cutoff)
        return Gene([m, meta, ssize, speed, rate, cutoff, fear, hunger, avoid, color, health])
        