import os
import sys
import mlflow
from mlflow.tracking import MlflowClient
import pandas as pd


# model_name = "foundry_model"
# model_version = 6

def predict(model_uri, features):
    loaded_model = mlflow.pyfunc.load_model(model_uri)
    return loaded_model.predict(features)


def main(model_name, model_version, base_path='/tmp/local_models'):
    client = MlflowClient()
    mv = client.get_model_version(model_name, model_version)
    run_id = mv.run_id

    # An example path that exists on every machine. Modify as needed
    model_download_path = f'{base_path}/{model_name}/v{model_version}'
    os.makedirs(model_download_path, exist_ok=True)

    # Download artifacts and verify if they exist
    client.download_artifacts(run_id, f"", model_download_path)
    os.listdir(model_download_path)

    # Load the model and predict
    d = pd.read_json(f'{model_download_path}/example-prediction-code/features.json', orient='records', lines=True)
    model_uri_saved = f'{model_download_path}/mymodel'
    return predict(model_uri_saved, d)


if __name__ == "__main__":
    print(main(sys.argv[1], sys.argv[2],sys.argv[3]))