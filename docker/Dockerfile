# tensorflow is chosen just because it was first found image with all CUDA gears installed
FROM tensorflow/tensorflow:2.1.0-gpu

# install your beloved version of python and make it default
RUN add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y python3.7 python3.7-dev \
    && ln -sf python3.7 /usr/bin/python \
    && ln -sf python3.7 /usr/bin/python3

# install some heavy dependency to speed up jobs initialization.
# it is not necessary to keep this list updated,
# because actual dependencies will be caught up from setup.py
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python get-pip.py
RUN python -m pip install torch==1.4.0 pandas==1.0.5 numpy==1.19.2

# this provides all necessary setuo for running the image as a training job
RUN python -m pip install sagemaker-training


ENV PATH="/opt/ml/code:${PATH}"

COPY /entrypoint.py /opt/ml/code/entrypoint.py
ENV SAGEMAKER_PROGRAM entrypoint.py
