import sys
import os
import importlib
from sagemaker_training import environment


def main():
    env = environment.Environment()

    entry_point_module = env.hyperparameters["entry_point"]

    src_package_dir = "/opt/ml/input/data/code"
    src_package_path = os.path.join(src_package_dir, os.listdir(src_package_dir)[0])
    os.system(sys.executable + " -m pip install " + src_package_path)

    importlib.import_module(entry_point_module).run(env)


if __name__ == "__main__":
    main()
