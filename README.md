# Foodgram
Проект доступен по [ссылке](https://gdefoodgram.ddns.net)

Документация API с актуальными адресами и возможными запросами доступна по [ссылке](http://localhost/api/docs/redoc.html)

Для ревьюера:
- Имя пользователя: manya
- Логин админки: manya@manya.com
- Пароль админки: foodgram_97

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
