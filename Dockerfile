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

