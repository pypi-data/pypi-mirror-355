from Genoa import Genoa
from torch import tensor

model = Genoa([2, 10, 10, 1])

model.train(tensor([[0, 0], [1, 1], [1, 0], [0, 1]]), tensor([[0], [0], [1], [1]]))
print(model.forward(tensor([[0, 0]])).item())
print(model.forward(tensor([[1, 1]])).item())
print(model.forward(tensor([[1, 0]])).item())
print(model.forward(tensor([[0, 1]])).item())