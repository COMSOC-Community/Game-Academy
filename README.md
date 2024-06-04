
Setup
-----

Install the requirements described in `requirements.txt`. Then, create a `gameserver/local_settings.py` with at least the following:

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'secret'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

```

Then, run the following commands:

```shell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

```

You're done! If you're running the project locally, run `python manage.py runserver` 
to start the Django server. Have fun!

Future developement
-------------------

To consider for later:

* Static display of IPD automatas as in https://gist.github.com/mbostock/1667139 https://gist.github.com/mbostock/6526445e2b44303eebf21da3b6627320
* Move IPD display to d3 v7
* Anonymise teams in IPD global_results
* Left panel floating, with user info (https://stackoverflow.com/questions/11399537/how-do-you-make-a-div-follow-as-you-scroll)

Other (minor) issues regarding presentation (CENTIPEDE):
- Better to rows and columns (so strategy 1 goes into the rows).
- No comma before ‘and’ for a list of two winners.