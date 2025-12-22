#!/bin/bash

# Ariadne Development Environment Verification Script
# This script checks if all required services are running and accessible

echo "🔍 Ariadne Development Environment Check"
echo "========================================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
ALL_PASSED=true

# Function to check service
check_service() {
    local service_name=$1
    local check_command=$2

    echo -n "Checking $service_name... "

    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        ALL_PASSED=false
        return 1
    fi
}

# 1. Check Docker is running
echo "📦 Docker Services"
echo "------------------"
check_service "Docker daemon" "docker info"

# 2. Check Neo4j container
check_service "Neo4j container" "docker ps | grep ariadne-neo4j | grep -q Up"

# 3. Check Redis container
check_service "Redis container" "docker ps | grep ariadne-redis | grep -q Up"

# 4. Check Neo4j HTTP endpoint
check_service "Neo4j HTTP (port 7474)" "curl -s http://localhost:7474 -o /dev/null"

# 5. Check Neo4j Bolt endpoint
check_service "Neo4j Bolt (port 7687)" "nc -z localhost 7687"

# 6. Check Redis connection
check_service "Redis connection" "docker exec ariadne-redis redis-cli -a ariadne_dev_password ping | grep -q PONG"

echo ""
echo "💾 Database Services"
echo "--------------------"

# 7. Check PostgreSQL
check_service "PostgreSQL connection" "psql -U postgres -c 'SELECT 1' -t"

# 8. Check ariadne_dev database exists
if psql -U postgres -lqt | cut -d \| -f 1 | grep -qw ariadne_dev; then
    echo -e "Checking ariadne_dev database... ${GREEN}✅ OK${NC}"
else
    echo -e "Checking ariadne_dev database... ${YELLOW}⚠️  NOT FOUND${NC}"
    echo "  Run: psql -U postgres -c 'CREATE DATABASE ariadne_dev;'"
    ALL_PASSED=false
fi

# 9. Check pgvector extension
if psql -U postgres -d ariadne_dev -c '\dx' 2>/dev/null | grep -q vector; then
    echo -e "Checking pgvector extension... ${GREEN}✅ OK${NC}"
else
    echo -e "Checking pgvector extension... ${YELLOW}⚠️  NOT INSTALLED${NC}"
    echo "  Run: psql -U postgres -d ariadne_dev -c 'CREATE EXTENSION vector;'"
    ALL_PASSED=false
fi

echo ""
echo "📁 Configuration Files"
echo "----------------------"

# 10. Check .env file exists
if [ -f "../.env" ]; then
    echo -e "Checking .env file... ${GREEN}✅ OK${NC}"
else
    echo -e "Checking .env file... ${YELLOW}⚠️  NOT FOUND${NC}"
    echo "  Run: cp .env.example .env"
    echo "  Then edit .env with your actual credentials"
    ALL_PASSED=false
fi

# 11. Check docker-compose.dev.yml exists
if [ -f "../docker-compose.dev.yml" ]; then
    echo -e "Checking docker-compose.dev.yml... ${GREEN}✅ OK${NC}"
else
    echo -e "Checking docker-compose.dev.yml... ${RED}❌ NOT FOUND${NC}"
    ALL_PASSED=false
fi

echo ""
echo "🌐 Network Connectivity"
echo "-----------------------"

# 12. Check port availability
check_service "Port 7474 (Neo4j HTTP)" "lsof -i :7474 | grep -q LISTEN"
check_service "Port 7687 (Neo4j Bolt)" "lsof -i :7687 | grep -q LISTEN"
check_service "Port 6379 (Redis)" "lsof -i :6379 | grep -q LISTEN"
check_service "Port 5432 (PostgreSQL)" "lsof -i :5432 | grep -q LISTEN"

echo ""
echo "========================================"

if [ "$ALL_PASSED" = true ]; then
    echo -e "${GREEN}✅ All checks passed! Environment is ready for Phase 1.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Codex can start implementing authentication endpoints"
    echo "  2. Gemini can start implementing authentication UI"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some checks failed. Please fix the issues above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "  • Start Docker services: docker-compose -f docker-compose.dev.yml up -d"
    echo "  • Create database: psql -U postgres -c 'CREATE DATABASE ariadne_dev;'"
    echo "  • Install pgvector: psql -U postgres -d ariadne_dev -c 'CREATE EXTENSION vector;'"
    echo "  • Create .env file: cp .env.example .env"
    echo ""
    exit 1
fi
