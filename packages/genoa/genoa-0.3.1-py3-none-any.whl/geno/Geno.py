import torch
from rich.progress import track
import matplotlib.pyplot as plt
# from alive_progress import alive_bar




class Node:
    def __init__(self, input_size, output_size, init_type, scale, device):
        if init_type == 'he':
            stddev = torch.sqrt(torch.tensor(2 / input_size, device=device))
        elif init_type == 'xavier':
            stddev = torch.sqrt(torch.tensor(1 / input_size, device=device))
        else:
            stddev = scale
        self.w = torch.normal(0, stddev, (input_size, output_size), device=device)
        self.b = torch.zeros(1, output_size, device=device)




class Geno:
    def __init__(self, layer_size, device='cpu', init_type='he', scale=2):
        self.msg = True
        self.device = device
        self.layer_size = layer_size
        self.mutate_fn = self.mutate
        self.loss_fn = self.MSE
        self.hidden_fn = self.LeakyRelu
        self.output_fn = self.Sigmoid
        self.loss_history = []

        if self.msg:
            print('Thanks for using GENO! Made by MrPsyghost. Visit https://www.youtube.com/@MrPsyghost for more information.')

        self.layers = []
        for i in range(1, len(layer_size)):
            self.layers.append(Node(layer_size[i-1], layer_size[i], init_type, scale, device))

    def Sigmoid(self, X):
        X = (X.float()).to(self.device)
        return 1 / (1 + torch.exp(-X))

    def ReLU(self, X):
        X = (X.float()).to(self.device)
        return torch.maximum(torch.tensor(0.0, device=self.device), X)
    
    def LeakyRelu(self, X, alpha=0.01):
        X = (X.float()).to(self.device)
        return torch.where(X > 0, X, alpha * X)

    def GELU(self, X):
        X = (X.float()).to(self.device)
        return 0.5 * X * (1 + torch.tanh(torch.sqrt(torch.tensor(2 / torch.pi, device=self.device)) * (X + 0.044715 * torch.pow(X, 3))))

    def Swish(self, X):
        X = (X.float()).to(self.device)
        return X * (1 / (1 + torch.exp(-X)))

    def Softmax(self, X):
        X = (X.float()).to(self.device)
        e_x = torch.exp(X - torch.max(X))
        return e_x / e_x.sum()
    
    def MSE(self, X, Y):
        X = (X.float()).to(self.device)
        Y = (Y.float()).to(self.device)
        return torch.mean((Y - X)**2)

    def MAE(self, X, Y):
        X = (X.float()).to(self.device)
        Y = (Y.float()).to(self.device)
        return torch.mean(torch.abs((Y - X)))
    
    def CCE(self, X, Y):
        X = (X.float()).to(self.device)
        Y = (Y.float()).to(self.device)
        return torch.sum(Y*(-torch.log(X)))

    def mutate(self, s, mr):
        return s + torch.normal(0, mr, s.shape, device=self.device)

    def train(self, X, Y, mr=0.1, dr=0.999, generations=1000, population=50, early_stop=None, optim_mr=False, threshold=50):
        X = (X.float()).to(self.device)
        Y = (Y.float()).to(self.device)
        
        best = [float('inf'), None, None]
        prev_loss = float('inf')

        n = 0

        if population < 2 or generations < 0:
            print("Error: Training not possible. Population must be >=2 and generations >=1.")
            return
        else:
            for gen in track(range(generations), description="Training: "):
                losses = []
                
                for _ in range(population):
                    weights = []
                    biases = []

                    for i in range(len(self.layers)):
                        w = self.mutate_fn(self.layers[i].w, mr)
                        b = self.mutate_fn(self.layers[i].b, mr)
                        weights.append(w)
                        biases.append(b)
                    
                    h = X
                    for i in range(len(self.layers)):
                        h = self.calc(h, weights[i], biases[i], self.layers[i])

                    losses.append([self.loss_fn(h, Y), weights, biases])
                
                p1, p2 = sorted(losses, key=lambda x: x[0])[:2]

                if best[0] > p1[0]:
                    best = p1

                self.loss_history.append(best[0].item())

                for i in range(len(self.layers)):
                    self.layers[i].w = ((p1[1])[i] + 0.5*((p2[1])[i]))/1.5
                    self.layers[i].b = ((p1[2])[i] + 0.5*((p2[2])[i]))/1.5

                loss = self.loss_fn(self.forward(X), Y)

                if early_stop != None and loss <= early_stop:
                    print(f"Loss reached {early_stop}. Training stopped...")
                    break
                
                if optim_mr:
                    if prev_loss > loss:
                        mr *= dr
                        n = 0
                    else:
                        n += 1
                        if n >= threshold:
                            mr += mr*(1-dr)*dr
                            n = 0
                else:
                    mr *= dr

                mr = max(0, min(0.5, mr))

                prev_loss = loss

                if loss <= p2[0]:
                    if loss <= p1[0]:
                        for i in range(len(self.layers)):
                            self.layers[i].w = (0.5*((p1[1])[i])+self.layers[i].w)/1.5
                            self.layers[i].b = (0.5*((p1[2])[i])+self.layers[i].b)/1.5
                    else:
                        for i in range(len(self.layers)):
                            self.layers[i].w = ((p1[1])[i]+(0.5*(self.layers[i].w)))/1.5
                            self.layers[i].b = ((p1[2])[i]+(0.5*(self.layers[i].b)))/1.5
                else:
                    for i in range(len(self.layers)):
                        self.layers[i].w = ((p1[1])[i]+(0.5*(p2[1])[i]))/1.5
                        self.layers[i].b = ((p1[2])[i]+(0.5*(p2[2])[i]))/1.5

    def calc(self, X, W, B, layer):
        X = (X.float()).to(self.device)
        if layer == self.layers[-1]:
            return self.output_fn(torch.matmul(X, W) + B)
        else:
            return self.hidden_fn(torch.matmul(X, W) + B)

    def forward(self, X):
        X = (X.float()).to(self.device)
        for i in range(len(self.layers)):
            X = self.calc(X, self.layers[i].w, self.layers[i].b, self.layers[i])
        return X

    def save(self, file_name='model'):
        torch.save({
            f'w{i}': layer.w.cpu() for i, layer in enumerate(self.layers)
        } | {
            f'b{i}': layer.b.cpu() for i, layer in enumerate(self.layers)
        }, file_name + '.pt')

    def load(self, file_name='model'):
        data = torch.load(file_name + '.pt', map_location=self.device, weights_only=True)
        for i, layer in enumerate(self.layers):
            layer.w = data[f'w{i}'].to(self.device)
            layer.b = data[f'b{i}'].to(self.device)

    def graph(self):
        if hasattr(self, "loss_history"):
            plt.figure(figsize=(10, 4))
            plt.plot(self.loss_history, label="Loss", color="blue")
            plt.xlabel("Generation")
            plt.ylabel("Loss")
            plt.title("GENO Training Progress")
            plt.grid(True)
            plt.legend()
            plt.tight_layout()
            plt.show()
        else:
            print("No training history found. Run `train()` first.")