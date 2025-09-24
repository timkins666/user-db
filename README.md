# User Management

A simple app to view, add and delete users.

## Usage

### tl;dr
Run `docker-compose up -d` from the project root to start all containers, then head to http://localhost:5173/ and start playing around.

### Components

#### Backend

FastAPI web server running on `localhost:8000` providing a basic API for getting, creating and deleting users.

It uses [uv](https://docs.astral.sh/uv/) for package management because it is great.

Spool it up then see http://localhost:8000/docs for API details.

Model validation imposes certain criteria when creating users:
- users must be at least 16 years old and born on or after 01/01/1990.
- `firstname` and `lastname` must be between 1 and 100 chars long, and can only contain letters, hypens and spaces.

Deleting a user is a soft delete operation so as not to break relationships if more tables are added.

#### Frontend

React frontend powered by Vite running on `localhost:5173`.

#### Postgres

Containerised postgres database running on `localhost:5432`.

## Local/dev setup

(For Mac/Linux, if you're on Windows you'll have to adapt as necessary)

Run the handy script at `scripts/dev-setup.sh` to install frontend packages and set up the venv for the backend. It also sets up some slightly clunky pre-commit hooks; they're not everyone's cup of tea but I like them.

Once everything is installed you can run the frontend and backend directly (without using Docker):
- start the postgres container with `docker-compose up -d postgres` from the project root so the backend has something to talk to
- if you don't already have `uv` installed globally on your system you'll need to activate the backend venv with `source ./backend/.venv/bin/activate`
- with `backend` as your working directory, start the backend with `uv run fastapi dev src/tmc/main.py`
- in a new terminal with `frontend` as your working directory, run `npm run dev`

### Unit tests

#### Backend

The backend tests use Pytest and an in-memory SQLite database to not interfere with users you've created in Postgres.

Run `uv run pytest` from `/backend`.

#### Frontend

The frontend tests use Jest, simply run `npm test` from `/frontend`.
