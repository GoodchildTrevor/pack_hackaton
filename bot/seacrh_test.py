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


class ElasticQuery():

    def __init__(self, query, size, svd, vectorizer):
        self.query = query
        self.size = size
        self.svd = svd
        self.vectorizer = vectorizer

    def get_vector(self):
        # Создание вектора запроса
        vector = self.vectorizer.transform([self.query])
        query_vector = self.svd.transform(vector)

        # Преобразование вектора запроса в список
        query_vector_list = query_vector[0].tolist()

        return query_vector_list

    def script(self, query_vector_list):

        script_query = {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                    "params": {"query_vector": query_vector_list}
                }
            }
        }

        return script_query

    def get_response(self, query_vector_list):

        script_query = self.script(query_vector_list)

        response = es.search(
            index="documents",
            body={
                "size": self.size,
                "query": script_query,
                "_source": ["filename", "paragraph", "department"]
            }
        )

        return response

    def get_results(self):

        query_vector_list = self.get_vector()
        response = self.get_response(query_vector_list)

        for hit in response['hits']['hits']:
            score = (hit['_score'] - 1) * 100
            filename = hit['_source']['filename']

        return score, filename


query = "отчет по агентским вознаграждениям FTL"
query_to_elastic = ElasticQuery(query=query, size=1, svd=svd, vectorizer=vectorizer)
score, filename = query_to_elastic.get_results()
print(f'Самый подходящий файл: \n {filename} \n со сходством {score:.0f}%')
