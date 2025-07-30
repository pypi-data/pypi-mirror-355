# rabbitpy/geometry.py

import math

def distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def midpoint(p1, p2):
    return [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2]

def vector(p1, p2):
    return [p2[0] - p1[0], p2[1] - p1[1]]

def normalize(v):
    d = math.hypot(v[0], v[1])
    return [v[0]/d, v[1]/d] if d != 0 else [0,0]

def angle_between(v1, v2):
    dot = v1[0]*v2[0] + v1[1]*v2[1]
    det = v1[0]*v2[1] - v1[1]*v2[0]
    return math.atan2(det, dot)
