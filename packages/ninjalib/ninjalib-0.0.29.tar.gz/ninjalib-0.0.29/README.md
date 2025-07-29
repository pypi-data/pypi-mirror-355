# ninjalib is a data science library
# 
# import ninjalib
# center = ninjalib.ninjalib(data).center()
# flatten = ninjalib.ninjalib(data,nth=0).flatten()
# gravity = ninjalib.ninjalib(grams,meters).gravity()
# mean = ninjalib.ninjalib(data).mean()
# project = ninjalib.ninjalib(focal_length,x,y,z).project()
# 
# NOTES:
# center expects a 2D list/tuple of 2D OR 3D vertices. It will also accept a 1D list/tuple of floats and/or ints. Returns the center of the line, 2D, or 3D shape.
# flatten: list or tuple expected; flatten nth times. returns a flattened array. If nth is left blank, it will flatten to a 1D list.
# gravity: expects int or float. Returns the gravitational pull of an object with mass in grams and diameter in meters.
# mean = list or tuple expected. Returns the mean of a tuple or list.
# project = expects floats and/or ints. Returns the projected 3D coordinates on a 2D plane.
