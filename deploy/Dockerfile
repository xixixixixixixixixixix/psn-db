# Full app: static site + /api/check bridge + background proxy scanner.
# Build from the psn-db directory:   docker build -f deploy/Dockerfile -t psn-db .
# Run:                               docker run -p 8080:8080 psn-db
# Override pacing/env at runtime:    -e PSN_INTERVAL=1.0 -e SCAN=0
FROM python:3.12-slim

WORKDIR /app
COPY server.py build.py index.html ./
COPY data ./data

ENV PORT=8080 \
    PSN_INTERVAL=0.35 \
    PSN_WORKERS=200 \
    SCAN=1 \
    PROXIES=data/proxies.txt

EXPOSE 8080
CMD ["python3", "-u", "server.py"]
