import torch
import torch.nn as nn
import torch.optim as optim
import time
import argparse


def test_gpu_performance(batch_size=40000, epochs=10, verbose=True):
    print(f"batch_size: {batch_size}\n"
          f"epochs: {epochs}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if verbose:
        print("Using device:", device)

    class VeryDeepLargeNN(nn.Module):
        def __init__(self):
            super(VeryDeepLargeNN, self).__init__()
            self.layer1 = nn.Linear(4096, 8192)
            self.layer2 = nn.Linear(8192, 8192)
            self.layer3 = nn.Linear(8192, 8192)
            self.layer4 = nn.Linear(8192, 8192)
            self.layer5 = nn.Linear(8192, 8192)
            self.layer6 = nn.Linear(8192, 4096)
            self.layer7 = nn.Linear(4096, 4096)
            self.layer8 = nn.Linear(4096, 4096)
            self.layer9 = nn.Linear(4096, 4096)
            self.layer10 = nn.Linear(4096, 2048)
            self.layer11 = nn.Linear(2048, 1024)
            self.output = nn.Linear(1024, 10)

        def forward(self, x):
            x = torch.relu(self.layer1(x))
            x = torch.relu(self.layer2(x)) + x
            x = torch.relu(self.layer3(x)) + x
            x = torch.relu(self.layer4(x)) + x
            x = torch.relu(self.layer5(x)) + x
            x = torch.relu(self.layer6(x))
            x = torch.relu(self.layer7(x)) + x
            x = torch.relu(self.layer8(x)) + x
            x = torch.relu(self.layer9(x)) + x
            x = torch.relu(self.layer10(x))
            x = torch.relu(self.layer11(x))
            return self.output(x)

    model = VeryDeepLargeNN().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.01)

    data = torch.randn(batch_size, 4096).to(device)
    labels = torch.randint(0, 10, (batch_size,)).to(device)

    start_time = time.time()
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(data)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        if verbose:
            print(f"Epoch {epoch + 1}, Loss: {loss.item()}")
    total_time = time.time() - start_time
    if verbose:
        print("Total training time:", total_time, "seconds")
    return total_time


def main():
    parser = argparse.ArgumentParser(description="Test GPU performance with a deep neural network")
    parser.add_argument("-b", "--batch-size", type=int, default=40000, help="Batch size for synthetic input")
    parser.add_argument("-e", "--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--no-verbose", action="store_true", help="Suppress detailed logs")

    args = parser.parse_args()

    test_gpu_performance(
        batch_size=args.batch_size,
        epochs=args.epochs,
        verbose=not args.no_verbose
    )

