import logging

import torch
from torch import nn
from torch import optim
import torchvision.models as torch_models


class TorchModelCollection:
    def __init__(self):
        self.target_device = "cuda"
        self.device = None
        self.model = None
        self.name = ""
        self.num_classes = 0
        self.loss_func = None
        self.optimizer = None
        self.optimizer_settings = {}

    def load_model(self):
        logging.info("Loading model")
        # device = "mps" if torch.cuda.is_available() else "cpu"
        if self.target_device == "cuda" and torch.cuda.is_available():
            self.device = torch.device("cuda")
            logging.info("Loading on GPU")
        else:
            self.device = torch.device("cpu")
            logging.info("Loading on CPU")

        if self.name == "resnet18":
            logging.info("Loading resnet model")
            self.model = torch_models.resnet18(
                weights=torch_models.ResNet18_Weights.DEFAULT
            )
            self.model.fc = nn.Linear(self.model.fc.in_features, self.num_classes)
        elif self.name == "mobilenet_v2":
            logging.info("Loading mobilenet_v2 model")
            self.model = torch_models.mobilenet_v2(
                weights=torch_models.MobileNet_V2_Weights.DEFAULT
            )
            self.model.classifier[1] = nn.Linear(
                self.model.classifier[1].in_features, self.num_classes
            )
        else:
            raise RuntimeError(f"Model name {self.name} not supported")

        self.model = self.model.to(self.device)
        self.loss_func = nn.CrossEntropyLoss()

        optimizer_name = self.optimizer_settings["name"]
        if optimizer_name == "sgd":
            learning_rate = self.optimizer_settings["learning_rate"]
            momentum = self.optimizer_settings["momentum"]
            self.optimizer = optim.SGD(
                self.model.parameters(), lr=learning_rate, momentum=momentum
            )
        elif optimizer_name == "adam":
            learning_rate = self.optimizer_settings["learning_rate"]
            torch.optim.Adam(params=self.model.parameters(), lr=learning_rate)
        else:
            raise RuntimeError(f"Unsupported optimizer name {optimizer_name}")
        logging.info("Finished Loading model")
