## Publish a Domino Model to an External Model Registry

## First Create and Register a model

For this we have provided a [notebook](./register_models.ipynb). 

The first section shows you how to create a model and register it. This is a scikit learn model
but any model can be registered using MLflow API supported by Domino

When you register the models go the "Experiments" page in Domino and view the artifacts for the runs

The folder structure is crucial.
- `mymodel` (All the model definitions and model binaries are stored here. The model is loaded from this folder)
- `client` (The client programs, for example, those going to the ENTRYPOINT in the Dockerfile endup here)
- The root folder contains the `Dockerfile.template` and `create_docker_image.sh.template`

The reason we have templates for the Dockerfile is because we cannot yet resolve them.
The resolution to `Dockerfile` and `create_docker_image.sh` needs the `model_version` that is assigned
after the artifacts are registered. Note that we do not need these files at all. The downstream client
program can use their own if they know the folder structure for the artifacts

## Build, Publish and Run Image to an external registry

```
export DOMINO_USER_API_KEY=<DOMINO_USER_API_KEY>
export DOMINO_RUN_ID=<DOMINO_RUN_ID>
export MLFLOW_TRACKING_URI=<MLFLOW_TRACKING_URI>

./download_models.py "/tmp/foundry_models"
```
1. You need a valid run id for this project for the above API key. Either run a job and fetch it
The runid need not be active. We could also use the Domino API to start a dummy job and create
a run id dynamically.
2. Example for the tracking uri is `export MLFLOW_TRACKING_URI=https://secureds53799.cs.domino.tech/`

```shell
cd /tmp/foundry_models
ls /tmp/foundry_models/

#You will see a folder for all registered models. I see only one because I have only one
/tmp/foundry_models/
- foundry_model
- pltr_foundry_model

cd /tmp/foundry_models/pltr_foundry_model

```
Now you will see a folder structure for all versions for which the tag `TARGET_PLTR_FOUNDRY` was added to the 
model version
```shell
/tmp/foundry_models/pltr_foundry_model
- v1
- v2     
- v3
- v4
- v5      
```


Go the most recent one

```shell
cd /tmp/foundry_models/pltr_foundry_model/v5

chmod 755 create_docker_image.sh
./create_docker_image.sh
```

This will publish the model to  `quay.io/domino/pltr_foundry_model:v5` (Or your registry) and also run it locally for you

## Key Takeaways

The process is fully automated as follows-

1. The Domino user will register models using specific protocols (Tags and Artifact locations). We can wrap this in a 
utility libraries
2. The `download_models.py` will run on schedule and download the models matching the appropriate tags
3. Each downloaded model will have a `create_model_image.sh` and `Dockerfile` along with other artifacts
4. The process to run these for non-published models will also be run on schedule

The end result is depending on the cadence (2,3,4) runs, the model images will be available in foundry.

If the cadence is 15 mins, the image will be available in 15 mins after the Domino user publishes the model.

The steps 2,3,4 are fairly lightweight allowing us to have a more frequent executions


