# Проект: ТГ-бот для поиска подходящих документов по запросу пользователя

Ссылка на бота: https://t.me/dokumentik_bot

## Описание

Этот проект посвящен анализу и парсингу данных из различных документов с использованием Elasticsearch. В проекте решаются лексические, технические и ресурсные проблемы, связанные с обработкой данных.

## Департаменты

5 основных департаментов:
- DRK
- CMK
- OTR
- FT
- FTL 

## Предобработка текстов

### Стратегия парсинга

- Для каждого департамента из оригинального набора данных представлен свой парсер c использованием BeautifulSoup, потому что оригинальные документы представлены на языке HTML.
  
Файлы хранятся в папке notebooks\parsers

### Чанкинг и векторизация текстов

- В этом случае мы так же обрабатываем каждый департамент отдельно. На общих данных векторизаторы справлилсь существенно хуже с поиском.
- Чанкинг нужен для лучшего распознования текстов и рассчётов близости (нужен примерно одинаковый размер текстов)
- Используемый способ векторизации - tf-idf, который позволял выдавать релевантные документы (эталонный ответ всегда попадал в ТОП-5 выдачи), остальные векторизаторы давали худшие результаты.
  
Файлы хранятся в папке notebooks\vectorizers

### Обогащения словаря 

Так как в документах встречаются термины, которые имеют разные значения в различных контекстах, а также одно понятие может называться различными словами, мы использовали модель glove-wiki-gigaword-100 библиотеки gensim, что позволило нам 

## База данных: Elasticsearch

### Разворачиваем локально

- Скачиваем Elasticsearch с официального сайта https://www.elastic.co/downloads/elasticsearch
- Задаём пароль через командную строку path_to_folder\bin\elasticsearch-setup-passwords interactive
- Сохраняем пароль в файле .env (в gitignore)
- Запускаем в командой строке path_to_folder\bin\elasticsearch.bat

### Подключаемся и заливаем данные

- Весь процесс представлен в database\database.py
- Подключаемся к базе данных по адресу https://localhost:9200
- В мэппинге прописываем колонки и типы данных в них. Разреженные векторы tf-idf уплотняем с помощью TruncatedSVD из библиотеки sklearn.
- Удаляем и создаём новые индексы, после чего заливаем документы в БД.

Файлы хранятся в папке notebooks\database

## Создание ТГ-бота

- Создаём бота в BotFather и получаем токен, который сохраняем в файле .env
- Используем библиотеку python-telegram-bot (ver. 21.1.1)

### Основные функции:
- start - запуск бота
- button - кнопка для начала работы с поисковиком
- input_output - обработка запроса и выдача ответа

Файлы хранятся в папке notebooks\bot


