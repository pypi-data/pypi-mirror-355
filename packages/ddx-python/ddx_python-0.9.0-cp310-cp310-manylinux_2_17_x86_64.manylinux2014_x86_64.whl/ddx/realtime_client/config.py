import os

WS_URL = os.environ.get(
    "REALTIME_API_WS_URL", "wss://exchange.derivadex.com/realtime-api"
)
DEFAULT_RETRY_DELAY = 1
MAX_RETRY_DELAY = 60
