import pygame
import random
from torch import tensor
from Genoa import Genoa, EvoNet

# ==== Pygame Setup ====
pygame.init()
WIDTH, HEIGHT = 1000, 500
CELL_SIZE = 10
GRID_W, GRID_H = WIDTH // CELL_SIZE, HEIGHT // CELL_SIZE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Genoa Evolution Simulation")
clock = pygame.time.Clock()
FRAME_RATE = 10000
font = pygame.font.SysFont("Arial", 20)

# ==== Creature ====
class Creature:
    def __init__(self, model: Genoa):
        self.model = model
        self.reset()

    def reset(self):
        self.x = random.randint(0, GRID_W - 1)
        self.y = random.randint(0, GRID_H - 1)
        self.energy = 100
        self.collected = 0
        self.frames = 0

    def inputs(self):
        return tensor([self.x / GRID_W, self.y / GRID_H, self.energy / 100])

    def act(self, inputs):
        out = self.model.forward(inputs).detach().numpy().flatten()
        vx = self._to_dir(out[0])
        vy = self._to_dir(out[1])
        eat = out[2] > 0
        return vx, vy, eat

    def _to_dir(self, x):
        if x < -0.33:
            return -1
        elif x > 0.33:
            return 1
        return 0

    def move(self, vx, vy):
        self.x = max(0, min(self.x + vx, GRID_W - 1))
        self.y = max(0, min(self.y + vy, GRID_H - 1))

    def update(self, food):
        if self.energy <= 0:
            return False
        self.energy -= 1
        self.frames += 1
        vx, vy, eat = self.act(self.inputs())
        self.move(vx, vy)
        if (self.x, self.y) in food and eat:
            food.remove((self.x, self.y))
            self.energy += 20
            self.collected += 1
        return True

    def draw(self):
        pygame.draw.rect(screen, 'Red', (self.x * CELL_SIZE, self.y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

# ==== Helpers ====
def model_fn():
    m = Genoa([3, 12, 3], device='cpu')
    m.hidden_fn = m.ReLU
    m.output_fn = m.Tanh
    return m

def gen_creatures(n):
    return [Creature(model_fn()) for _ in range(n)]

def gen_food(n):
    return [(random.randint(0, GRID_W - 1), random.randint(0, GRID_H - 1)) for _ in range(n)]

def draw_env(creatures, food, gen, fr):
    screen.fill('White')
    for fx, fy in food:
        pygame.draw.rect(screen, 'Green', (fx * CELL_SIZE, fy * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    for c in creatures:
        c.draw()
    text = font.render(f"Generation: {gen}", True, (0, 0, 0))
    screen.blit(text, (10, 10))
    pygame.display.update()
    clock.tick(fr)

def fitness(c):
    distance = abs(c.x - GRID_W // 2) + abs(c.y - GRID_H // 2)
    return c.collected * 100 + c.frames - (100 - c.energy) - distance * 0.5

# ==== Main Simulation Loop ====
POP_SIZE = 20
creatures = gen_creatures(POP_SIZE)
generation = 0

while True:
    food = gen_food(300)
    for c in creatures:
        c.reset()

    live_creatures = creatures.copy()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        draw_env(live_creatures, food, generation, FRAME_RATE)

        alive = 0
        next_live = []
        for c in live_creatures:
            if c.update(food):
                alive += 1
                next_live.append(c)

        live_creatures = next_live
        running = len(live_creatures) > 0

        if alive == 0:
            running = False

    # Evolve
    scores = [fitness(c) for c in creatures]
    models = EvoNet([c.model for c in creatures], scores, POP_SIZE).evolve(mr=1.0)
    creatures = [Creature(models[i]) for i in range(POP_SIZE)]
    generation += 1
    print(f"Generation {generation} | Max: {max(scores)} | Avg: {sum(scores)//len(scores)}")
