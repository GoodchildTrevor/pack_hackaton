import pandas as pd
import joblib

# Загрузка данных и векторов
df = pd.read_csv('all_pack_df.csv').head(10)  # Берем только первые 10 строк
loaded_vectors = joblib.load('vectors.joblib')

# Проверка размерности векторов
vector_length = loaded_vectors.shape[1]

# Преобразование векторов в список для добавления в DataFrame
vector_list = [loaded_vectors[i].toarray()[0].tolist() for i in range(len(df))]

# Добавление векторов в DataFrame
df['vector'] = vector_list

print(df.head())

df.to_csv('final_dataframe.csv', index=False)
