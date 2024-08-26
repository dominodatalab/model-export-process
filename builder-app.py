import shutil
from pathlib import Path
import mlflow.sklearn
from mlflow.client import MlflowClient
from mlflow.tracking.request_header.registry import _request_header_provider_registry
import os
import mlflow
import threading
# Create a Dockerfile
import string

from domino_api_key_header_provider import DominoApiKeyRequestHeaderProvider
from domino_execution_header_provider import DominoExecutionRequestHeaderProvider
from quart import Quart, request, jsonify
app = Quart(__name__)
import subprocess
import os
DOMINO_API_KEY = "DOMINO_API_KEY"
DOMINO_RUN_ID = "DOMINO_RUN_ID"
REGISTRY_USER = "REGISTRY_USER"
REGISTRY_TOKEN = "REGISTRY_TOKEN"
REGISTRY_URL = "REGISTRY_URL"
lock = threading.Lock()
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
    #provider_name = DominoApiKeyRequestHeaderProvider()

    '''
    if provider_name in _request_header_provider_registry._registry:
        del _request_header_provider_registry._registry[provider_name]
        print(f"Provider '{provider_name}' unregistered successfully.")
    else:
        print(f"Provider '{provider_name}' not found in the registry.")
    '''
    _request_header_provider_registry.register(DominoApiKeyRequestHeaderProvider)


def register_domino_execution_request_header_provider():

    if not os.getenv("DOMINO_RUN_ID"):
        print("DOMINO_RUN_ID environment variable must be set.")
        exit(1)
    # Set X-Domino-Execution request header
    '''
    provider_name = DominoExecutionRequestHeaderProvider()
    if provider_name in _request_header_provider_registry._registry:
        del _request_header_provider_registry._registry[provider_name]
        print(f"Provider '{provider_name}' unregistered successfully.")
    else:
        print(f"Provider '{provider_name}' not found in the registry.")
    '''
    _request_header_provider_registry.register(DominoExecutionRequestHeaderProvider)


base_path = "/tmp/mlflow_models"

def predict(model_uri, features):
    loaded_model = mlflow.pyfunc.load_model(model_uri)
    return loaded_model.predict(features)


def create_file_from_template(template_string, context, output_file_path):
    template = string.Template(template_string)
    content = template.safe_substitute(context)

    directory = os.path.dirname(output_file_path)
    # Create the directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(output_file_path, 'w') as file:
        file.write(content)



def run_subprocess(command, working_dir):
    out = ""
    err = ""
    try:
        result = subprocess.run(command, cwd=working_dir, check=True, text=True, capture_output=True)
        out =  result.stdout
        err =  result.stderr
        print("Command output:", result.stdout)
        print("Command error (if any):", result.stderr)
    except subprocess.CalledProcessError as e:
        out = e.stdout
        err = e.stderr

        print(f"An error occurred: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")

    return out,err


def download_and_build(mv, base_path):

    client = MlflowClient()
    run_id = mv.run_id
    model_name = mv.name
    model_version = mv.version
    model_download_path = f'{base_path}/{model_name}/v{model_version}'
    os.makedirs(model_download_path, exist_ok=True)

    client.download_artifacts(run_id, f"", model_download_path)
    os.listdir(model_download_path)
    # Resolve files
    context = {
        'model_name': model_name,
        'model_version': model_version,
        'model_download_folder': model_download_path,
        'model_folder': mv.tags['MODEL_FOLDER'],
        'model_client_folder': mv.tags['MODEL_CLIENT_FOLDER'],
        'entry_point': mv.tags['MODEL_ENTRY_POINT'],
        'command_line': mv.tags['MODEL_EXECUTE_PATH'],
    }

    templates_folder = 'templates'
    templates = []
    if 'MODEL_TEMPLATES_FOLDER' in context:
        templates_folder = context['MODEL_TEMPLATES_FOLDER']

    templates_final_folder = f"{model_download_path}/{templates_folder}/"
    files = Path(templates_final_folder).rglob('*.template')

    for file_path in files:
        fp = str(file_path)
        t = fp.removeprefix(templates_final_folder)
        templates.append(t)

    for t in templates:
        with open(f"{templates_final_folder}/{t}", 'r') as file:
            content = file.read()
            resolved_path = t.removesuffix(".template")
            output_file = f"{model_download_path}/{resolved_path}"
            create_file_from_template(content, context, output_file)
    '''
    with open(f"{model_download_path}/{templates_folder}/Dockerfile.template", 'r') as file:
        content = file.read()
        output_file = f"{model_download_path}/Dockerfile"
        create_file_from_template(content, context, output_file)
    with open(f"{model_download_path}/{templates_folder}/create_docker_image.sh.template", 'r') as file:
        content = file.read()
        output_file = f"{model_download_path}/create_docker_image.sh"
        print(content)
        create_file_from_template(content, context, output_file)
    '''

    run_subprocess(["chmod","755","create_docker_image.sh"],working_dir=model_download_path)
    print(model_download_path)

    return run_subprocess(["sh","create_docker_image.sh"], working_dir=model_download_path)


def main(base_path,model_name,model_version):
    client = MlflowClient()
    mv = client.get_model_version(model_name, model_version)
    o,e = download_and_build(mv, base_path)
    return o,e

os.environ['MLFLOW_TRACKING_URI']='http://fake.com'
os.environ['DOMINO_USER_API_KEY']='fake'
os.environ['DOMINO_RUN_ID']='fake'
first_time = True

@app.route('/cleanup', methods=['POST'])
async def cleanup():
    perform_cleanup()

def perform_cleanup():
    home_dir = os.path.expanduser("~")
    run_subprocess(["sh","dockercleanup.sh"], working_dir=home_dir)


@app.route('/build', methods=['POST'])
async def build():
    global  first_time
    with lock:
        data = await request.get_json()
        model_name = data.get('model_name')
        model_version = data.get('model_version')
        headers = request.headers
        mlflow_tracking_uri = headers.get("MLFLOW_TRACKING_URI", "")
        domino_run_id = headers.get("DOMINO_RUN_ID", "")
        domino_api_key = headers.get("DOMINO_USER_API_KEY", "")
        registry_url = headers.get("REGISTRY_URL","")
        registry_user = headers.get("REGISTRY_USER", "")
        registry_token = headers.get("REGISTRY_TOKEN", "")

        if (not mlflow_tracking_uri or not domino_api_key or not domino_run_id
                or not registry_token or not registry_url or not registry_user):
            error = "Must include MLFLOW_TRACKING_URI, DOMINO_USER_API_KEY,DOMINO_RUN_ID and REGISTRY_TOKEN "
            return jsonify(model_name=model_name, model_version=model_version, stdout="", stderror=error)
        os.environ["MLFLOW_TRACKING_URI"] = mlflow_tracking_uri
        os.environ["DOMINO_RUN_ID"] = domino_run_id
        os.environ["DOMINO_USER_API_KEY"] = domino_api_key
        os.environ["REGISTRY_URL"] = registry_url
        os.environ["REGISTRY_USER"] = registry_user
        os.environ["REGISTRY_TOKEN"] = registry_token

        #if  first_time:
        _request_header_provider_registry._registry.clear()
        set_mlflow_tracking_uri()
        register_domino_api_key_request_header_provider()
        register_domino_execution_request_header_provider()
        first_time = False
        # End If
        base_dir = "/tmp/output"

        print(os.environ['MLFLOW_TRACKING_URI'])
        final_dir = f"{base_dir}/{model_name}/v{model_version}"
        os.makedirs("/tmp/output",exist_ok=True)

        output,error = main(base_dir,model_name,model_version)
        shutil.rmtree(final_dir)

        ##Clean up here
        print("Cleanup")
        perform_cleanup()
        return jsonify(model_name=model_name, model_version=model_version,stdout=output, stderror = error)

@app.route('/healthz')
def healthz():
   return "healthy"

if __name__ == '__main__':
    home = os.environ['HOME']
    port = os.getenv("SSL_PORT",8443)
    app.run(host='0.0.0.0', port=int(port), certfile=f"{home}/app/cert.pem", keyfile=f"{home}/app/key.pem")
