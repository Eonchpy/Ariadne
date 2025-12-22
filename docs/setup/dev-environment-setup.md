# Ariadne Development Environment Setup

## Prerequisites

- Docker Desktop installed and running
- PostgreSQL installed locally (you already have this ✅)
- Python 3.11+ (for backend)
- Node.js 18+ (for frontend)

---

## Quick Start

### 1. Start Neo4j and Redis

```bash
cd /Users/shenshunan/projects/Ariadne
docker-compose -f docker-compose.dev.yml up -d
```

### 2. Verify Services

```bash
# Check containers are running
docker-compose -f docker-compose.dev.yml ps

# Expected output:
# NAME              STATUS    PORTS
# ariadne-neo4j     Up        0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp
# ariadne-redis     Up        0.0.0.0:6379->6379/tcp
```

### 3. Access Neo4j Browser

Open in browser: http://localhost:7474

**Login Credentials**:
- Username: `neo4j`
- Password: `ariadne_dev_password`

**First-time setup**: Neo4j will ask you to change password on first login. You can keep the same password or change it (remember to update `.env` file if you change it).

### 4. Test Redis Connection

```bash
# Test Redis connection
docker exec -it ariadne-redis redis-cli -a ariadne_dev_password ping

# Expected output: PONG
```

---

## Service Details

### Neo4j (Graph Database)

- **HTTP UI**: http://localhost:7474
- **Bolt Protocol**: bolt://localhost:7687
- **Username**: neo4j
- **Password**: ariadne_dev_password
- **Memory**: 512MB initial, 2GB max
- **Plugins**: APOC (for advanced graph operations)

**Data Persistence**: Data stored in Docker volume `neo4j_data`

### Redis (Cache & Task Queue)

- **Host**: localhost
- **Port**: 6379
- **Password**: ariadne_dev_password
- **Persistence**: AOF (Append-Only File) enabled

**Data Persistence**: Data stored in Docker volume `redis_data`

### PostgreSQL (Metadata Database)

- **Host**: localhost (your local installation)
- **Port**: 5432 (default)
- **Database**: Create `ariadne_dev` database
- **Extensions needed**: pgvector

**Create Database**:
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE ariadne_dev;

# Connect to the database
\c ariadne_dev

# Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

# Verify
\dx
```

---

## Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/ariadne_dev
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=ariadne_dev_password
REDIS_URL=redis://:ariadne_dev_password@localhost:6379/0

# Application Configuration
APP_NAME=Ariadne Metadata System
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production

# JWT Configuration
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI Configuration (Phase 5)
OPENAI_API_KEY=your-openai-api-key
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4

# Celery Configuration (Phase 4)
CELERY_BROKER_URL=redis://:ariadne_dev_password@localhost:6379/1
CELERY_RESULT_BACKEND=redis://:ariadne_dev_password@localhost:6379/2
```

---

## Useful Commands

### Start Services
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### Stop Services
```bash
docker-compose -f docker-compose.dev.yml down
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f neo4j
docker-compose -f docker-compose.dev.yml logs -f redis
```

### Restart Services
```bash
docker-compose -f docker-compose.dev.yml restart
```

### Remove All Data (Clean Slate)
```bash
# WARNING: This deletes all data!
docker-compose -f docker-compose.dev.yml down -v
```

### Check Service Health
```bash
# Neo4j health
curl http://localhost:7474

# Redis health
docker exec -it ariadne-redis redis-cli -a ariadne_dev_password ping
```

---

## Troubleshooting

### Neo4j Won't Start

**Issue**: Port 7474 or 7687 already in use

**Solution**:
```bash
# Check what's using the port
lsof -i :7474
lsof -i :7687

# Kill the process or change ports in docker-compose.dev.yml
```

### Redis Connection Refused

**Issue**: Redis not accepting connections

**Solution**:
```bash
# Check Redis logs
docker-compose -f docker-compose.dev.yml logs redis

# Restart Redis
docker-compose -f docker-compose.dev.yml restart redis
```

### PostgreSQL pgvector Extension Missing

**Issue**: `CREATE EXTENSION vector` fails

**Solution**:
```bash
# Install pgvector (macOS with Homebrew)
brew install pgvector

# Or follow: https://github.com/pgvector/pgvector#installation
```

---

## Phase 1 Readiness Checklist

Before Codex starts Phase 1 implementation:

```markdown
- [ ] Docker containers running (neo4j, redis)
- [ ] Neo4j accessible at http://localhost:7474
- [ ] Redis responding to PING
- [ ] PostgreSQL database `ariadne_dev` created
- [ ] pgvector extension installed
- [ ] `.env` file created with correct credentials
- [ ] All services can connect to each other
```

**Verification Script**:
```bash
# Test all connections
echo "Testing Neo4j..."
curl -s http://localhost:7474 > /dev/null && echo "✅ Neo4j OK" || echo "❌ Neo4j FAILED"

echo "Testing Redis..."
docker exec -it ariadne-redis redis-cli -a ariadne_dev_password ping > /dev/null && echo "✅ Redis OK" || echo "❌ Redis FAILED"

echo "Testing PostgreSQL..."
psql -U postgres -d ariadne_dev -c "SELECT 1;" > /dev/null && echo "✅ PostgreSQL OK" || echo "❌ PostgreSQL FAILED"
```

---

## Next Steps

1. **Now**: Start Docker services and verify they're running
2. **Before Phase 1**: Create PostgreSQL database and install pgvector
3. **Phase 1 Week 3**: Codex will create database schemas and migrations
4. **Phase 1 Week 4**: Backend will connect to all three databases

---

**Setup Time**: ~10 minutes
**Document Version**: v1.0
**Last Updated**: 2025-12-22
