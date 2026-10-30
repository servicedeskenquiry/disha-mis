# Read automatically by "gunicorn app:app" (Render start command).
# Threads let one slow request (a large upload) not block everyone else.
workers = 2
threads = 4
timeout = 120
