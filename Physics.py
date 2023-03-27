import numpy as np


# Function ot find the magnitude of a 2d vector
def _mag(arr):
    return np.sqrt(arr[0] ** 2 + arr[1] ** 2)


def _unit_vec(arr):
    mag = _mag(arr)
    return np.array([
        arr[0] / mag,
        arr[1] / mag
    ])


class PhysicsEngine:
    def __init__(self):
        self.body_pos_array = np.array([]).reshape((0, 2))
        self.body_list = None

    def compute_force_vectors(self):
        pass
