#образ версии Python, на которой будет работать программа
FROM python:3.10.6-alpine

#для устранения глюков и вывода log файлов
ENV PYTHONUNBUFFERED 1

#присвоение файлу requirements.txt образ файла requirements.txt
COPY ./requirements.txt requirements.txt
COPY ./bot /bot

#настройка образа postrgesql
#apt-get update -> обновить пакеты linux
#-qq -> no logs
#build-essential libpq-dev -> пакеты для установки
#netcat -> смотрящий зависимость запуска базы первоначально
RUN apt-get update && apt-get install -qq -y build-essential libpq-dev netcat --no-install-recommends

#запуск образа файла requirements.txt, где описаны пакеты используемые в проекте
RUN pop install -r requirements.txt

WORKDIR /bot

#создание нового пользователя, для избежания запуска от имени root
#созданный user не будет иметь папки home и т.д., нужен только для запуска проекта
RUN adduser --disabled-password --gecos '' user

#вход от имени user
USER user

#Запуск файла entrypoint.sh
ENTRYPOINT [ "sh", "/entrypoint.sh" ]