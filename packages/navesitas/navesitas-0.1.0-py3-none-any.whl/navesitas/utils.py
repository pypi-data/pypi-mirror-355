from .naves import naves

def total_duration():

    return sum(nave.duration for nave in naves)
