import numpy as np
import pygame

TIME_DELAY = 0.001
# TIME_DELAY = 1


# This class defines the drone itself.
# velocity: 2d array of the forces acting in each dimension. We'll keep it 2d for now but only change the y axis.
# force: Forces acting on the drone. This will be updated as (rotor force - 9.8*mass)
# mass: Mass of the drone in kg; lets have it be 50g for now.
# position: Pretty self evident
# radius: Assume a spherical drone
# color: can be whatever
#
class Drone:
    def __init__(self, position_array, colour, radius=10):
        self.velocity = np.array([[0, 0]])
        self.force = np.array([[0, 9.8]])
        self.mass = 1
        self.position = position_array
        self.radius = radius
        self.colour = colour
        self.RotorsOn = False
        self.RotorForce = 15

    # Function to draw the drone on the area (Doesn't need to be called when fully training)
    def draw(self, surface):
        surface.fill((0, 0, 0))
        pygame.draw.circle(surface, self.colour, (self.position[0][0],
                           self.position[0][1]), self.radius)
        pygame.display.update()

    # Update velocity with velocity_array, which will be calculated from the forces.
    def add_velocity(self, velocity_array):
        self.velocity = self.velocity + velocity_array

    # Update forces acting on drone with force_array, calculated from the drone's actions and gravity.
    def add_force(self, force_array):
        self.force = self.force + force_array

    # Update position and velocity
    def move(self):
        self.velocity = self.velocity + ((self.force / self.mass) * TIME_DELAY)
        self.position = self.position + self.velocity * TIME_DELAY
