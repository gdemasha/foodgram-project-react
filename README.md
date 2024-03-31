# Foodgram

### Стек и инструменты:
Python, Django, Django Rest Framework, Docker, Gunicorn, NGINX, PostgreSQL, JSON, YAML, React, Telegram, API, Djoser, Postman


## Описание

Дипломный проект Фудграм - это сайт, на котором пользователи будут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

Для создания сайта был предоставлен готовый фронтенд — одностраничное SPA-приложение, написанное на фреймворке React.
Проект запущен на виртуальном удалённом сервере в трёх контейнерах: nginx, PostgreSQL и Django+Gunicorn. Заготовленный контейнер с фронтендом используется для сборки файлов.

## В ходе работы над проектом:
- настроено взаимодействие Python-приложения с внешними API-сервисами;
- создан собственный API-сервис на базе проекта Django;
- подключено SPA к бэкенду на Django через API;
- созданы образы и запущены контейнеры Docker;
- созданы, развёрнуты и запущены на сервере мультиконтейнерные приложения;
- закреплены на практике основы DevOps, включая CI&CD.

## Установка

1. Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:gdemasha/foodgram-project-react.git
cd foodgram-project-react
```
2. Cоздать и активировать виртуальное окружение:
```
# Для MacOS и Linux
python3 -m venv venv
source venv/bin/activate

# Для Windows
python -m venv venv && . venv/Scripts/activate
```
3. Создать файл .env и наполнить его данными:
```
POSTGRES_USER=<имя_пользователя_БД>
POSTGRES_PASSWORD=<пароль>
POSTGRES_DB=<имя_БД>
DB_HOST=db
DB_PORT=5432
SECRET_KEY=<'секретный ключ django'>
ALLOWED_HOSTS='localhost 127.0.0.1 <IP домен>'
DEBUG=False
```
4. Перейти в директорию backend и установить зависимости из файла requirements.txt:
```
cd backend
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```
5. Установить Docker, если у Вас его нет. Инструкция по установке: https://docs.docker.com/
6. Из директории infra выполнить команды:
```
docker compose -f docker-compose.production.yml up
docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /app/static/
docker compose -f docker-compose.production.yml exec backend python manage.py migrate
docker compose -f docker-compose.production.yml exec backend python manage.py import_ingredients ./data/ingredients.csv
```
Проект будет доступен по адресу: http://localhost:8080/recipes/
