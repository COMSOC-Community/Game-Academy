# The Game Academy

The Game Academy is a [Django](https://www.djangoproject.com/) project that provides a platform
for educational games.
It has been developped within the [Computational Social Choice group](https://staff.science.uva.nl/u.endriss/group.php)
of the [University of Amsterdam](https://uva.nl) and is used for public events and courses.

The project is open-source. You can find on this repository the entire source code. In the following
we provide explanations about the general structure of the code for anyone interested in developing
it further.

## Table of Content

- [Setting-Up the Scene](#setting-up-the-scene)
  - [General Setup](#general-setup)
  - [Games Setup](#games-setup)
- [Details of the Implementation](#details-of-the-implementation)
  - [Structure of the Project](#structure-of-the-project)
  - [Core Models](#the-core-models)
    - [Users and Player Profiles](#users-and-player-profiles)
    - [Handling Teams](#handling-teams)
  - [GameConfig for Game Apps](#gameconfig-for-game-apps)
  - [Story of a Request](#the-story-of-a-request)
    - [Enforce Login Scope Middelware](#the-enforce-login-scope-middleware)
    - [Context Initialisers](#context-initialisers)
    - [Base Templates](#base-templates)
  - [Control of the Side Panel](#control-of-the-side-panel)
  - [Built-In Restrictions](#built-in-restrictions)
- [Developing a New Game](#developing-a-new-game)
  - [Start a New Game App](#start-a-new-game-app)
  - [Models and Forms](#models-and-forms)
  - [Game Views](#game-views)
  - [Base Templates for Games](#base-templates-for-games)
  - [Management Commands](#management-commands)
  - [Export Functions](#export-functions)
  - [Random Answer Generator](#random-answers-generator)

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

## Details of the Implementation

In the following we provide details about the actual implementation of the website.
Any prospective developper should read this first before starting.

### Structure of the Project

The project is organised around different Django apps.

- `core`: is the app that implements the general website. The core models (Session, Players, Game, Team)
are defined there, together with a set of views impacting the whole website.
- Additional game applications implement the game themselves, building on top of the blocks
defined in the `core` module. These modules are for instance: `numbersgame`, `goodbadgame` ...

### The Core Models

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

### Handling Teams

It is also possible to require players to submit answers as a team. In this case players
create teams, that are instance of `core.models.Team`. When a team is created, a 
team player is automatically created, so that we have an instance of `core.models.Player`
representing the team. When a user submits an answer as a team, behind the scene it is 
actually the team player that is submitting an answer.

### `GameConfig` for Game Apps

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

#### The Enforce Login Scope Middleware

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

### Control of the Side Panel

The display of the side panel is partially controlled by JavaScript. 
The script defined in `core/static/js/side_panel.js` sets the height of the side panel
together with its position in the page (so that's it's sticky and does not hide the
header and or footer).

### Built-In Restrictions

To avoid ever-growing databses, few restrictions are implemented. These restrictions are all
defined in the `gameserver.local_settings.py` file that you have to create when setting up the
project.

- A user cannot create more than `MAX_NUM_SESSION_PER_USER` sessions. We advise this value to be
no more than 10.
- Within a session, there cannot be more than `MAX_NUM_GAMES_PER_SESSION` games.
We advise this value to be no more than 20.
- Within a session, there cannot be more than `MAX_NUM_RANDOM_PER_SESSION` randomly generated 
players. We advise this value to be no more than 1000.

Some forms are also Captcha-protected to avoid abuses. We use ReCaptcha v3 which means that for
local development you need to generate a set of keys for 127.0.0.1. These keys should be
put in the `gameserver.local_settings.py` as `RECAPTCHA_PUBLIC_KEY` and `RECAPTCHA_PRIVATE_KEY`.

## Developing a New Game

If you are planning on developing a new game, here are some information to take into account.

### Start a New Game App

We strongly recommend you use the `start_game_app` management command that we provide to get a clean
folder structure already tailored to your game. To do so, simply run:

```shell
python manage.py start_game_app
```

You will have to enter the value for the important parameters of the app. A new directory will then
be created for your app with all the necessary files.

### Models and Forms

By default, your app will have three models: `Setting`, `Answer` and `Result`. This models are 
respectively used to store:

- `Setting`: the settings that are specific to your game
- `Answer`: the answer submitted by the players
- `Result`: the result of the game (data for graph, name of the winner etc...).

All these models are optional. If you use an `Answer` model (and you probably should), it should 
have a foreign key to `core.models.Game` and a foreign key to `core.models.Player`.

If you use the `Setting` model, it has to have a `OneToOneField` to `core.models.Game` called `game`.
Moreover, all the fields, except for the `game` field, should have a default or accept null. Indeed,
when creating a game, the associated `Setting` object is automatically created without passing
any other argument than `game`.

In order to allow users to modify the `Setting` instances, you need to provide a form. This should 
be a `ModelForm` that excludes the `game` field.

### Game Views

To help with developing game views with the right contexts, we provide several class-based views
for games. These views are defined in the `core.game_views.py` file.

- `GameView` is the basic class, it sets up the context as expected for a game view.
- `GameIndexView` is the class for the index page of a game. It adjusts few settings of the
`GameView` context.
- `GameSubmitAnswerView` is the class for the submit answer page of a game. It defines many methods
to be overriden to ensure proper handling of parameters such as running the management commands after
submitting and all.
- `GameResultsView` is the class for the result page of a game. It ensures that non-authorised users
cannot access this page.

Check the code for these views, check examples in other game apps to see how it is used and you'll
be able to use all these tools easily.

### Base Templates for Games

For the templates, extend the base templates for games described above. These are:

- `base_game.html`,
- `base_game_index.html`,
- `base_game_submit_answers.html`.

### Management Commands

Some games require management commands to be run, typically to prepare the result page. If this is 
the case, implement your management command within the app and update the value of the
`management_commands` argument passed to the GameConfig inside the `apps.py` file of your app.

### Export Functions

You can configure export functions to allow your game to be exported as CSV. This concerns the 
settings of the game and the answers of the game. These functions are typically implemented in
the `exportdata.py` file of your app. These function should take two parameters: `writer` which is
a buffer that you can write to, and `game` which is the instance of the `Game` model that is
being exported.

Once you have implemented your export functions, update the value of the `answer_to_csv_func` and
`settings_to_csv_func` members in the `ready()` of your `GameConfig`.

### Random Answers Generator

You can also implement function to generate random answers to your game. This is useful notably for
users to test the display of the game before actual answers are submitted.

To implement such functionality, populate the `create_random_answers` of the `random.py` file of your
app. Then, update the value of the `random_answers_func` member in the `ready()` of your `GameConfig`.