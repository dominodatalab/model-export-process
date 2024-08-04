import os
import subprocess
import download_models
import time
# Kaniko build arguments

model_name = os.environ['MODEL_NAME']
model_version = os.environ['MODEL_VERSION']

download_models.main("/tmp/mlflow_models")


dockerfile_path = f"/tmp/mlflow_models/{model_name}/v{model_version}/Dockerfile"
context = f"/tmp/mlflow_models/{model_name}/v{model_version}"
destination = f"quay.io/domino/{model_name}:kv{model_version}"

#Set the working directory
os.chdir(context)
cwd = os.getcwd()

print(f'Current working directory {cwd}')

command = [
    "/kaniko/executor",
    f"--dockerfile={dockerfile_path}",
    f"--context={context}",
    f"--destination={destination}"
]

# Run Kaniko build
st = time.time()
print(f'Starting Kaniko Build')
result = subprocess.run(command, capture_output=True, text=True)
end = time.time()
total_time = (end - st)
print(f'Total time for build and push {total_time} seconds' )
# Print the output
print(result.stdout)
print(result.stderr)