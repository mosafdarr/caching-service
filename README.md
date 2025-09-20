# Caching Service

A **FastAPI-based microservice** that provides deterministic caching for transformed payloads.  
This project simulates a production-ready **caching layer** with in-memory decorators, database-backed persistence, and containerized deployment.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
    - [Flow: POST /payload](#flow-post-payload)
    - [Flow: GET /payload/{id}](#flow-get-payloadid)
    - [Modules](#modules)
4. [Tech Stack](#tech-stack)
5. [Setup](#setup)
    - [Clone Repository](#clone-repository)
    - [Environment Variables](#environment-variables)
    - [Database](#database)
    - [Poetry Environment](#poetry-environment)
6. [Running Locally](#running-locally)
    - [Uvicorn](#uvicorn)
    - [Docker](#docker)
7. [API Reference](#api-reference)
    - [Health Check](#health-check)
    - [Create Payload](#create-payload)
    - [Read Payload](#read-payload)
8. [Testing](#testing)
    - [Unit Tests](#unit-tests)
    - [Mocking Strategy](#mocking-strategy)
9. [Development Guidelines](#development-guidelines)
10. [Future Improvements](#future-improvements)

---

## Overview

The **Caching Service** generates deterministic payloads from two lists of strings:

- **Input**: two lists of equal length.
- **Transformation**: normalization, validation, interleaving.
- **Output**: uppercase, comma-separated string.

It uses:
- **Deterministic hashing** to generate a stable `payload_id`.
- **Read-through and write-through decorators** to emulate Redis.
- **Database persistence** with SQLAlchemy for payload caching.
- **In-memory registries** to short-circuit repeated requests.

---

## Features

- **FastAPI** for endpoints and OpenAPI docs.
- **Pydantic models** for validation and serialization.
- **SQLAlchemy ORM** with Alembic migrations.
- **Logging** with simple, consistent Loguru integration.
- **Dockerized deployment** with Poetry dependency management.
- **Thorough unit tests** (mocked and non-mocked) covering edge cases.

---

## Architecture
### Flow: POST /payload

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant Decorator as @check_redis_cache
    participant Controller as CacheController
    participant Transformer as TransformerApp
    participant DB as Database

    Client->>FastAPI: POST /payload {list_1, list_2}
    FastAPI->>Decorator: calculate payload_id
    alt payload_id in cache
        Decorator-->>Client: {payload_id}
    else cache miss
        Decorator->>Controller: create(payload_id, payload, db_session)
        Controller->>DB: check existing payload_id
        alt hit
            DB-->>Controller: cached record
            Controller-->>Decorator: {payload_id}
        else miss
            Controller->>Transformer: transform(payload)
            Transformer-->>Controller: {"output": "..."}
            Controller->>DB: persist (payload_id, input, output)
            DB-->>Controller: commit
            Controller-->>Decorator: {payload_id}
        end
        Decorator-->>Client: {payload_id}
    end
```

### Flow: GET /payload/{id}

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant Decorator as @cache_read_through
    participant Controller as CacheController
    participant DB as Database

    Client->>FastAPI: GET /payload/{id}
    FastAPI->>Decorator: lookup id in REDIS_OUTPUT_CACHE
    alt hit
        Decorator-->>Client: {"output": "..."}
    else miss
        Decorator->>Controller: get(payload_id, db_session)
        Controller->>DB: query payload_id
        alt found
            DB-->>Controller: cached row
            Controller-->>Decorator: {"output": "..."}
            Decorator->>REDIS_OUTPUT_CACHE: store result
            Decorator-->>Client: {"output": "..."}
        else not found
            Controller-->>Client: 404
        end
    end
```

### Modules

- `src/index.py`: app entrypoint, health check.
- `src/settings.py`: config loader via .env.
- `libintegration/domain/models/cache_model.py`: Pydantic schemas.
- `libintegration/domain/controllers/cache_controller.py`: orchestration logic.
- `libintegration/domain/apps/transformer.py`: pure interleaving logic.
- `libintegration/domain/routers/caches.py`: FastAPI router with decorators.
- `schema/tables.py`: SQLAlchemy table definitions.
- `tests/`: unit tests for all endpoints.

---

## Tech Stack

- **Python 3.12**
- **FastAPI 0.109.0**
- **SQLAlchemy 2.0+**
- **Alembic 1.13.1**
- **Pydantic v2**
- **Loguru**
- **Docker**
- **Poetry**

---

## Setup

### Clone Repository

```bash
git clone git@github.com:mosafdarr/caching-service.git
cd caching-service
```

### Environment Variables

Create `.env` at project root:

```env
PROJECT_NAME=Caching Service
DATABASE_URL=postgresql://user:password@localhost:5432/caching_db
DATABASE_ENGINE_ECHO=false
```

### Database

Initialize migrations:

```bash
alembic upgrade head
```

### Poetry Environment

Install dependencies:

```bash
poetry install
```

---

## Running Locally

### Uvicorn

```bash
cd src
uvicorn index:app --reload --port 8000
```

### Docker

Build and run:

```bash
docker build -t caching-service .
docker run -p 8000:8000 --env-file .env caching-service
```

---

## API Reference

### Health Check

```bash
curl -X GET http://localhost:8000/health
```

**Response:**
```json
{"message": "Application's health is good."}
```

### Create Payload

**POST /payload**

**Request:**

```bash
curl -X POST http://localhost:8000/payload \
  -H "Content-Type: application/json" \
  -d '{"list_1":["first string","second string"],"list_2":["other string","another string"]}'
```

**Response:**
```json
{"payload_id": "bda123f..."}
```

### Read Payload

**GET /payload/{id}**

**Request:**

```bash
curl -X GET http://localhost:8000/payload/bda123f...
```

**Response:**
```json
{"output": "FIRST STRING, OTHER STRING, SECOND STRING, ANOTHER STRING"}
```

---

## Testing

### Unit Tests

Run full suite:

```bash
pytest -vv
```

### Mocking Strategy

- `tests/mock.py`: stores deterministic payloads and expected outputs.
- Controller calls (`CacheController.get`, `.create`) are patched.
- Hash function patched for predictable ids.

---

## Development Guidelines

Use conventional commits:
- `feat: add payload endpoint`
- `fix: correct transformer validation`
- `chore: setup dockerfile`

**Logging:** always log entry/exit points in controllers.  
**Tests:** add regression tests for every bugfix.  
**DB migrations:** always via Alembic, never manually.

---

## Future Improvements

- Replace in-memory cache (`REDIS_CACHED_IDS`, `REDIS_OUTPUT_CACHE`) with real Redis.
- Add eviction strategies (LRU, TTL).
- Load testing to validate 1M+ hits resilience.
