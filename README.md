# The Game Academy

The Game Academy is a [Django](https://www.djangoproject.com/) project that provides a platform
for educational games.
It has been developped within the [Computational Social Choice group](https://staff.science.uva.nl/u.endriss/group.php)
of the [University of Amsterdam](https://uva.nl) and is used for public events and courses.

The project is open-source. You can find on this repository the entire source code. In the following
we provide explanations about the general structure of the code for anyone interested in developing
it further.

## Setting-Up the Scene

The game academy is provided as a finished product that can readily be installed on any server capable of
running a [Django](https://www.djangoproject.com/) project. Just use it out of the box!

If you want to develop it further, prior knowledge of [Django](https://www.djangoproject.com/) is 
recommended. In its current state, the project uses many of the Django features so a good understanding
of the inner Django mechanism is preferable.

### General Setup

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

# To silence Recaptcha errors, you need to set up 
SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']
#RECAPTCHA_PUBLIC_KEY = 'your_public_key'
#RECAPTCHA_PRIVATE_KEY = 'your_private_key'

```

Then, run the following commands:

```shell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

You're done! If you're running the project locally, run `python manage.py runserver` 
to start the Django server. Have fun!

### Games Setup

Some games require additional setup.

#### Good/Bad Game

For the good/bad games, the set of questions are added individually. There are two sets of questions:

- Riddles about Computational Social Choice (COMSOC)
- Companies Logos

Each set is added via a different command:

```shell
python manage.py goodbad_addcomsocriddles
python manage.py goodbad_addlogos
```

## Information on the Code

### Structure

#### The `gameserver` Module

#### The `GameApp` Modules

### The Story of a Request

#### `EnforceLoginScopeMiddleware`

#### Default Contexts

##### Context Initialisers

##### Game Views Inheritance

### Additional Points

#### Control of the Side Panel

### Developing a New Game

#### Setting up the `GameApp`

#### Models and Forms

#### Base Templates

#### Management Commands

#### Export Functions

### Random Answers Functions

