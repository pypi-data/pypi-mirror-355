from Genoa import Genoa
from torch import tensor

X = tensor([
    [0, 0],
    [1, 1],
    [0, 1],
    [1, 0]
])

Y = tensor([
    [0],
    [0],
    [1],
    [1]
])

model = Genoa([2, 10, 10, 1], device='cpu')

model.load()

print(f"Inputs: {X}\n")
print(f"Outputs: {Y}\n")
print(f"Predictions: {model.forward(X)}")
print(f"Loss: {model.loss_fn(model.forward(X), Y)}")

model.train(X, Y)

print(f"Inputs: {X}\n")
print(f"Outputs: {Y}\n")
print(f"Predictions: {model.forward(X)}")
print(f"Loss: {model.loss_fn(model.forward(X), Y)}")
