FROM public.ecr.aws/docker/library/python:3.7-buster as base

RUN apt-get -y update && apt-get install -y \
         nginx \
         ca-certificates \
         policycoreutils \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/usr/sbin/:${PATH}"

COPY helpers/requirements.txt /requirements.txt

RUN pip install --upgrade pip && pip install --no-cache -r /requirements.txt && \
    rm /requirements.txt
# Set up the program in the image
COPY helpers /opt/program


### start of TRAINING container
FROM base as xgboost
COPY training/xgboost/requirements.txt /requirements.txt
RUN pip install --no-cache -r /requirements.txt && \
    rm /requirements.txt

# sm vars
ENV SAGEMAKER_MODEL_SERVER_TIMEOUT="300"
ENV MODEL_SERVER_TIMEOUT="300"
ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/program:${PATH}"

# env vars

# Set up the program in the image
COPY training/xgboost /opt/program

# set permissions of entrypoint
RUN chmod +x /opt/program/__main__.py

WORKDIR /opt/program
