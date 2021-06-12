# OMAD-api

API backend for the Office of Mobility Analysis &amp; Design's experiments and prototypes

## Development Environment

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

Create a `.env` file that defines a `BIKESHARE_DATABASE_URL`. For example:

```
BIKESHARE_DATABASE_URL = postgresql://username:password@host:port/database
```

Run the API locally:

```
uvicorn src.app.main:app --reload
```
