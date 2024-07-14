import pandas as pd

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from dotenv import load_dotenv
import os

import warnings

warnings.filterwarnings("ignore")

load_dotenv()

password = os.getenv("ELASTIC_PASSWORD")

es = Elasticsearch(
    ["https://localhost:9200"],
    http_auth=('elastic', password),
    verify_certs=False
)

df = pd.read_csv('all_pack_df.csv')


def doc_generator(df, index_name):
    for index, row in df.iterrows():
        yield {
            "_index": index_name,
            "_source": {
                "filename": row['filename'],
                "paragraph": row['paragraphs'],
                "department": row['department']
            }
        }

index_name = 'documents'
if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name)

bulk(es, doc_generator(df, index_name))

query = {
    "query": {
        "match_all": {}
    }
}

# Проведение запроса
response = es.search(index="documents", body=query, size=1000)

# Выаод результатов для проверки корректности работы
for doc in response['hits']['hits'][:5]:
    print(doc['_source'])
