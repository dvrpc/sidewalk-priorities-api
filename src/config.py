import os
from dotenv import find_dotenv, load_dotenv


load_dotenv(find_dotenv())

DATABASE_URL = os.environ.get("DATABASE_URL")
URL_ROOT = os.environ.get("URL_ROOT")