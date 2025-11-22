# Docker setup (Streamlit AI Fraud Detection Dashboard)

Build image locally:

```bash
docker build -t fraudshield .
```

Run container:

```bash
docker run -p 8501:8501 fraudshield
```

Or use docker-compose (recommended for development/live reload):

```bash
docker-compose up --build
```

Notes:

- `docker-compose.yml` mounts the repository root into the container (`./:/app`) so code changes are reflected immediately.
- The `Dockerfile` will prefer `requirements.txt` if present; otherwise it falls back to `requirements.example.txt` (provided in the repo).
- If you need additional system packages for building wheels (e.g., for `xgboost`), add them to the `apt-get install` list in the `Dockerfile`.
