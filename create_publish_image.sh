docker build --platform=linux/arm64/v8 -f ./Dockerfile -t  quay.io/domino/kaniko-based-modelregistry-push:v1 .
docker push quay.io/domino/kaniko-based-modelregistry-push:v1