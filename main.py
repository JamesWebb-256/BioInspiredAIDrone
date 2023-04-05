import pygame
import math
import random
import os
import time
import neat
import pickle
from math import sin, cos, tan, radians, atan2, degrees

pygame.font.init()  # init font

# =========== Variables to play around with ============
# =================== Drone Specs ==================================

DRONE_DBG = False
MAX_VEL = 200
ACC_STRENGTH = 2
BRAKE_STRENGTH = 2
SENSOR_DISTANCE = 200
ACTIVATION_THRESHOLD = 0.5

# =========== Recommend not changing these =============
WIN_WIDTH = 1200
WIN_HEIGHT = 600
STAT_FONT = pygame.font.SysFont("comicsans", 50)
END_FONT = pygame.font.SysFont("comicsans", 70)
DRAW_LINES = False

MAP_SIZE = (100, 100)


drone_height = 20
drone_width = 20

WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Cave Explorer")

OBSTACLE_COLOUR = (185, 122, 87)

gen = 0

drone_images = [pygame.transform.scale(pygame.image.load(os.path.join("imgs", "blue_drone.png")), (drone_width, drone_height))]
bg_img = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "background.png")), (WIN_WIDTH, WIN_HEIGHT))

ceil_imgs = [pygame.transform.scale(pygame.image.load(os.path.join("imgs", "ceil_1.png")), (WIN_WIDTH, 100)),
             pygame.transform.rotate(
                 pygame.transform.scale(pygame.image.load(os.path.join("imgs", "ceil_1.png")), (WIN_WIDTH, 100)), -180)]

cave_imgs = [pygame.transform.scale(pygame.image.load(os.path.join("imgs", "cave_1.png")), (WIN_WIDTH, WIN_HEIGHT))]

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

        self.hori = 0  # Right-ward
        self.vert = 0  # Downward

    def collision(self, obstacle):
        """
        gets the mask for the current image of the drone
        """
        obstacle_mask = pygame.mask.from_surface(obstacle.IMG)
        drone_mask = pygame.mask.from_surface(self.img)
        offset = (self.x - obstacle.x, self.y - round(obstacle.y))

        b_point = obstacle_mask.overlap(drone_mask, offset)  # Should be a boolean

        return b_point

    def move(self):

        # command[0] controls the movement forward and backwards from value [-1, 1]
        # command[1] controls the movement sideways from value [-1, 1]

        if self.commands[0] > ACTIVATION_THRESHOLD or self.commands[0] < (- ACTIVATION_THRESHOLD):  # If going
            # forward/backwards
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


# Sensor
class Sensor:
    def __init__(self, x, y, angle, sen_range):
        self.x = x
        self.y = y
        self.angle = angle
        self.range = sen_range

    def check_radar(self, win):
        length = 0
        end_x = round(self.x)
        end_y = round(self.y)

        # While We Don't Hit BORDER_COLOR AND length < 300 (just a max) -> go further and further
        while not win.get_at((end_x, end_y)) == OBSTACLE_COLOUR and length < self.range:
            length = length + 1
            end_x = int(self.x + math.cos(math.radians(self.angle)) * length)
            if end_x < 0 + 5:
                end_x = 0
            if end_x >= WIN_WIDTH - 5:
                end_x = WIN_WIDTH - 5

            end_y = int(self.y - math.sin(math.radians(self.angle)) * length)
            if end_y < 0 + 5:
                end_y = 0 + 5
            if end_y >= WIN_HEIGHT - 5:
                end_y = WIN_HEIGHT - 5

        # Calculate Distance To Border And Append To Radars List
        dist = int(math.sqrt(math.pow(end_x - self.x, 2) + math.pow(end_y - self.y, 2)))

        return dist

    def draw(self, surface):
        pygame.draw.line(surface, (250, 0, 0), (self.x, self.y), (
            self.x + math.cos(math.radians(self.angle)) * self.range,
            self.y - math.sin(math.radians(self.angle)) * self.range), 2)


# MAP
class Map:
    array = [[False for x in range(MAP_SIZE[0])] for y in range(MAP_SIZE[1])]
    cell_size = (WIN_WIDTH // MAP_SIZE[0], WIN_HEIGHT // MAP_SIZE[1])

    def __int__(self):
        self.array = [[False for x in range(MAP_SIZE[0])] for y in range(MAP_SIZE[1])]
        self.cell_size = (WIN_WIDTH // MAP_SIZE[0], WIN_HEIGHT // MAP_SIZE[1])


# ======================== LOCAL FUNCTIONS ==========================
def draw_window(win, drones, ceil, floor, cave, sensors):
    win.blit(bg_img, (0, 0))
    floor.draw(win)
    ceil.draw(win)
    cave.draw(win)

    # base.draw(win)
    for i, drone in enumerate(drones):
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

        for sensor in sensors[i]:
            sensor.draw(win)

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
    # drone object that uses that network to play
    nets = []
    drones = []
    ge = []
    sensors = []  # List of lists
    maps = []

    for genome_id, genome in genomes:
        genome.fitness = 0  # start with fitness level of 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)  # Define neural network for genome
        nets.append(net)  # Add network to list of networks
        drones.append(Drone(50, 50))  # Add a new drone to list of drones
        ge.append(genome)  # Add genome to list of genomes
        maps.append(Map)

    for _ in drones:
        drone_sensor_list = [Sensor(60, 60, 45 * sensor, 50) for sensor in range(8)]
        sensors.append(drone_sensor_list)  # Add list of sensors for each drone

    # Create all the obstacles in the map
    ceiling = Ceil(0)
    floor = Floor(500)
    cave = Cave(0)
    obstacles = [ceiling.IMG, floor.IMG, cave.IMG]

    start_time = pygame.time.get_ticks()  # Set for a time-limit for all the genomes

    clock = pygame.time.Clock()

    while len(drones) > 0:
        clock.tick(30)  # 30 frames per second (i think)

        for event in pygame.event.get():  # Set up so you can actually quit pygame
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        sensed_lists = [[0] * 8 for _ in drones]  # Set up the lists for the sensor output values
        for i, drone in enumerate(drones):
            ge[i].fitness += 0.1  # If it is still alive reward it for staying alive

            for j, sensor in enumerate(sensors[i]):
                sensor.x = drone.x + (drone_width / 2)
                sensor.y = drone.y + (drone_height / 2)
                dist = sensor.check_radar(win)  # Distance of an obstacle from the drone (Max value = 300)
                sensed_lists[i][j] = dist

            # Create a tuple for the input of the neural network
            inputs = (drone.x, drone.y, sensed_lists[i][0], sensed_lists[i][1], sensed_lists[i][2], sensed_lists[i][3],
                      sensed_lists[i][4], sensed_lists[i][5], sensed_lists[i][6], sensed_lists[i][7])

            drone.commands = nets[i].activate(inputs)  # Get the outputs of the neural network given the inputs

            (x, y) = drone.move()  # Move the drone

            map_x = int(x) // maps[i].cell_size[0]
            map_y = int(y) // maps[i].cell_size[1]
            if not maps[i].array[map_y][map_x]:
                maps[i].array[map_y][map_x] = True
                ge[i].fitness += 1

        for i, drone in enumerate(drones):
            # If it collides with anything, kill it.
            if drone.collision(ceiling) or drone.collision(floor) or drone.collision(cave) or \
                    drone.y > WIN_HEIGHT or drone.y < 0 or drone.x < 0 or drone.x > WIN_WIDTH:
                nets.pop(i)
                ge.pop(i)
                drones.pop(i)
        elapsed_time = pygame.time.get_ticks() - start_time
        if elapsed_time > 20000:  # 10 seconds time limit (in milliseconds)
            for i, drone in enumerate(drones):
                nets.pop(i)
                ge.pop(i)
                drones.pop(i)

        # # Draw the map
        # for y in range(MAP_SIZE[1]):
        #     for x in range(MAP_SIZE[0]):
        #         if map[y][x]:
        #             color = (0, 255, 0)  # Visited cells are green
        #         else:
        #             color = (255, 255, 255)  # Unvisited cells are white
        #         rect = pygame.Rect(x * cell_size[0], y * cell_size[1], cell_size[0], cell_size[1])
        #         pygame.draw.rect(WIN, color, rect)

        draw_window(WIN, drones, ceiling, floor, cave, sensors)


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
    winner = p.run(eval_genomes, 10)

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
