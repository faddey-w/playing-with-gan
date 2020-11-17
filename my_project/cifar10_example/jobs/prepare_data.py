import os
import torchvision
from sagemaker_training import environment


def run(env: environment.Environment):
    """
    An example of simplest job - no checkpoints, no distributed workers.
    """
    data_dir = os.path.join(env.channel_input_dirs["training"], "cifar10-data")
    torchvision.datasets.CIFAR10(data_dir, download=True)
