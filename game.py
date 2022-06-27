
import math
import random
from re import T
from typing import Any, List, Tuple
import pygame
import pygame.transform
import neat

from utils import clamp

pygame.font.init()
pygame.init()

NEAT_CONFIG_PATH = "neat.config.txt"

WIN_WIDTH = 500
WIN_HEIGHT = 800


def load_image(path: str):
    return pygame.transform.scale2x(pygame.image.load(path))


BIRD_IMGS = [load_image(f"imgs/bird{i}.png") for i in range(1, 4)]
PIPE_IMG = load_image(f"imgs/pipe.png")
BASE_IMG = load_image(f"imgs/base.png")
BG_IMG = load_image(f"imgs/bg.png")

STAT_FONT = pygame.font.SysFont("Cascadia", 50)


class Bird():
    '''
    the bird class
    '''
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 7

    JUMP_VEL = -10.5

    MAX_DOWN_ROTATION = -90

    MAX_VEL = 16

    FIRST_IMG_TILT = -80

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img = BIRD_IMGS[0]
        self.img_time_counter = 0

    def jump(self) -> None:
        '''
        make the bird jump, and setting the tilt and height
        '''
        self.vel = self.JUMP_VEL
        self.tick_count = 0
        self.height = self.y
        self.tilt = self.MAX_ROTATION

    def move(self) -> None:
        '''
        moves the bird one tick base on the velocity.
        '''
        self.tick_count += 1

        # physics

        d = self.vel * self.tick_count + 1.5*self.tick_count**2
        d = clamp(d, -math.inf, self.MAX_VEL)

        if d < 0:
            d -= 2

        self.y += d

        # rotation

        if d < 0 or self.y < self.height + 50:
            self.tilt = clamp(
                self.tilt, self.MAX_DOWN_ROTATION, self.MAX_ROTATION)
        else:
            if self.tilt > -self.MAX_DOWN_ROTATION:
                self.tilt -= self.ROT_VEL

    def draw(self, target: pygame.surface.Surface) -> None:
        '''
        draws the bird to the target
        :param target: the target to draw on
        :type target: pygame.surface.Surface
        '''
        self.img_time_counter += 1
        place = self.img_time_counter//self.ANIMATION_TIME
        if place >= len(BIRD_IMGS):
            place = 0
            self.img_time_counter = 0
        self.img = BIRD_IMGS[place]

        if self.tilt <= -self.FIRST_IMG_TILT:
            self.img = BIRD_IMGS[0]

        rotated_img = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_img.get_rect(
            center=self.img.get_rect(topleft=(self.x, self.y)).center)

        target.blit(rotated_img, new_rect.topleft)

    def get_mask(self) -> pygame.mask.Mask:
        '''
        returns the mask of the bird
        :returns: the mask of the bird
        :rtype: pygame.mask.Mask
        '''
        return pygame.mask.from_surface(self.img)


class Pipe():
    '''
    the pipe class
    '''


    GAP = 200
    VEL = 5

    def __init__(self, x) -> None:
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0

        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False

        self.set_height()

    def set_height(self) -> None:
        '''
        set the height accordingly to the random value  
        '''
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self) -> None:
        '''
        moves the pipe
        '''
        self.x -= self.VEL

    def draw(self, target: pygame.surface.Surface):
        '''
        draw both of the pipes
        :param target: the target to draw on
        :type target: pygame.surface.Surface
        '''
        
        target.blit(self.PIPE_TOP, (self.x, self.top))

        target.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def get_masks(self) -> Tuple[pygame.mask.Mask, pygame.mask.Mask]:
        '''
        returns a tuple of the masks of the 2 pipes
        '''
        return pygame.mask.from_surface(self.PIPE_TOP), pygame.mask.from_surface(self.PIPE_BOTTOM)

    def collide(self, bird: Bird) -> bool:
        '''
        check if a bird is colliding with a pipe
        :param bird: the bird to check
        :type bird: Bird
        :return: True if the bird is colliding with a pipe, False otherwise
        :rtype: bool
        '''
        bird_mask = bird.get_mask()
        mask_top, mask_bottom = self.get_masks()

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(mask_bottom, bottom_offset)
        t_point = bird_mask.overlap(mask_top, top_offset)

        if b_point or t_point:
            return True

        return False


class Base:
    '''
    the base class (the floor)
    '''

    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        '''
        moves the base the base and keep it inside the screen
        '''
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, target: pygame.surface.Surface):
        '''
        draw 2 times the base
        :param target: the target to draw on
        :type target: pygame.surface.Surface
        '''
        target.blit(self.IMG, (self.x1, self.y))
        target.blit(self.IMG, (self.x2, self.y))


def draw(window: pygame.surface.Surface, birds: List[Bird], pipes: List[Pipe], base: Base, score: int):
    '''
    draws all of the state to the screen
    :param window: the window to draw on
    :type window: pygame.surface.Surface
    :param birds: list of birds to draw
    :type birds: List[Bird]
    :param pipes: list of pipes to draw
    :type pipes: List[Pipe]
    :param base: base to draw
    :type base: Base
    :param score: the score to draw
    :type score: int
    '''
    window.blit(BG_IMG, (0, 0))
    for pipe in pipes:
        pipe.draw(window)
    for b in birds:
        b.draw(window)
    base.draw(window)

    score_text = STAT_FONT.render(f"Score: {score}", False, (255, 255, 255))

    window.blit(score_text, (WIN_WIDTH-score_text.get_width(), 0))

    pygame.display.update()


def eval_flappy(genomes: List[Tuple[Any, neat.DefaultGenome]], config: neat.Config):
    '''
    run the game for the different genomes
    :param genomes: the genomes to test
    :type genomes: List[Tuple[Any, neat.DefaultGenome]]
    :param config: the config
    :type config: neat.Config
    '''
    birds: List[Bird] = []
    ge: List[neat.DefaultGenome] = []
    nets: List[neat.nn.FeedForwardNetwork] = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)
    base = Base(700)

    pipes = [Pipe(700)]

    window = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

    clock = pygame.time.Clock()

    running = True

    score = 0

    while running:

        if birds.__len__() == 0:
            break

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
                quit()
        # bird.move()
        rem = []
        add_pipe = False

        pipe_ind = 0
        if len(birds) > 0:
            # determine whether to use the first or second
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1

        for index, bird in enumerate(birds):
            bird.move()
            ge[index].fitness += 0.1
            output = nets[birds.index(bird)].activate((bird.y, abs(
                bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0:
                bird.jump()

        for pipe in pipes:

            pipe.move()
            for index, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[index].fitness -= 1
                    birds.pop(index)
                    ge.pop(index)
                    nets.pop(index)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + PIPE_IMG.get_width() < 0:
                rem.append(pipe)
        if add_pipe:
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(700))
            score += 1

        for index, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(index)
                ge.pop(index)
                nets.pop(index)

        base.move()
        draw(window, birds, pipes, base, score)

        clock.tick(60)

        for r in rem:
            pipes.remove(r)


def run():
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation, NEAT_CONFIG_PATH)

    pop = neat.Population(config)

    pop.add_reporter(neat.StdOutReporter(True))

    pop.add_reporter(neat.StatisticsReporter())

    winner = pop.run(eval_flappy, 50)

    pygame.quit()


if __name__ == "__main__":
    run()
