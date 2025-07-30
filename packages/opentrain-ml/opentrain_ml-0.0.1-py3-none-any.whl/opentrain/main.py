
import argparse
from opentrain.config.loader import load_config
from opentrain.models.factory import load_model
from opentrain.data.factory import get_data_loaders
from opentrain.engine.trainer import Trainer

def train(config_path):
    cfg = load_config(config_path)
    model = load_model(cfg['model'])
    train_loader, val_loader = get_data_loaders(cfg['dataset'])
    trainer = Trainer(model, train_loader, val_loader, cfg)
    trainer.train()

def main():
    parser = argparse.ArgumentParser(description="OpenTrain CLI")
    parser.add_argument("train", help="Train a model")
    parser.add_argument("--config", type=str, required=True, help="Path to config file")
    args = parser.parse_args()
    train(args.config)

if __name__ == "__main__":
    main()