import os
import sys
import mlflow
from mlflow.tracking import MlflowClient
import pandas as pd

model_base_path = os.environ['MODEL_PATH']

def predict(model_uri,features):
    loaded_model = mlflow.pyfunc.load_model(model_uri)
    return loaded_model.predict(features)

#Load the model and predict
d = pd.read_json(f'{model_base_path}/client/features.json', orient='records', lines=True)
model_uri_saved = f'{model_base_path}/model'
p = predict(model_uri_saved,d)

print(f'Model input {d}')
print(f'Model output {p}')

'''
import mlflow
from pyspark.sql.functions import struct, col
# Load model as a Spark UDF. Override result_type if the model does not return double values.
loaded_model = mlflow.pyfunc.spark_udf(spark, "/app/model/sklearn-model", result_type='double')

# Predict on a Spark DataFrame.
df.withColumn('predictions', loaded_model(struct(*map(col, df.columns))))
'''