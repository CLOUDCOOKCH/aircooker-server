import os

import uvicorn

if __name__ == "__main__":
    os.umask(0o077)
    uvicorn.run(
        "mealf.app:create_app",
        factory=True,
        host="0.0.0.0",
        port=8080,
        workers=1,
        proxy_headers=True,
        forwarded_allow_ips=os.environ.get("TRUSTED_PROXY_CIDRS", ""),
        log_level=os.environ.get("LOG_LEVEL", "info"),
        access_log=False,
        timeout_graceful_shutdown=30,
        limit_concurrency=64,
    )
