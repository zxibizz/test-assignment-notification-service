# Notification Service

Behold My Awesome Project!

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

License: MIT

## Settings

### General

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

### Specific

- `MAILING_SERVICE_TOKEN` - authorization token of the mailing service

## Running in Docker locally

### Build

This can take a while, especially the first time you run this particular command on your development system:

    $ docker-compose -f local.yml build

Generally, if you want to emulate production environment use production.yml instead. And this is true for any other actions you might need to perform: whenever a switch is required, just do it!

Before doing any git commit, pre-commit should be installed globally on your local machine, and then:

    $ pre-commit install

Failing to do so will result with a bunch of CI and Linter errors that can be avoided with pre-commit.

### Run

This brings up both Django and PostgreSQL. The first time it is run it might take a while to get started, but subsequent runs will occur quickly.

Open a terminal at the project root and run the following for local development:

    $ docker-compose -f local.yml up

You can also set the environment variable COMPOSE_FILE pointing to local.yml like this:

    $ export COMPOSE_FILE=local.yml

And then run:

    $ docker-compose up

To run in a detached (background) mode, just:

    $ docker-compose up -d

Here, django is the target service we are executing the commands against.

In the local environment running the container automatically triggers the database migrations to be applied.
But the task schedules creating command is something you should run manually.
Without doing this the scheduling logic will now work properly.

## Basic Commands

As with any shell command that we wish to run in our container, this is done using the

    $ docker-compose -f local.yml run --rm <command>

### Updating database schema

    $ python manage.py migrate

### Creating a superuser

    $ python manage.py createsuperuser

### Creating default task schedules

To create the predefined task schedules, use this command:

    $ python manage.py create_periodic_tasks

Keep in mind that **the execution of the command above will remove all the existing periodic tasks** if there are some.

The following tasks will be created:

- "Start upcoming mailings" - creates messages for all the currently upcoming mailings.
By default, scheduled to be executed every 10 seconds.
- "Send upcoming messages" - set the status of all the outdated messages to 'CANCELED';
posts all the actual messages in 'PENDING' and 'FAILED' statues to the mailing service.
By default, scheduled to be executed every 10 seconds.

### Type checks

Running type checks with mypy:

    $ mypy notification_service

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest

### Celery

This app comes with Celery.

To run a celery worker:

``` bash
cd notification_service
celery -A config.celery_app worker -l info
```

Please note: For Celery's import magic to work, it is important *where* the celery commands are run. If you are in the same folder with *manage.py*, you should be right.

## Deployment

The following details how to deploy this application.

### Docker

See detailed [cookiecutter-django Docker documentation](http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html).

## Пояснительная записка

В данном проекте реализованы следующие основные требования тестового задания:

- [x] Выполненное задание необходимо разместить в публичном репозитории на gitlab.com
- [x] Понятная документация по запуску проекта со всеми его зависимостями (в данном случае все устанавливается в докере само)
- [ ] Документация по API для интеграции с разработанным сервисом
(если честно этот пункт озадачил, т.к. не совсем уверен в каком виде это нужно помимо swagger. Буду рад если в фидбеке
поясните что именно ожидалось в данном пункте)
- [x] Описание реализованных методов в формате OpenAPI

Также выполнены следующие дополнительные задания:
- организовать тестирование написанного кода (тестирование не 100%, но постарался покрыть ключевую логику)
- обеспечить автоматическую сборку/тестирование с помощью GitLab CI
- подготовить docker-compose для запуска всех сервисов проекта одной командой
- сделать так, чтобы по адресу /docs/ открывалась страница со Swagger UI
- повторная отправка сообщения в случае неудачи

За основу проекта я взял cookiecutter-django, который дал мне в коробке
множество приятных фич, которые не пришлось настраивать самостоятельно, например:
- docker и docker-compose для local и production окружений
- gitlab-ci
- flake8 линтинг
- автосетап rest framework + drf spectacular + allauth + много еще чего

На самом деле в проекте еще много недоделок, которые хотелось бы довести до ума:
- фильтрация, пагинация, сортировка в апи
- аутентификация / авторизация апи
- логгирование
- админка
- внутренняя документация (докстринги)
- тесты (смоук, интеграционные)
- почистить ненужные фичи унаследованные от cookiecutter-django
- поменять менеджер пакетов (спорно на самом деле)

Но к сожалению я уже сильно вышел из лимита 4-ех часов о которых говорится в описании тестового задания.
Возможно позже я таки вернусь к проекту и доделаю его, но пока что придется довольствоваться тем что есть =)

Очень расчитываю на фидбек, особенно если найдутся совсем жесткие косяки.
