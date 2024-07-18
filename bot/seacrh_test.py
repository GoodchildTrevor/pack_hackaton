from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import os
import pandas as pd
import joblib

import warnings
warnings.filterwarnings("ignore")

load_dotenv()
password = os.getenv("ELASTIC_PASSWORD")

# Подключение к Elasticsearch
es = Elasticsearch(
    ["https://localhost:9200"],
    http_auth=('elastic', password),
    verify_certs=False
)

# Загрузка данных
df = pd.read_csv('../database/final_dataframe.csv')
vectorizer = joblib.load('../database/tfidf_vectorizer.joblib')
svd = joblib.load('../database/svd_model.joblib')

# Создание вектора запроса
query = "отчет по агентским вознаграждениям FTL"
vector = vectorizer.transform([query])
query_vector = svd.transform(vector)

# Преобразование вектора запроса в список
query_vector_list = query_vector[0].tolist()

script_query = {
    "script_score": {
        "query": {"match_all": {}},
        "script": {
            "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
            "params": {"query_vector": query_vector_list}
        }
    }
}

response = es.search(
    index="documents",
    body={
        "size": 3,
        "query": script_query,
        "_source": ["filename", "paragraph", "department"]
    }
)

print("Search results:")
for hit in response['hits']['hits']:
    print(f"ID: {hit['_id']}, Score: {hit['_score'] - 1}")
    print(f"Filename: {hit['_source']['filename']}")
    print("---")