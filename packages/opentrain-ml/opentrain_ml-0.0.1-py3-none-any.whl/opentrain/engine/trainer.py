# opentrain/engine/trainer.py

class Trainer:
    def __init__(self, model, train_loader, val_loader, cfg):
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.cfg = cfg

    def train(self):
        print("Training started...")
        print(f"Model: {self.model.__class__.__name__}")
        print(f"Train samples: {len(self.train_loader.dataset)}")
        print("Finished one dummy epoch ✅")
