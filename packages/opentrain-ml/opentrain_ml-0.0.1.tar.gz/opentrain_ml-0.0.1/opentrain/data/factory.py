import torchvision.transforms as transforms
from torchvision.datasets import MNIST
from torch.utils.data import DataLoader

def get_data_loaders(cfg):
    transform = transforms.ToTensor()
    train_dataset = MNIST(root="data", train=True, download=True, transform=transform)
    val_dataset = MNIST(root="data", train=False, download=True, transform=transform)

    train_loader = DataLoader(train_dataset, batch_size=cfg.get("batch_size", 32), shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=cfg.get("batch_size", 32))

    return train_loader, val_loader
