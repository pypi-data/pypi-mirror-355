import torchvision.models as models

def load_model(cfg):
    model_name = cfg.get("name", "resnet18")
    pretrained = cfg.get("pretrained", False)

    if model_name == "resnet18":
        return models.resnet18(pretrained=pretrained)
    raise ValueError(f"Model '{model_name}' not supported")