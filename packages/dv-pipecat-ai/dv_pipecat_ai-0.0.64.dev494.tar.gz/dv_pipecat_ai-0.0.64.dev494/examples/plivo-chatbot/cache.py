import ssl
from urllib.parse import urlparse

import aiocache  # type: ignore  # noqa: D100
from env_config import api_config

if api_config.REDIS_URL:
    parsed_url = urlparse(api_config.REDIS_URL)

    use_ssl = parsed_url.scheme == "rediss"

    cache_config = {
        "endpoint": parsed_url.hostname,
        "port": parsed_url.port,
        "db": int(parsed_url.path.lstrip("/")) if parsed_url.path and parsed_url.path != "/" else 0,
        "password": parsed_url.password,
    }

    if use_ssl:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        cache_config["ssl"] = ssl_context

    cache = aiocache.Cache(aiocache.RedisCache, **cache_config)
    print(f"Redis cache initialized")
else:
    cache = aiocache.Cache(aiocache.SimpleMemoryCache)
    print("Memory cache initialized")
