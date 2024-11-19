# The Game Academy

The [Game Academy](https://game-academy.org/) is a [Django](https://www.djangoproject.com/) project that provides a
platform for educational games. It has been developed within the
[Computational Social Choice Group](https://staff.science.uva.nl/u.endriss/group.php)
of the [University of Amsterdam](https://uva.nl) and can used for courses and public outreach events.

Check it out: https://game-academy.org/!

The project is open-source. You can find the entire source code in this repository.
Below, we provide explanations regarding the general structure of the code for anyone interested in
developing it further.

## Table of Content

- [Setting-Up the Scene](#setting-up-the-scene)
  - [General Setup](#general-setup)
  - [Game Setup](#game-setup)
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
- [Maintenance](#maintenance)

## Setting Up the Scene

The Game Academy is provided as a finished product that can readily be installed on any server
capable of running a [Django](https://www.djangoproject.com/) project.
Just use it out of the box!

If you want to develop it further, prior knowledge of
[Django](https://www.djangoproject.com/) is
recommended. In its current state, the project utilises many features of Django,
so a good understanding of its inner workings is preferable (but not per se needed).

### General Setup

To set up the Game Academy project, ensure you have the required dependencies installed. This project is built on [Django](https://www.djangoproject.com/). Follow these steps:

1. **Install the Requirements**: Run the following command to install the necessary packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

2. **Create Local Settings**: Create a configuration file at `gameserver/local_settings.py` with the following content:

```python
  import os
  from pathlib import Path

  BASE_DIR = Path(__file__).resolve().parent.parent

  # SECURITY WARNING: keep the secret key used in production secret!
  SECRET_KEY = 'your_secret_key_here'  # Change this!

  # SECURITY WARNING: don't run with debug turned on in production!
  DEBUG = True

  ALLOWED_HOSTS = []

  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
      }
  }

  # Silence should be deactivated in production.
  SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']
  RECAPTCHA_PUBLIC_KEY = 'your_public_key'
  RECAPTCHA_PRIVATE_KEY = 'your_private_key'
  RECAPTCHA_REQUIRED_SCORE = 0.85

  MAX_NUM_SESSION_PER_USER = 10
  MAX_NUM_GAMES_PER_SESSION = 20
  MAX_NUM_RANDOM_PER_SESSION = 1000
  ```

3. **Run Database Migrations**: Execute the following commands to set up the database and create an admin user:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py initialise_db
```

4. **Start the Server**: If running locally, you can start the server using:

```bash
python manage.py runserver
```

You're all set! Enjoy using The Game Academy!

### Game Setup

Some games require additional setup.

#### Good/Bad Game

For the Good/Bad Game, the set of questions are added individually. There are two read-made sets of questions:

- Riddles about Computational Social Choice (COMSOC)
- Company Logos

Each set is added via a different command:

```shell
python manage.py goodbad_addcomsocriddles
python manage.py goodbad_addlogos
```
## Details of the Implementation

Below, we provide details regarding the implementation of the website.
Any prospective developer should read this before starting.

### Structure of the Project

The project is organised around different Django apps.

- **`core`**: This app implements the general website. The core models (Session, Players, Game, Team)
are defined here, along with a set of views for the entire website.
- Additional game applications implement the games themselves, building on top of the components
defined in the `core` module. These modules include: `numbersgame`, `goodbadgame`, etc.

### The Core Models

The basic element is a session, described in the `core.models.Session` model. A session
includes players and games that the players can participate in.

The `core.models.Game` model records the games that are part of a session (the game logic is
implemented in the respective game app).

The `core.models.Player` model records the players of a session. This model defines "player
profiles," while actual Django users are described in the `core.models.CustomUser` model.

The `core.models.Team` model records teams that have been registered for a game within a session.
A team is linked to a given game and contains several players.

### Users and Player Profiles

To manage users, we utilise the provided Django user framework. The model
`core.models.CustomUser` extends Django's `AbstractUser` to add extra information,
notably whether the user is restricted to a session.

Users can register for a session by creating a player profile. These profiles are
recorded in the `core.models.Player` model. A user can have a player profile in several
sessions, but no more than one profile per session.

Users of the website can also directly create a player profile for a session. In this case,
they are restricted to the session, and the `is_player` attribute of their `core.models.CustomUser`
instance is set to `True` (the user is created in the background without their knowledge).
These users have restricted permissions (as implemented in the `EnforceLoginScopeMiddleware`
middleware).

### Handling Teams

It is also possible to require players to submit answers as a team. In this case, players
create teams, which are instances of `core.models.Team`. When a team is created, a
team player is automatically created, so that we have an instance of `core.models.Player`
representing the team. When a user submits an answer as a team, behind the scenes it is
actually the team player that is submitting the answer.

### `GameConfig` for Game Apps

To register game apps within the website, the configuration for all these apps should
inherit from the `GameConfig` class (defined in `core.game_config`). Without that, it is not possible
to add use the game that the app defines to a session.

### The Story of a Request

Additional checks and processes are added by the website to the standard Django process.

- The `EnforceLoginScopeMiddleware` implements various permission tests
for users when accessing a page.
- For the correct display of pages, many elements need to be passed to the Django
templates. A set of context initialisers is defined in `core.views`.
- To facilitate the integration of game apps into the website, class-based views are provided
to ensure expected behaviours.

Here are the details.

#### The Enforce Login Scope Middleware

Defined in the `core.middleware` submodule, this middleware is activated after the Django
authentication middleware. It ensures several things:

- That unauthenticated users cannot access pages that require authentication;
- That sessions that are not visible can only be accessed by session admins;
- That users who are restricted to a session (users with `is_player=True`) cannot access
pages outside of their session.

Not taking this middleware into account can lead to unexpected behaviour. For instance,
if you are adding a new page to the website that is meant to be accessible to anyone,
don't forget to add it to the `OPEN_VIEWS` list of the middleware.

#### Context Initialisers

Once the request has passed all the middleware, it reaches the view level. There, in
order to ensure the proper behaviour of the base templates, the context needs to include a
long list of elements. For that reason, we provide a set of context initialisers to
ensure that the correct information is passed to the template.

There are three context initialisers, all defined in `core.views`:
- `base_context_initializer`: initialises the context for any view. This is the only
initializer needed for general views that do not relate to a session or a game.
- `session_context_initializer`: expands the context for views that relate to a session.
It needs to be called on top of the `base_context_initializer`.
- `game_context_initializer`: expands the context for views that are within a game
(submitting answers, viewing results, etc.). It needs to be called on top of the other two initialisers.

Check the code to see which values are initialised in the context through these functions.

#### Base Templates

We provide base templates that should be extended for any page.
They are all located in `core/templates/core`.

- `base.html`: the base template. All templates should extend this template.
- `base_game.html`: the base template for a game. It extends the `base.html` template
and adds the game navigation buttons.
- `base_game_index.html`: the base template for the index page of a game. It extends
the `base_game.html` template and adds the team section when needed (if the game requires it).
- `base_game_submit_answers.html`: the base template for the submit answer page of a
game. It extends the `base_game.html` template and adds team checks if the game
requires them.
- `core/templates/include/form_table_template.html`: the template to use for rendering
forms. Use the Django include mechanism in the following manner:

```django
{% include "include/form_table_template.html" with form=form_object form_type='form_type' submit_button_label='Submit Form' %}
```
### Control of the Side Panel

The display of the side panel is partially controlled by JavaScript.
The script defined in `core/static/js/side_panel.js` sets the height of the side panel
along with its position on the page (so that it’s sticky and does not hide the
header or footer).

### Built-In Restrictions

To avoid ever-growing databases, a few restrictions are implemented. These restrictions are all
defined in the `gameserver.local_settings.py` file that you need to create when setting up the
project.

- A user cannot create more than `MAX_NUM_SESSION_PER_USER` sessions. We advise this value to be
no more than 10.
- Within a session, there cannot be more than `MAX_NUM_GAMES_PER_SESSION` games.
We advise this value to be no more than 20.
- Within a session, there cannot be more than `MAX_NUM_RANDOM_PER_SESSION` randomly generated
players. We advise this value to be no more than 1000.

Some forms are also Captcha-protected to avoid abuse. We use ReCaptcha v3, which means that for
local development you need to generate a set of keys for 127.0.0.1. These keys should be
placed in `gameserver.local_settings.py` as `RECAPTCHA_PUBLIC_KEY` and `RECAPTCHA_PRIVATE_KEY`.

## Developing a New Game

If you are planning on developing a new game, here is some information to take into account.

### Start a New Game App

We strongly recommend using the `start_game_app` management command that we provide to create a clean
folder structure tailored to your game. To do so, simply run:

```shell
python manage.py start_game_app
```

You will need to enter values for the important parameters of the app. A new directory will then be
created for your app with all the necessary files.

### Models and Forms

By default, your app will have three models: `Setting`, `Answer`, and `Result`. These models are
respectively used to store:

- `Setting`: the settings that are specific to your game;
- `Answer`: the answers submitted by the players;
- `Result`: the results of the game (data for graphs, name of the winner, etc.).

All these models are optional. If you use an `Answer` model (and you probably should), it should
have a foreign key to `core.models.Game` and a foreign key to `core.models.Player`.

If you use the `Setting` model, it must have a `OneToOneField` to `core.models.Game` called `game`.
Moreover, all the fields, except for the `game` field, should have a default value or accept null.
Indeed, when creating a game, the associated `Setting` object is automatically created without
passing any other argument than `game`.

To allow users to modify the `Setting` instances, you need to provide a form. This should
be a `ModelForm` that excludes the `game` field.

### Game Views

To assist with developing game views with the correct contexts, we provide several class-based views
for games. These views are defined in the `core/game_views.py` file.

- `GameView`: This is the basic class that sets up the context as expected for a game view.
- `GameIndexView`: This class is for the index page of a game and adjusts a few settings of the
  `GameView` context.
- `GameSubmitAnswerView`: This class is for the submit answer page of a game. It defines many methods
  to be overridden to ensure proper handling of parameters, such as running the management commands after
  submission.
- `GameResultsView`: This class is for the results page of a game. It ensures that non-authorised users
  cannot access this page.

Check the code for these views, and review examples in other game apps to see how they are used, and you'll
be able to utilise all these tools easily.

### Base Templates for Games

For the templates, extend the base templates for games described above. These are:

- `base_game.html`
- `base_game_index.html`
- `base_game_submit_answers.html`

### Management Commands

Some games require management commands to be run, typically to prepare the results page. If this is
the case, implement your management command within the app and update the value of the
`management_commands` argument passed to the `GameConfig` inside the `apps.py` file of your app.

### Export Functions

You can configure export functions to allow your game to be exported as CSV. This includes the
settings of the game and the answers submitted by players. These functions are typically implemented in
the `exportdata.py` file of your app. These functions should take two parameters: `writer`, which is
a buffer that you can write to, and `game`, which is the instance of the `Game` model that is
being exported.

Once you have implemented your export functions, update the values of the `answer_to_csv_func` and
`settings_to_csv_func` members in the `ready()` method of your `GameConfig`.

### Random Answers Generator

You can also implement a function to generate random answers for your game. This is particularly useful for
users to test the display of the game before actual answers are submitted.

To implement this functionality, populate the `create_random_answers` function in the `random.py` file of your
app. Then, update the value of the `random_answers_func` member in the `ready()` method of your `GameConfig`.

## Maintenance

To update the server:

- SSH to the server
- Add your GitHub ssh key to the agent: `ssh-add ~/.ssh/your_key`
- Move to the folder of the Django project: `cd gameserver/Game-Server`
- Pull the git: `git pull`
- If static files have been updated:
  - `source ../venv/bin/activate`
  - `python manage.py collectstatic`
- If the database needs updating:
  - `source ../venv/bin/activate`
  - `python manage.py makemigrations`
  - `python manage.py migrate`
- In any case, restart the uwsgi:
  - `cd`
  - `./restart_supervisord.sh`
- Log out of the server
