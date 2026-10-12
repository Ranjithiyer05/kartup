import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
threads = 2
timeout = 30
accesslog = "-"
errorlog = "-"
forwarded_allow_ips = "*"
# Build the app (and create tables) once in the master before forking workers.
preload_app = True
