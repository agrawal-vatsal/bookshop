# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install --upgrade pip && pip install uv
RUN uv pip install --system --no-cache-dir -e .

COPY . .

EXPOSE 8000

CMD ["python", "amenify/manage.py", "runserver", "0.0.0.0:8000"]