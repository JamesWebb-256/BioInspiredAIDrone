import numpy as np
import pygame

display = pygame.display.set_mode((1200, 600))
pygame.init()
from cave import cave
from Drone import *
# from Physics import *

from pygame.locals import (
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)

Drone = Drone(np.array([[100, 100]]), (255, 255, 255), 10)

cave = cave(10)

Drone.draw(display)
cave.draw(display)
running = True

while running:
    ev = pygame.event.get()

    for event in ev:
        pressed_keys = pygame.key.get_pressed()
        # if pressed_keys[K_UP]:

        if event.type == pygame.KEYDOWN:
            if event.key == K_UP:
                Drone.RotorsOn = True
                Drone.force = np.array([[0, 9.8 - 30]])

        if event.type == pygame.KEYUP:
            if event.key == K_UP:
                Drone.RotorsOn = False
                Drone.force = np.array([[0, 9.8]])

        if pressed_keys[K_UP]:
            Drone.move()
            Drone.draw(display)
            cave.draw(display)

        if event.type == pygame.QUIT:
            running = False
        cave.draw(display)
        pygame.display.flip()
    Drone.move()
    Drone.draw(display)
    cave.draw(display)
