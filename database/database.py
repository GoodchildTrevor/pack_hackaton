from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import numpy as np
import pandas as pd
import joblib
from dotenv import load_dotenv
import os
from sklearn.decomposition import TruncatedSVD

import warnings
warnings.filterwarnings("ignore")

vector_size = 2000

svd = TruncatedSVD(n_components=vector_size)

df = pd.read_csv('all_pack_df.csv')
vectors = joblib.load('vectors.joblib')
reduced_vectors = svd.fit_transform(vectors)
vector_length = len(reduced_vectors[0])
print(vector_length)

svd = joblib.dump(svd,'svd_model.joblib')

df['reduced_vector'] = [list(vector) for vector in reduced_vectors]

df.to_csv('final_dataframe.csv')

load_dotenv()
password = os.getenv("ELASTIC_PASSWORD")

# Подключение к Elasticsearch
es = Elasticsearch(
    ["https://localhost:9200"],
    http_auth=('elastic', password),
    verify_certs=False
)

# Определение мэппинга для индекса
mapping = {
    "mappings": {
        "properties": {
            "filename": {"type": "text"},
            "paragraph": {"type": "text"},
            "department": {"type": "text"},
            "link": {"type": "text"},
            "vector": {"type": "dense_vector", "dims": vector_size}
        }
    }
}

# Генерация документов для индексации
def doc_generator(df, index_name):
    for index, row in df.iterrows():
        # Проверка на наличие ненулевых значений в векторе
        if np.any(row['reduced_vector']):  # Проверяем, что не все элементы вектора равны 0
            doc = {
                "_index": index_name,
                "_id": str(index),
                "_source": {
                    "filename": row['filename'],
                    "paragraph": row['paragraphs'],
                    "department": row['department'],
                    "link": row['link'],
                    "vector": row['reduced_vector']
                }
            }
            yield doc

index_name = 'documents'

if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)

es.indices.create(index=index_name, body=mapping)

# Индексация документов
bulk(es, doc_generator(df, index_name))

# Обновление индекса
es.indices.refresh(index=index_name)

response = es.search(
    index="documents",
    body={
        "size": 5,
        "query": {
            "match_all": {}
        },
        "_source": ["filename", "paragraph", "department", 'link', "vector"]  # Указываем необходимые поля
    }
)

# Вывод результатов
print("Search results:")
for hit in response['hits']['hits']:
    print(f"ID: {hit['_id']}, Score: {hit['_score']}")
    print(f"Filename: {hit['_source']['filename']}")
    print(f"Paragraph: {hit['_source']['paragraph']}")
    print(f"Department: {hit['_source']['department']}")
    print(f"Vector: {hit['_source']['vector']}")
    print("---")