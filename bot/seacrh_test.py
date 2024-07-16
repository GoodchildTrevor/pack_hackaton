import pandas as pd
import numpy as np
import joblib
from sklearn.metrics.pairwise import cosine_similarity

# Загрузка данных
df = pd.read_csv('../database/final_dataframe.csv')
vectorizer = joblib.load('../database/tfidf_vectorizer.joblib')

# Подготовка векторов из DataFrame
# Предполагаем, что векторы сохранены в формате строки или списка, преобразуем их в numpy arrays
vector_list = np.array([np.array(eval(vec)) for vec in df['vector']])

# Создание вектора запроса
query = "отчет по агентским вознаграждениям FTL"
query_vec = vectorizer.transform([query])

# Вычисление косинусного сходства
results = cosine_similarity(vector_list, query_vec).flatten()

# Поиск индексов трех самых близких документов
top_indices = np.argsort(-results)[:3]

# Вывод результатов
for i in top_indices:
    similarity_score = results[i]
    print(f"Similarity: {similarity_score:.4f}")
    print(f"Paragraph: {df.iloc[i]['paragraphs'][:100]}...")
    if 'title' in df.columns:
        print(f"Title: {df.iloc[i]['title']}")
    print("---")
