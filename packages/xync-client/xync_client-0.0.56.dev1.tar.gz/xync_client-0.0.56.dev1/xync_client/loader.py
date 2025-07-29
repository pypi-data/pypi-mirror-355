from dotenv import load_dotenv
from os import getenv as env
from aerich import models as amodels
from xync_schema import models as xmodels

load_dotenv()

TOKEN = env("TOKEN")
PG_DSN = f"postgres://{env('POSTGRES_USER')}:{env('POSTGRES_PASSWORD')}@{env('POSTGRES_HOST', 'xyncdbs')}:{env('POSTGRES_PORT', 5432)}/{env('POSTGRES_DB', env('POSTGRES_USER'))}"
TORM = {
    "connections": {"default": PG_DSN},
    "apps": {"models": {"models": [xmodels, amodels]}},
    "use_tz": False,
    "timezone": "UTC",
}
TG_API_ID = env("TG_API_ID")
TG_API_HASH = env("TG_API_HASH")
WSToken = env("WST")
