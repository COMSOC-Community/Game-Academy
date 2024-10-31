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

# Silence should be de-activated in production and RECAPTCHA_PUBLIC_KEY and RECAPTCHA_PRIVATE_KEY
# should be used.
SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']
#RECAPTCHA_PUBLIC_KEY = 'your_public_key'
#RECAPTCHA_PRIVATE_KEY = 'your_private_key'
RECAPTCHA_REQUIRED_SCORE = 0.85

MAX_NUM_SESSION_PER_USER = 10
MAX_NUM_GAMES_PER_SESSION = 20
MAX_NUM_RANDOM_PER_SESSION = 1000

```

Then, run the following commands:

```shell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py initialise_db
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

## Information on the Implementation

In the following we provide details about the actual implementation of the website.
Any prospective developper should read this first before starting.

### Structure

The project is organised around different Django apps.

- `core`: is the app that implements the general website. The core models (Session, Players, Game, Team)
are defined there, together with a set of views impacting the whole website.
- Additional game applications implement the game themselves, building on top of the blocks
defined in the `core` module. These modules are for instance: `numbersgame`, `goodbadgame` ...

### Core models

The basic element is a session, described in the `core.models.Session` model. A session
includes players and games that the player can play.

The `core.models.Game` model records games that are part of a session (the game logic is 
implemented in the game app).

The `core.models.Player` model records the player of a session. This model define "player 
profiles" while actual Django users are described in the `core.models.CustomUser` model.

The `core.models.Team` model records teams that have been registered for a game of a session.
A team is specific to a game and contains several players.

### Users and Player Profiles

To deal with users, we make of the provided Django user framework. The model 
`core.models.CustomUser` extends the Django `AbstractUser` to add extra information, 
notably whether the user is restricted to a session. 

Users can register to a session by creating a player profile for the session. These are
recorded in the `core.models.Player` model. A user can have a player profile in several
sessions, but no more than one profile per session. 

The users of the website can also directly create a player profile for a session. In that
case, they are restricted to the session and the `is_player` of their `core.models.CustomUser` 
instance is set to `True` (the user is created in the background without them knowing).
These users have restricted permissions (as implemented in the `EnforceLoginScopeMiddleware`
middleware).

### The Teams Logic

It is also possible to require players to submit answers as a team. In this case players
create teams, that are instance of `core.models.Team`. When a team is created, a 
team player is automatically created, so that we have an instance of `core.models.Player`
representing the team. When a user submits an answer as a team, behind the scene it is 
actually the team player that is submitting an answer.

### `GameConfig`

In order to register game apps within the website, the config for all these apps should
inherit from the `GameConfig` class (defined in `core.game_config`). This makes it possible
to create new games of the type that the app defines.

### The Story of a Request

Additional checks and processes are added by the website to the standard Django process.

- The `EnforceLoginScopeMiddleware` middleware implements all kinds of permission tests
for the users when accessing a page
- For a correct display of the pages, many elements need to be passed to the Django
templates. A set of context initialisers are defined in `core.views`.
- To ease with the integration of game apps to the website, class-based views are provided
to ensure expected behaviours.

We provide details here.

#### `EnforceLoginScopeMiddleware`

Defined in the `core.middelware` submodel, this middleware kicks in after the Django
authentication middelware. It ensures several things:

- That un-authentiated users cannot access pages that require authentication
- That sessions that are not visible can only be accessed by session admin
- That users that are restricted to a session (users with `is_player=True`) cannot access
pages outside of their session.

Not taking this middelware into account can lead to surprising behaviours. For instance, 
if you are adding a new page to the website that is meant to be accessible to anyone, 
don't forget to add it to the `OPEN_VIEWS` list of the middelware.

#### Context Initialisers

Once the request has passed all the middelwares, it reaches the view level. There, in 
order to ensure proper behaviour of the base templates the context needs to have a
long list of elements. For that reason we provide a set of context initialisers to be
used to ensure that the correct information is passed to the template. 

There are three context initialisers, all defined in `core.views`:
- `base_context_initialiser`: initialises the context for any view, this is the only 
initialiser needed for general views that do not relate to a session or a game
- `session_context_initialiser`: expands the context for views that relate to a session.
Needs to be called on top of the `base_context_initialiser`.
- `game_context_initialiser`: expands the conext for views that are within a game 
(submit answer, view results...). Needs to be called on top of the other two initialisers.

Check the code to see which value are initialised in the context through these functions.

#### Base Templates

We provide base templates that should be extended for any page.
They are all located in `core/templates/core`

- `base.html`: is the base template. All templates should extend this template.
- `base_game.html`: is the base template for a game. It extends the `base.html` template
and adds the game navigation buttons for the game.
- `base_game_index.html`: is the base template for the index page of a game. It extends
the `base_game.html` template and adds the team section when needed (if the game requires
it).
- `base_game_submit_answers.html`: is the base template for the submit_answer page of a
game. It extends the `base_game.html` template and adds the team checks if the game 
requires them.
- `core/templates/include/form_table_template.html` is the template to use for rendering
forms. Use the Django include mechanism in the following manner:

```{% include "include/form_table_template.html" with form=form_object form_type='form_type' submit_button_label='Submit Form' %}```

### Additional Points

#### Control of the Side Panel

The display of the side panel is partially controlled by JavaScript. 
The script defined in `core/static/js/side_panel.js` sets the height of the side panel
together with its position in the page (so that's it's sticky and does not hide the
header and or footer).

#### Limits

Max session

Max players

Max games

### Developing a New Game

#### Setting up the `GameApp`

#### Models and Forms

#### Game Views Inheritance

#### Base Templates

#### Management Commands

#### Export Functions

### Random Answers Functions

