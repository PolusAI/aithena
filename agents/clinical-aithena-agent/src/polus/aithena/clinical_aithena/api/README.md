# Clinical Aithena API

FastAPI application for querying clinical trials data.

## Quick Start

### Prerequisites

1. Ensure you have a `.env` file in the project root with database configuration:

```bash
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/clinical_aithena
```

### Running the API

```bash
# Install dependencies
uv sync

# Start the development server
uv run uvicorn polus.aithena.clinical_aithena.api.main:app --reload

# Or with custom host/port
uv run uvicorn polus.aithena.clinical_aithena.api.main:app --host 0.0.0.0 --port 8000
```

### Accessing the API

- **Root:** http://localhost:8000/
- **Health Check:** http://localhost:8000/health
- **Search Trials:** http://localhost:8000/search
- **Statistics:** http://localhost:8000/stats
- **Interactive Docs:** http://localhost:8000/docs
- **OpenAPI Schema:** http://localhost:8000/openapi.json

## Project Structure

```
api/
├── __init__.py
├── main.py                 # FastAPI app with lifespan management
├── README.md              # This file
├── core/
│   ├── __init__.py
│   ├── config.py          # Pydantic settings
│   └── database.py        # Database session management
└── routes/
    ├── __init__.py
    └── health.py          # Health check endpoint
```

## Configuration

The API uses Pydantic Settings to load configuration from environment variables. All settings can be configured in the `.env` file (see `sample.env` for reference).

### Environment Variables

#### Database Configuration
- `DATABASE_URL`: PostgreSQL connection string
  - Default: `postgresql+psycopg://postgres:postgres@localhost:5432/clinical_aithena`
  - For async operations, the API automatically converts to `postgresql+asyncpg://`

#### API Configuration
- `API_TITLE`: API title (default: `Clinical Aithena API`)
- `API_VERSION`: API version (default: `0.1.0`)
- `API_DESCRIPTION`: API description (default: `API for querying clinical trials data`)

#### CORS Configuration
- `CORS_ORIGINS`: Comma-separated list of allowed origins
  - Default: `*` (allows all origins - use with caution in production)
  - Example: `http://localhost:3000,https://example.com`
  - For development: `*`
  - For production: Restrict to specific domains

## Development

### Adding New Routes

1. Create a new file in `api/routes/` (e.g., `trials.py`)
2. Define your router:

```python
from fastapi import APIRouter

router = APIRouter(tags=["trials"])

@router.get("/trials")
async def get_trials():
    return {"message": "List of trials"}
```

3. Include the router in `api/main.py`:

```python
from .routes import health, trials

app.include_router(health.router)
app.include_router(trials.router)
```

### Database Access

Use the `get_session` dependency to access the database:

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_session

@router.get("/example")
async def example(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Study))
    return result.scalars().all()
```

## Security

- The API uses async PostgreSQL connections via `asyncpg`
- All database queries use SQLAlchemy/SQLModel parameterized queries to prevent SQL injection
- For production deployments, configure a read-only database user for query endpoints

