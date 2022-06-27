

import math


def clamp(val:float, min:float, max:float):
    
    return min if val < min else max if val > max else val
