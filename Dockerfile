FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install --no-cache-dir .
COPY configs ./configs
COPY schemas ./schemas
COPY dashboard ./dashboard
COPY docs ./docs
COPY reports ./reports

EXPOSE 8501
CMD ["python", "-m", "streamlit", "run", "dashboard/app.py", "--server.address=0.0.0.0"]

