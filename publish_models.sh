echo 'test'
which kaniko
python download_models.py /tmp
destination = "docker.io/test:v1"
ls /tmp

ls /tmp/pltr_foundry_model/v7

/kaniko/executor --dockerfile /tmp/pltr_foundry_model/v7/Dockerfile --context /tmp/pltr_foundry_model/v7 --destination docker.io/test:v1