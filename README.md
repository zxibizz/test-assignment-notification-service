# Notification Service

The service allows to schedule mailing lists and automatically sends them out when the time comes.

This is my solution for the test assignment I haven't even got a feedback on...

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

License: MIT

## Features
The service is meant to be used via rest API, although having an internal django admin.
The description of the API can be found in 'api/docs/' of the running service.

In addition to providing an API, the service performs some periodic tasks.
Please take a look at [Creating default task schedules](#creating-default-task-schedules)

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
