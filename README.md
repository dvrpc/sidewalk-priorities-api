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

Create a `.env` file that defines a `DATABASE_URL` or declare it as a system variable

```
DATABASE_URL = postgresql://username:password@host:port/database
```

## Run the API

Run the API locally:

```
uvicorn src.main:app --reload
```
