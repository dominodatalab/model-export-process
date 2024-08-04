"""
An example script making MLflow API calls as an external client to a Domino deployment.
"""
import sys

import mlflow.sklearn
from mlflow.client import MlflowClient
from mlflow.tracking.request_header.registry import _request_header_provider_registry
import os
import mlflow

# Create a Dockerfile
import string

from domino_api_key_header_provider import DominoApiKeyRequestHeaderProvider
from domino_execution_header_provider import DominoExecutionRequestHeaderProvider

import pandas as pd

def set_mlflow_tracking_uri():
    mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    if not mlflow_tracking_uri:
        print("MLFLOW_TRACKING_URI environment variable must be set.")
        exit(1)
    mlflow.set_tracking_uri(mlflow_tracking_uri)


def register_domino_api_key_request_header_provider():
    if not os.getenv("DOMINO_USER_API_KEY"):
        print("DOMINO_USER_API_KEY environment variable must be set.")
        exit(1)
    # Set X-Domino-Api-Key request header
    _request_header_provider_registry.register(DominoApiKeyRequestHeaderProvider)


def register_domino_execution_request_header_provider():
    if not os.getenv("DOMINO_RUN_ID"):
        print("DOMINO_RUN_ID environment variable must be set.")
        exit(1)
    # Set X-Domino-Execution request header
    _request_header_provider_registry.register(DominoExecutionRequestHeaderProvider)

base_path = "/tmp/mlflow_models"

def predict(model_uri, features):
    loaded_model = mlflow.pyfunc.load_model(model_uri)
    return loaded_model.predict(features)


def create_file_from_template(template_string, context, output_file_path):
    template = string.Template(template_string)
    content = template.substitute(context)

    with open(output_file_path, 'w') as file:
        file.write(content)




def download_and_test(model_versions_to_build, base_path='/tmp/local_models'):
    client = MlflowClient()
    for mv in model_versions_to_build:
        run_id = mv.run_id
        model_name = mv.name
        model_version = mv.version
        model_download_path = f'{base_path}/{model_name}/v{model_version}'
        os.makedirs(model_download_path, exist_ok=True)

        client.download_artifacts(run_id, f"", model_download_path)
        os.listdir(model_download_path)
        # Resolve files
        context = {
                'FOUNDRY_URL': mv.tags['FOUNDRY_URL'],
                'model_name': model_name,
                'model_version': model_version,
                'model_download_folder': model_download_path,
                'model_folder': mv.tags['MODEL_FOLDER'],
                'model_client_folder': mv.tags['MODEL_CLIENT_FOLDER'],
                'entry_point': mv.tags['MODEL_ENTRY_POINT'],
                'command_line': mv.tags['MODEL_EXECUTE_PATH']
        }



        templates_folder = 'templates'
        if 'MODEL_TEMPLATES_FOLDER' in context:
            templates_folder = context['MODEL_TEMPLATES_FOLDER']
        with open(f"{model_download_path}/{templates_folder}/Dockerfile.template", 'r') as file:
            content = file.read()
            output_file = f"{model_download_path}/Dockerfile"
            create_file_from_template(content, context, output_file)
        with open(f"{model_download_path}/{templates_folder}/create_docker_image.sh.template", 'r') as file:
            content = file.read()
            output_file = f"{model_download_path}/create_docker_image.sh"
            create_file_from_template(content, context, output_file)




if __name__ == "__main__":
    print(sys.argv[1])
    base_path = sys.argv[1]
    set_mlflow_tracking_uri()
    register_domino_api_key_request_header_provider()
    register_domino_execution_request_header_provider()

    client = MlflowClient()
    lst = client.search_registered_models()

    model_versions_to_build = []
    for m in lst:
        name = m.name
        versions = m.latest_versions

        total_versions = 0
        if versions and len(versions) > 0:
            latest_version = m.latest_versions[0]
            total_versions = latest_version.version
            for i in range(1, int(total_versions) + 1):
                v = client.get_model_version(name, i)
                tag_for_publish_to_foundry = 'EXTERNAL_TARGET_PLTR_FOUNDRY'
                if tag_for_publish_to_foundry in v.tags and v.tags[tag_for_publish_to_foundry]:
                    print(f'Relevant Model For Publishing: {name}:{i}')
                    model_versions_to_build.append(v)
                # This if of type ModelVersion - See MLFLOW API
    os.makedirs(base_path, exist_ok=True)
    download_and_test(model_versions_to_build, base_path)


