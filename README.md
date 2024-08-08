## Publish a Domino Model to an External Model Registry

The design for this workload is outlined in this ![Architecture Overview](assets/publish-to-external-model-regisry.png).
## First Create and Register a model

For this we have provided a [notebook](./create_models.ipynb). 

The first section shows you how to create a model and register it. This is a scikit learn model
but any model can be registered using MLflow API supported by Domino

When you register the models go the "Experiments" page in Domino and view the artifacts for the runs

The folder structure is crucial.
- `mymodel` (All the model definitions and model binaries are stored here. The model is loaded from this folder)
- `client` (The client programs, for example, those going to the ENTRYPOINT in the Dockerfile endup here)
- `templates` (Contains `Dockerfile.template` and `create_docker_image.sh.template`)

The reason we have templates for the Dockerfile is because we cannot yet resolve them.
The resolution to `Dockerfile` and `create_docker_image.sh` needs the `model_version` that is assigned
after the artifacts are registered. Note that we do not need these files at all. The downstream client
program can use their own if they know the folder structure for the artifacts

## Build, Publish and Run Image to an external registry 
 
Run the notebook publish_models.ipynb [notebook](./publish_models.ipynb)

In the first cell update the appropriate values to your values
```python
import os
#Ideally put these in your Domino User Environment Variables. Try not to hard code them
os.environ['REGISTRY_URL']='xxx-xx-registry.palantirfoundry.com'
os.environ['REGISTRY_USER']='<REGISTRY_USER>'
os.environ['REGISTRY_TOKEN']='REGISTRY_TOKEN'


#This comes from the previous notebook where the model was published to Experiment Manager
model_name="pltr_foundry_model"
model_version="19"
```
And then run the next cell
```python
import requests
import json
import os
import mlflow
from mlflow.client import MlflowClient

#From previous cell
model_name="pltr_foundry_model"
model_version="19"


client = MlflowClient()
mv = client.get_model_version(model_name, model_version)
print(mv)
#Update these to your Domino URL and get this IP from your Domino Representative
MLFLOW_TRACKING_URI='https://secureds53799.cs.domino.tech/'
BUILD_URL = "https://34.218.240.146:8443/build"

payload = json.dumps({
  "model_name": model_name,
  "model_version": model_version
})
headers = {
  'MLFLOW_TRACKING_URI': MLFLOW_TRACKING_URI,
  'DOMINO_USER_API_KEY': os.environ['DOMINO_USER_API_KEY'],
  'DOMINO_RUN_ID': os.environ['DOMINO_RUN_ID'],
  'REGISTRY_URL': os.environ['REGISTRY_URL'],
  'REGISTRY_USER': os.environ['REGISTRY_USER'],
  'REGISTRY_TOKEN': os.environ['REGISTRY_TOKEN'],
  'Content-Type': 'application/json'
}

response = requests.request("POST", BUILD_URL, headers=headers, data=payload,verify=False)

print(response.text)

```

## Build, Publish and Run Image to an external registry from a shell

```shell

export MLFLOW_TRACKING_URI=https://securedsxxx.cs.domino.tech/
export DOMINO_RUN_ID=<DOMINO_RUN_ID>
export DOMINO_USER_API_KEY=<DOMINO_USER_API_KEY>
export REGISTRY_URL=xxx-xx-registry.palantirfoundry.com
export REGISTRY_USER=<REGISTRY_USER>
export REGISTRY_TOKEN=<REGISTRY_TOKEN>
export MODEL_NAME=<MODEL_NAME>
export MODEL_VERSION=<MODEL_VERSION>
python download_models_and_publish.py $MODEL_NAME $MODEL_VERSION
```



## Deploy the REST APP to publish models [This is a pre-requisite to the previous two steps]


Follow these steps:
1. Use a linux instance with a Docker client installed (I used an EC2 instance)
```shell
sudo apt-get update -y
sudo apt-get install apt-transport-https ca-certificates curl software-properties-common -y
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo apt-get update -y
sudo apt-get install docker-ce -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

```
2. Clone the current repo 
3. Install certificates in the `$HOME/app` folder
```shell
mkdir $HOME/app
openssl req -x509 -nodes -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365


```
3. Create a python virtual environment
```shell
sudo apt-get install python3 -y
sudo apt-get install python3-pip -y
sudo apt-get install python3-venv -y
python3 -m venv myenv
source myenv/bin/activate

```
4. Update the libraries to the environment
```shell
pip install -r flask.requirements.txt
```
5. Start the Flask App
```shell
nohup python3 builder-app.py >log.txt 2>log.err & 
```

## Benefits of this approach

Domino introduced the Model Registry along with its new Experiment Manager. The purpose of the model 
registry to encourage users to publish models which can be **run anywhere**. 

Anywhere includes any execution architecture, `linux/amd64`, `linux/arm64`, `linux/arm/v7` or any new
one that emerges in the future. 

The other benefit if this approach is, it allows you to create  docker image of minimum size possible
to run on the target platform. This reduces startup times as well as makes the model execution
process as cost efficient as possible. If you want to bundle the Domino models from Domino Model
Registry into an existing image, you are free to do so by using it as the base image. The Model
Registry only contains the model artifacts and the metadata about the execution environment such as
- `conda.yaml`, `python_env.yaml` and `requirements.txt`


## Alternative approach using Kaniko in the K8s cluster 


We could run the build using Kaniko. First create the image which downloads the models from Model Registry
and builds them in Kaniko and pubishes them back to `quay.io/domino` . You can adapt this code to publish to any
registry.

```shell
docker build --platform=linux/amd64  -f ./Dockerfile -t  quay.io/domino/kaniko-based-modelregistry-push:v3 .
docker push quay.io/domino/kaniko-based-modelregistry-push:v3    
```

This builds the image based on the `Dockerfile` in the root folder. The full Dockerfile is below:

```shell
FROM gcr.io/kaniko-project/executor:v1.23.2 as kaniko
FROM python:3.9-slim

# Copy Kaniko executor from the previous stage
COPY --from=kaniko /kaniko /kaniko
# Ensure Kaniko executor is executable
RUN chmod +x /kaniko/executor
RUN chmod 777 /kaniko/
ENV PATH=$PATH:/home/app/.local/bin:/home/app/bin
ENV PYTHONUNBUFFERED=true
ENV PYTHONUSERBASE=/home/app

#RUN groupadd --gid 1000 domino && \
#    useradd --uid 1000 --gid 1000 domino -m -d /app
#RUN apt-get update \
#    && apt-get upgrade --yes \
#    && apt-get install -y --no-install-suggests --no-install-recommends \
#    curl \
#    && apt-get clean \
#    && rm -rf /var/lib/apt/lists/*
RUN pip install mlflow pyjwt
WORKDIR /app
COPY  *.py  .
#USER 1000
ENTRYPOINT ["python","/app/publish_models.py"]
```

This has to run as root. If I run it as another user `kaniko` builds throw and error which looks like this
```shell
INFO[0001] Building stage 'quay.io/domino/python-slim:3.9.16-slim-bullseye-356299' [idx: '0', base-idx: '-1']
INFO[0001] Unpacking rootfs as cmd RUN groupadd --gid 1000 domino &&     useradd --uid 1000 --gid 1000 domino -m -d /app requires it.
error building image: error building stage: failed to get filesystem from image: chown /bin: operation not permitted
```

Create a k8s secret
```shell
export MLFLOW_TRACKING_URI=https://securedsxxx.cs.domino.tech/
export DOMINO_RUN_ID=<DOMINO_RUN_ID>
export DOMINO_USER_API_KEY=<DOMINO_USER_API_KEY>
export REGISTRY_URL=xxx-xx-registry.palantirfoundry.com
export REGISTRY_USER=<REGISTRY_USER>
export REGISTRY_TOKEN=<REGISTRY_TOKEN>
export MODEL_NAME=<MODEL_NAME>
export MODEL_VERSION=<MODEL_VERSION>

kubectl create secret generic domino-kaniko-secret \
  --from-literal=MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI} \
  --from-literal=DOMINO_RUN_ID=${DOMINO_RUN_ID} \
  --from-literal=DOMINO_USER_API_KEY=${DOMINO_USER_API_KEY} \
  --from-literal=REGISTRY_URL=${REGISTRY_URL} \
  --from-literal=REGISTRY_USER=${REGISTRY_USER} \
  --from-literal=REGISTRY_TOKEN=${REGISTRY_TOKEN} 

```

Next run the example kaniko pod in the path `./k8s/kaniko-pod.yaml`. 

Note that if your `Dockerfile` based on the `./template/Dockerfile.template` uncomment this section the kanio build will fails
```shell
#RUN apt-get update \
#    && apt-get upgrade --yes \
#    && apt-get install -y --no-install-suggests --no-install-recommends \
#    curl \
#    && apt-get clean \
#    && rm -rf /var/lib/apt/lists/*
```

In my example I used

```shell
MODEL_NAME=pltr_foundry_model
MODEL_VERSION=8
```

Now create the pod

```shell
kubectl -n domino-compute delete pod kaniko-domino-model-registry
kubectl -n domino-compute apply -f kaniko-domino-model-registry
kubectl -n domino-compute logs -f kaniko-domino-model-registry
```

The logs will show you that the build and push takes approximately 55 seconds. Compared to around 40 seconds from
the laptop