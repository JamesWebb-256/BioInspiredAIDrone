import numpy as np
import pygame
import os

cave_images = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "ceil_1.png")).convert_alpha())]


class cave():
    """
    Represnts the moving floor of the game
    """
    IMG = cave_images[0]

    def __init__(self, y):
        """
        Initialize the object
        :param y: int
        :return: None
        """
        self.y = y
        self.x = 0

    def draw(self, win):
        """
        Draw the floor. This is two images that move together.
        :param win: the pygame surface/window
        :return: None
        """
        win.blit(self.IMG, (self.x, self.y))
        pygame.display.update()
