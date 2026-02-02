# Appendix D: Troubleshooting Guide

## D.1 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Barcode not found | Not in any lookup provider | Enable Brave Search fallback |
| LLM timeout | Model too slow or overloaded | Increase `LLM_TIMEOUT_SECONDS` or use faster model |
| Grocy sync failed | Connection refused | Check `GROCY_API_URL` and firewall |
| Camera not working | HTTPS required for camera API | Use reverse proxy with TLS |
| Scanner input missed | Focus lost from input field | Enable kiosk mode |
| Redis connection refused | Redis not running | Start Redis container/service |

## D.2 Debug Mode

```bash
# Enable debug logging
GROCYSCAN_DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_ECHO=true

# View logs
tail -f /var/log/grocyscan/app.log | jq .

# Test database connection
python -c "from app.db.database import engine; print(engine.execute('SELECT 1'))"

# Test Grocy connection
curl -H "GROCY-API-KEY: $GROCY_API_KEY" "$GROCY_API_URL/api/system/info"

# Test lookup providers
curl "http://localhost:3334/api/v1/external/lookup/012345678901" \
  -H "X-API-Key: your-key"
```

## D.3 Health Check Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Basic health check |
| `GET /health/ready` | Readiness (DB, Redis, Grocy connected) |
| `GET /health/live` | Liveness (app running) |
| `GET /metrics` | Prometheus metrics |

## D.4 Lookup Provider Issues

### OpenFoodFacts
```bash
# Test directly
curl "https://world.openfoodfacts.org/api/v2/product/012345678901"
```

### go-upc
```bash
# Check API key validity
curl "https://go-upc.com/api/v1/code/012345678901" \
  -H "Authorization: Bearer $GOUPC_API_KEY"
```

### Brave Search
```bash
# Test Brave Search API
curl "https://api.search.brave.com/res/v1/web/search?q=UPC+012345678901" \
  -H "X-Subscription-Token: $BRAVE_API_KEY"
```

## D.5 Database Issues

### Check Connection
```bash
psql $DATABASE_URL -c "SELECT 1"
```

### Check Migrations
```bash
alembic current
alembic history
```

### Reset Database (Development Only)
```bash
alembic downgrade base
alembic upgrade head
```

## D.6 Docker Issues

### View Logs
```bash
docker-compose logs -f grocyscan-app
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Restart Services
```bash
docker-compose restart grocyscan-app
```

### Rebuild Container
```bash
docker-compose build --no-cache grocyscan-app
docker-compose up -d
```

## D.7 Performance Issues

### Slow Lookups
1. Check Redis cache hit rate in metrics
2. Increase `CACHE_TTL_DAYS`
3. Enable parallel lookup strategy

### High Memory Usage
1. Check database connection pool size
2. Reduce `DATABASE_POOL_SIZE`
3. Check for memory leaks in background jobs

### Slow Database
1. Check for missing indexes
2. Analyze slow queries with `pg_stat_statements`
3. Vacuum and analyze tables

---

## Navigation

- **Previous:** [Appendix C - Environment Variables](appendix-c-environment-variables.md)
- **Next:** [Appendix E - User Documentation](appendix-e-user-documentation.md)
- **Back to:** [README](README.md)
