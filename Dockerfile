FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /workspace
COPY requirements.txt pyproject.toml ./
RUN pip install -r requirements.txt
COPY . .
RUN pip install --no-deps -e . && useradd --create-home app && mkdir -p data reports && chown -R app:app /workspace
USER app
EXPOSE 8000 8501
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
