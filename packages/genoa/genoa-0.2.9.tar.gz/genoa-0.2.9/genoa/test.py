from Genoa import Genoa_NN
from Genoa import Genoa_NEAT
import torch

def make_model():
    return Genoa_NN([6, 12, 4])

def fitness_fn(model):
    score = 0
    for _ in range(10):
        inputs = torch.rand(1, 6)
        output = model.forward(inputs)
        score += torch.sum(output).item()
    return score

neat = Genoa_NEAT(model_fn=make_model, fitness_fn=fitness_fn, population=50, generations=100)
best_model = neat.train()