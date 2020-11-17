import torch
import sys
import os
import pprint
from sagemaker_training import environment


def run(env: environment.Environment):
    print(sys.argv)
    pprint.pprint(os.environ)
    print("CUDA available =", torch.cuda.is_available())
    pprint.pprint(env.__dict__)

    def getfiletree(rootdir):
        for name in os.listdir(rootdir):
            if os.path.isdir(os.path.join(rootdir, name)):
                yield name + "/"
                for line in getfiletree(os.path.join(rootdir, name)):
                    yield (" " * 4) + line
            else:
                yield name

    print("filetree:")
    print("\n".join(getfiletree("/opt/ml")))
