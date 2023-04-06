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

DRONE_DBG = False  # Idk was from code I stole
MAX_VEL = 200  # Max velocity of the drone
ACC_STRENGTH = 2  # Most the drone can move
SENSOR_DISTANCE = 200  # Range of the sensor
ACTIVATION_THRESHOLD = 0  # Threshold needed for neural network to activate the movement of the drone

# =========== Recommend not changing these =============
# Window dims
WIN_WIDTH = 1200
WIN_HEIGHT = 600

# Font for scores if we wanted to draw them on the window
STAT_FONT = pygame.font.SysFont("comicsans", 50)
END_FONT = pygame.font.SysFont("comicsans", 70)

DRAW_LINES = False  # If you want to draw the lines of the sensors
TIME_LIMIT = 30000  # Time limit of each run in milliseconds (30000 = 30 secs)
MAP_SIZE = (200, 200)  # Grid size for calculating where the drone has been

# Drone dims
drone_height = 20
drone_width = 20

# Initialising the pygame window
WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Cave Explorer")

# Colour of all the cave sections (obstacles)
OBSTACLE_COLOUR = (185, 122, 87)

# Initialising generation number
gen = 0

# ================== CAVE IMAGES ==================
drone_images = [pygame.transform.scale(pygame.image.load(os.path.join("imgs", "blue_drone.png")), (drone_width, drone_height))]
bg_img = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "background.png")), (WIN_WIDTH, WIN_HEIGHT))

ceil_imgs = [pygame.transform.scale(pygame.image.load(os.path.join("imgs", "ceil_1.png")), (WIN_WIDTH, 100)),
             pygame.transform.scale(pygame.image.load(os.path.join("imgs", "ceil_2.png")), (WIN_WIDTH, 100)),
             pygame.transform.scale(pygame.image.load(os.path.join("imgs", "ceil_3.png")), (WIN_WIDTH, 100))]


floor_imgs = [pygame.transform.rotate(pygame.transform.scale(pygame.image.load(os.path.join("imgs", "ceil_1.png")),
                                                             (WIN_WIDTH, 100)), -180),
              pygame.transform.rotate(pygame.transform.scale(pygame.image.load(os.path.join("imgs", "ceil_2.png")),
                                                             (WIN_WIDTH, 100)), -180),
              pygame.transform.rotate(pygame.transform.scale(pygame.image.load(os.path.join("imgs", "ceil_3.png")),
                                                             (WIN_WIDTH, 100)), -180)
              ]

cave_imgs = [pygame.transform.scale(pygame.image.load(os.path.join("imgs", "cave_1.png")), (WIN_WIDTH, WIN_HEIGHT)),
             pygame.transform.scale(pygame.image.load(os.path.join("imgs", "cave_2.png")), (WIN_WIDTH, WIN_HEIGHT)),
             pygame.transform.scale(pygame.image.load(os.path.join("imgs", "cave_3.png")), (WIN_WIDTH, WIN_HEIGHT)),
             pygame.transform.scale(pygame.image.load(os.path.join("imgs", "cave_4.png")), (WIN_WIDTH, WIN_HEIGHT)),
             pygame.transform.scale(pygame.image.load(os.path.join("imgs", "cave_5.png")), (WIN_WIDTH, WIN_HEIGHT))]


# ========= Surroundings =========
class Cave:

    def __init__(self, y, img_ind):
        self.y = y
        self.x = 0
        self.IMG = cave_imgs[img_ind]

    def draw(self, win):
        win.blit(self.IMG, (self.x, self.y))


class Floor:

    def __init__(self, y, img_ind):
        self.y = y
        self.x = 0
        self.IMG = floor_imgs[img_ind]

    def draw(self, win):
        win.blit(self.IMG, (self.x, self.y))


class Ceil:
    def __init__(self, y, img_ind):
        self.y = y
        self.x = 0
        self.IMG = ceil_imgs[img_ind]

    def draw(self, win):
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
        self.time_since_explored = 0

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
# ================== END OF DRONES ==================


# ================== SENSOR ==================
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

        # While We Don't Hit OBSTACLE COLOUR AND length < sensor range -> make the length of sensor larger
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
# ================== END OF SENSOR ==================


# ================== MAP ==================
class Map:
    array = [[False for x in range(MAP_SIZE[0])] for y in range(MAP_SIZE[1])]
    cell_size = (WIN_WIDTH // MAP_SIZE[0], WIN_HEIGHT // MAP_SIZE[1])
    surface = pygame.Surface((MAP_SIZE[0] * cell_size[0], MAP_SIZE[1] * cell_size[1]), pygame.SRCALPHA)

    def __int__(self):
        self.array = [[False for x in range(MAP_SIZE[0])] for y in range(MAP_SIZE[1])]
        self.cell_size = (WIN_WIDTH // MAP_SIZE[0], WIN_HEIGHT // MAP_SIZE[1])
        self.surface = pygame.Surface((MAP_SIZE[0] * self.cell_size[0], MAP_SIZE[1] * self.cell_size[1]),
                                      pygame.SRCALPHA)
# ================== END OF MAP ==================


# ======================== LOCAL FUNCTIONS ==========================
def draw_window(win, drones, ceil, floor, cave, sensors, maps, best_drone):
    win.blit(bg_img, (0, 0))  # Draw the background image (taken from super mario 2)

    # Draw obstacles
    floor.draw(win)
    ceil.draw(win)
    cave.draw(win)

    # For each drone, draw the drone and if told to do so, draw the line sensors
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

        if DRAW_LINES:
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

    maps[best_drone].surface.fill((0, 0, 0, 0))

    # Draw the squares on the surface
    for y in range(MAP_SIZE[1]):
        for x in range(MAP_SIZE[0]):
            if maps[best_drone].array[x][y]:
                color = (0, 255, 0, 100)  # Visited cells are green and slightly transparent
            else:
                color = (255, 255, 255, 0)  # Unvisited cells are white and slightly transparent
            rect = pygame.Rect(x * maps[best_drone].cell_size[0], y * maps[best_drone].cell_size[1],
                               maps[best_drone].cell_size[0], maps[best_drone].cell_size[1])
            pygame.draw.rect(maps[best_drone].surface, color, rect)

    # Draw the map for the best genome
    win.blit(maps[best_drone].surface, (0, 0))

    pygame.display.update()


def eval_genomes(genomes, config):
    """
    runs the simulation of the current population of
    drones and sets their fitness based on the distance they
    reach in the game.
    """
    # ================== INITIALISE RUN ==================
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
    # Select a random image from the possible images
    ceil_floor_ind = random.randint(0, 2)
    cave_ind = random.randint(0, 4)

    ceiling = Ceil(0, ceil_floor_ind)
    floor = Floor(500, ceil_floor_ind)
    cave = Cave(0, cave_ind)

    start_time = pygame.time.get_ticks()  # Set for a time-limit for all the genomes
    clock = pygame.time.Clock()

    # While the run still has genomes to evaluate...
    while len(drones) > 0:
        clock.tick(30)  # 30 frames per second (i think)

        for event in pygame.event.get():  # Set up so you can actually quit pygame
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        best_drone_index = 0
        best_fitness = 0

        # ================== GET NEURAL NETWORK INPUTS ==================
        sensed_lists = [[0] * 8 for _ in drones]  # Set up the lists for the sensor output values
        for i, drone in enumerate(drones):
            for j, sensor in enumerate(sensors[i]):
                sensor.x = drone.x + (drone_width / 2)
                sensor.y = drone.y + (drone_height / 2)
                dist = sensor.check_radar(win)  # Distance of an obstacle from the drone (Max value = 300)
                sensed_lists[i][j] = dist

            # Create a tuple for the input of the neural network
            inputs = (drone.x, drone.y, sensed_lists[i][0], sensed_lists[i][1], sensed_lists[i][2], sensed_lists[i][3],
                      sensed_lists[i][4], sensed_lists[i][5], sensed_lists[i][6], sensed_lists[i][7])

            drone.commands = nets[i].activate(inputs)  # Get the outputs of the neural network given the inputs

            # ================== MOVE DRONE ==================
            (x, y) = drone.move()  # Move the drone

            # ================== REWARD GENOMES ==================
            ge[i].fitness += 0.05  # If it is still alive reward it for staying alive
            map_x = int(x) // maps[i].cell_size[0]
            map_y = int(y) // maps[i].cell_size[1]
            if not maps[i].array[map_x][map_y]:
                maps[i].array[map_x][map_y] = True
                ge[i].fitness += 1
                drone.time_since_explored = 0
            else:
                drone.time_since_explored += 1
            if ge[i].fitness > best_fitness:
                best_fitness = ge[i].fitness
                best_drone_index = i

        # ================== CHECK IF DRONE IS ALIVE ==================
        for i, drone in enumerate(drones):
            # If it collides with anything, kill it.
            if drone.collision(ceiling) or drone.collision(floor) or drone.collision(cave) or \
                    drone.y > WIN_HEIGHT or drone.y < 0 or drone.x < 0 or drone.x > WIN_WIDTH:
                nets.pop(i)
                ge.pop(i)
                drones.pop(i)
            if drone.time_since_explored > 50:
                nets.pop(i)
                ge.pop(i)
                drones.pop(i)

        # ================== CHECK IF TIMELIMIT REACHED ==================
        elapsed_time = pygame.time.get_ticks() - start_time
        if elapsed_time > TIME_LIMIT:  # Time limit (in milliseconds)
            for i, drone in enumerate(drones):
                nets.pop(i)
                ge.pop(i)
                drones.pop(i)

        # ================== DRAW THE UPDATED SIMULATION ==================
        draw_window(WIN, drones, ceiling, floor, cave, sensors, maps, best_drone_index)


def run(config_file):
    """
    runs the NEAT algorithm to train a neural network to fly drones.
    """

    # Configure NEAT
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # Run for up to 'n' generations.
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
