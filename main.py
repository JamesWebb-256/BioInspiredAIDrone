import pygame
import random
import os
import time
import neat
import pickle
from math import sin, cos, tan, radians, atan2, degrees

pygame.font.init()  # init font

WIN_WIDTH = 1200
WIN_HEIGHT = 600
STAT_FONT = pygame.font.SysFont("comicsans", 50)
END_FONT = pygame.font.SysFont("comicsans", 70)
DRAW_LINES = False

WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Cave Explorer")

gen = 0

drone_images = [pygame.transform.scale(pygame.image.load(os.path.join("imgs", "blue_drone.png")), (20, 20))]
bg_img = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "background.png")), (WIN_WIDTH, WIN_HEIGHT))

ceil_imgs = [pygame.transform.scale(pygame.image.load(os.path.join("imgs", "ceil_1.png")), (WIN_WIDTH, 100)),
             pygame.transform.rotate(
                 pygame.transform.scale(pygame.image.load(os.path.join("imgs", "ceil_1.png")), (WIN_WIDTH, 100)), -180)]

cave_imgs = [pygame.transform.scale(pygame.image.load(os.path.join("imgs", "cave_1.png")), (WIN_WIDTH, WIN_HEIGHT))]

# =================== Drone Specs ==================================

DRONE_DBG = False
MAX_VEL = 100
MAX_VEL_REDUCTION = 1  # at the start reduce maximum speed
ACC_STRENGTH = 1
BRAKE_STRENGTH = 1
TURN_VEL = 2
SENSOR_DISTANCE = 200
ACTIVATION_THRESHOLD = 0.5


# ========= Surroundings =========
class Cave:
    IMG = cave_imgs[0]

    def __init__(self, y):
        self.y = y
        self.x = 0

    def draw(self, win):
        win.blit(self.IMG, (self.x, self.y))


class Floor:
    IMG = ceil_imgs[1]

    def __init__(self, y):
        self.y = y
        self.x = 0

    def draw(self, win):
        win.blit(self.IMG, (self.x, self.y))


class Ceil:
    """
    Represnts the moving floor of the game
    """
    IMG = ceil_imgs[0]

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
# ========= End of Surroundings =========


# ========= Drones =========
class Drone:

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vel = 0
        self.img = drone_images[0]
        self.acc = 0
        self.commands = [0, 0]

        self.hori = 0  # Forward
        self.vert = 0  # Right-ward

    def collision(self, obstacle):
        """
        gets the mask for the current image of the drone
        """
        obstacle_mask = pygame.mask.from_surface(obstacle.IMG)
        drone_mask = pygame.mask.from_surface(self.img)
        offset = (self.x - obstacle.x, self.y - round(obstacle.y))

        b_point = obstacle_mask.overlap(drone_mask, offset)  # Should be a boolean

        return b_point

    def sensors(self):
        pass

    def move(self):

        # command[0] controls the movement forward and backwards from value [-1, 1]
        # command[1] controls the movement sideways from value [-1, 1]

        if self.commands[0] > ACTIVATION_THRESHOLD or self.commands[0] < (- ACTIVATION_THRESHOLD):  # If going forward/backwards
            self.vert = self.commands[0] * ACC_STRENGTH

        if self.commands[1] > ACTIVATION_THRESHOLD or self.commands[1] < (- ACTIVATION_THRESHOLD):  # If going sideways
            self.hori = self.commands[1] * ACC_STRENGTH

        if self.vert > MAX_VEL:
            self.vert = MAX_VEL
        if self.hori > MAX_VEL:
            self.hori = MAX_VEL

        self.x = self.x + self.hori
        self.y = self.y - self.vert  # I subtract because the origin is top left

        return self.x, self.y

    # ======================== LOCAL FUNCTIONS ==========================

    # ----


def draw_window(win, drones, ceil, floor, cave):
    win.blit(bg_img, (0, 0))
    floor.draw(win)
    ceil.draw(win)
    cave.draw(win)

    # base.draw(win)
    for drone in drones:
        # draw lines from bird to pipe
        # if DRAW_LINES:
        #     try:
        #         pygame.draw.line(win, (255, 0, 0),
        #                          (bird.x + bird.img.get_width() / 2, bird.y + bird.img.get_height() / 2),
        #                          (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width() / 2, pipes[pipe_ind].height),
        #                          5)
        #         pygame.draw.line(win, (255, 0, 0),
        #                          (bird.x + bird.img.get_width() / 2, bird.y + bird.img.get_height() / 2), (
        #                              pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width() / 2,
        #                              pipes[pipe_ind].bottom), 5)
        #     except:
        #         pass
        # draw bird
        win.blit(drone.img, (drone.x, drone.y))

    # # score
    # score_label = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    # win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))
    #
    # # generations
    # score_label = STAT_FONT.render("Gens: " + str(gen - 1), 1, (255, 255, 255))
    # win.blit(score_label, (10, 10))
    #
    # # alive
    # score_label = STAT_FONT.render("Alive: " + str(len(birds)), 1, (255, 255, 255))
    # win.blit(score_label, (10, 50))

    pygame.display.update()


def eval_genomes(genomes, config):
    """
    runs the simulation of the current population of
    drones and sets their fitness based on the distance they
    reach in the game.
    """
    global WIN, gen
    win = WIN
    gen += 1

    # start by creating lists holding the genome itself, the
    # neural network associated with the genome and the
    # bird object that uses that network to play
    nets = []
    drones = []
    ge = []
    for genome_id, genome in genomes:
        genome.fitness = 0  # start with fitness level of 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        drones.append(Drone(50, 50))
        ge.append(genome)

    ceiling = Ceil(0)
    floor = Floor(500)
    cave = Cave(0)

    score = 0

    clock = pygame.time.Clock()

    run = True
    while run and len(drones) > 0:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        for x, drone in enumerate(drones):  # give each bird a fitness of 0.1 for each frame it stays alive
            ge[x].fitness += 0.1

            # send bird location, top pipe location and bottom pipe location and determine from network whether to jump
            # or not
            drone.commands = nets[drones.index(drone)].activate((drone.x, drone.y))

            (x, y) = drone.move()

        for drone in drones:
            if drone.collision(ceiling) or drone.collision(floor) or drone.collision(cave):
                nets.pop(drones.index(drone))
                ge.pop(drones.index(drone))
                drones.pop(drones.index(drone))

            if drone.y > WIN_HEIGHT or drone.y < 0 or drone.x < 0 or drone.x > WIN_WIDTH:
                nets.pop(drones.index(drone))
                ge.pop(drones.index(drone))
                drones.pop(drones.index(drone))

        draw_window(WIN, drones, ceiling, floor, cave)


def run(config_file):
    """
    runs the NEAT algorithm to train a neural network to play flappy bird.
    :param config_file: location of config file
    :return: None
    """
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # Run for up to 50 generations.
    winner = p.run(eval_genomes, 50)

    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))


if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)
    # running = True
    # drones = [Drone(50, 50)]
    # ceil = Ceil(0)
    # floor = Floor(500)
    # cave = Cave(0)
    # while running:
    #     draw_window(WIN, drones, ceil, floor, cave)
