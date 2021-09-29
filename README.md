# sidewalk-priorities-api

API backend for the Sidewalk Priorities webmap.

## Development Environment Setup

Create the virtual environment:

```
python -m venv env
```

Activate the environment:

```
source env/bin/activate
```

Install requirements:

```
pip install -r requirements.txt
```

## Configuration

Create a `.env` file that defines a `DATABASE_URL` and `URL_ROOT` as shown below, or otherwise declare them as a system variables.

```
DATABASE_URL = postgresql://username:password@host:port/database
URL_ROOT = /api/mcosp/v1
```

## Run the API

Run the API locally:

```
uvicorn src.main:app --reload
```
