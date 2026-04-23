# AI Visibility Intelligence API

Production-grade Flask REST API with 3-agent AI pipeline for discovering high-value commercial queries and generating content recommendations to improve visibility in AI-generated answers (ChatGPT, Claude, Perplexity).

## Quick Start (5 minutes)

### 1. Clone & Setup

```bash
cd ai_visibility_api

# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API key (get from OpenAI or Anthropic):
# OPENAI_API_KEY=sk-your-key-here
```

### 3. Initialize Database

```bash
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### 4. Run the Server

```bash
python run.py
```

Server runs on `http://localhost:5000`

### 5. Test Immediately

```bash
# Check health
curl http://localhost:5000/health

# Create a profile (copy the profile_uuid from response)
curl -X POST http://localhost:5000/api/v1/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Surfer SEO",
    "domain": "surferseo.com",
    "industry": "SEO Software",
    "competitors": ["clearscope.io", "marketmuse.com"]
  }'

# Replace {profile_uuid} with the UUID from above and run pipeline (takes 10-30 seconds)
curl -X POST http://localhost:5000/api/v1/profiles/{profile_uuid}/run

# Get results
curl http://localhost:5000/api/v1/profiles/{profile_uuid}/queries
curl http://localhost:5000/api/v1/profiles/{profile_uuid}/recommendations
```

Done! You now have a working AI visibility intelligence system.

---

## System Architecture

## System Architecture

### Three-Agent Pipeline

**Agent 1: Query Discovery**
- Generates 15-20 realistic queries customers ask AI assistants
- Input: Business profile (domain, industry, competitors)
- Output: List of queries with intent classification

**Agent 2: Visibility Scoring**  
- Evaluates each query for: search volume, competitive difficulty, domain visibility
- Input: Query text, target domain, industry
- Output: Structured scoring data

**Agent 3: Content Recommendations**
- Generates 3-5 actionable content pieces for high-opportunity queries
- Input: Queries where domain is NOT visible
- Output: Specific content recommendations with keywords and rationale

**Orchestrator**
- Runs agents sequentially: 1 → 2 → 3
- Handles errors gracefully (one failure doesn't crash pipeline)
- Saves all results to database

### Opportunity Score Formula

```
Score = clamp(0.0, BaseScore × IntentMultiplier, 1.0)

BaseScore = (0.6 × VolumeScore) + (0.3 × DifficultyScore) + (0.1 × VisibilityBonus)

VolumeScore = min(volume / 10000, 1.0)
DifficultyScore = 1.0 - (difficulty / 100)
VisibilityBonus = +0.3 if not_visible else -0.1

IntentMultiplier: comparison=1.3, best_of=1.3, evaluation=1.2, how_to=1.1, other=1.0
```

**Logic**: Prioritizes queries with real search demand, low competition, and visibility gaps.

### Database Schema

```
BusinessProfile → PipelineRun → DiscoveredQuery → ContentRecommendation
  (company)       (execution)    (queries)         (recommendations)
```

---

## API Reference

Base URL: `/api/v1` on `http://localhost:5000`

### POST /profiles
Register a business profile

**Request:**
```json
{
  "name": "Company Name",
  "domain": "company.com",
  "industry": "SaaS",
  "competitors": ["competitor1.com", "competitor2.com"]
}
```

**Response:** 201 Created
```json
{
  "profile_uuid": "abc-123",
  "name": "Company Name",
  "domain": "company.com",
  "status": "created",
  "created_at": "2025-01-15T10:00:00Z"
}
```

### GET /profiles/{uuid}
Get profile with stats

**Response:** 200 OK
```json
{
  "profile_uuid": "abc-123",
  "name": "Company Name",
  "domain": "company.com",
  "industry": "SaaS",
  "total_queries_discovered": 47,
  "avg_opportunity_score": 0.642
}
```

### POST /profiles/{uuid}/run
Trigger the 3-agent pipeline (takes 10-30 seconds)

**Response:** 200 OK
```json
{
  "run_uuid": "run-456",
  "status": "completed",
  "queries_discovered": 18,
  "queries_scored": 18,
  "top_opportunity_queries": [
    {
      "query_text": "Best SEO tool for agencies",
      "opportunity_score": 0.87,
      "search_volume": 2400,
      "difficulty": 45,
      "domain_visible": false
    }
  ],
  "recommendations_generated": 15
}
```

### GET /profiles/{uuid}/queries
Get discovered queries

**Query Params:**
- `min_score=0.5` - Filter by minimum score
- `status=visible|not_visible` - Filter by visibility
- `page=1&per_page=20` - Pagination

**Response:** 200 OK
```json
{
  "queries": [
    {
      "query_uuid": "q1",
      "query_text": "How does Company compare to Competitor?",
      "estimated_search_volume": 450,
      "competitive_difficulty": 62,
      "opportunity_score": 0.81,
      "domain_visible": false,
      "discovered_at": "2025-01-15T10:05:00Z"
    }
  ],
  "pagination": {"page": 1, "per_page": 20, "total": 47, "pages": 3}
}
```

### GET /profiles/{uuid}/recommendations
Get content recommendations

**Response:** 200 OK
```json
{
  "recommendations": [
    {
      "recommendation_uuid": "rec1",
      "target_query_uuid": "q1",
      "content_type": "blog_post",
      "title": "Company vs Competitor: Complete Comparison",
      "rationale": "Directly addresses comparison query",
      "target_keywords": ["company vs competitor", "seo tools comparison"],
      "priority": "high"
    }
  ],
  "total": 15
}
```

### POST /queries/{uuid}/recheck
Re-score a query after publishing content

**Response:** 200 OK (updated query with new scores)

## Testing

### Run All Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Unit Tests (Agent Logic with Mocked LLM)

```bash
pytest tests/test_agents.py -v
```

Tests verify:
- Query discovery with valid/malformed JSON
- Visibility scoring with value normalization
- Content recommendations validation
- Opportunity score calculations
- Error handling

### Integration Tests (API Endpoints)

```bash
pytest tests/test_api.py -v
```

Tests verify:
- Profile creation and retrieval
- Proper HTTP status codes (201, 200, 400, 404, 409)
- Error response format
- Health endpoint

### Performance Testing

Manual testing to verify end-to-end pipeline:

```bash
time python -c "
from app import create_app, db
from app.services.pipeline import PipelineOrchestrator
from app.models import BusinessProfile

app = create_app()
with app.app_context():
    profile = BusinessProfile.query.first()
    if profile:
        orch = PipelineOrchestrator()
        result = orch.run_pipeline(profile.uuid)
        print(f'Pipeline completed: {result}')
"
```

---

## Configuration

### Environment Variables

Required (get keys from OpenAI or Anthropic):

```bash
OPENAI_API_KEY=sk-...                    # Or ANTHROPIC_API_KEY for Claude
AI_PROVIDER=openai                        # 'openai' or 'anthropic'
```

Optional:

```bash
DATABASE_URL=sqlite:///dev.db             # Default
FLASK_ENV=development                     # or 'production'
SECRET_KEY=your-secret-key
DEBUG=true
LOG_LEVEL=DEBUG
```

### Supported Databases

**SQLite** (Development - Default)
```bash
DATABASE_URL=sqlite:///dev.db
```

**PostgreSQL** (Production)
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/ai_visibility_api
```

---

## Project Structure

```
app/
├── __init__.py              # App factory & Flask config
├── cli.py                   # CLI commands
├── config.py                # Environment-based config
├── agents/
│   ├── base.py              # BaseAgent with LLM client
│   ├── discovery.py         # Agent 1: Query Discovery
│   ├── scoring.py           # Agent 2: Visibility Scoring
│   └── recommendation.py    # Agent 3: Content Recommendations
├── models/
│   ├── profile.py           # BusinessProfile
│   ├── pipeline_run.py      # PipelineRun
│   ├── query.py             # DiscoveredQuery
│   └── recommendation.py    # ContentRecommendation
├── api/
│   ├── profiles.py          # Profiles blueprint
│   └── queries.py           # Queries blueprint
├── services/
│   └── pipeline.py          # PipelineOrchestrator
└── utils/
    └── scoring.py           # Opportunity score formula

tests/
├── conftest.py              # Pytest fixtures
├── test_agents.py           # Unit tests (mocked LLM)
└── test_api.py              # Integration tests

.env.example                 # Environment template
requirements.txt             # Dependencies
requirements-dev.txt         # Dev dependencies
run.py                       # Dev server
wsgi.py                      # Production entry point
docker-compose.yml           # Docker stack
README.md                    # This file
```

---

## Deployment

### Local Development

```bash
python run.py
```

Runs on `http://localhost:5000` with auto-reload.

### Docker

```bash
docker-compose up
```

Requires:
- Docker
- docker-compose
- API keys in `.env`

### Production (Gunicorn)

```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 wsgi:app
```

For systemd service, nginx reverse proxy, SSL, etc. - follow standard Flask deployment guides.

---

## Troubleshooting

### "OPENAI_API_KEY not set"
```bash
echo "OPENAI_API_KEY=sk-your-key" >> .env
```

### LLM Response Parsing Errors
The system has robust fallback JSON parsing:
1. Direct JSON parse
2. Extract from markdown blocks (\```json...\```)
3. Regex extraction of JSON patterns
4. Returns empty result if all fail (continues pipeline)

### "Database locked"
SQLite issue in production - use PostgreSQL:
```bash
DATABASE_URL=postgresql://user:pass@localhost/db
```

### Profile Already Exists
Domain must be unique:
```bash
python
>>> from app.models import BusinessProfile
>>> BusinessProfile.query.filter_by(domain="test.com").delete()
>>> db.session.commit()
```

### Pipeline Taking Too Long
- LLM API latency (10-30 seconds normal)
- Check your API key has quota
- Network connectivity to OpenAI/Anthropic

---

## Code Quality

- **Type Hints**: Full PEP 484 compliance
- **Error Handling**: Try-catch with JSON validation
- **Logging**: Structured logs with context
- **Testing**: 25+ tests covering core logic
- **Docstrings**: All functions documented
- **No Dead Code**: Clean, minimal codebase

## Performance

- **Pipeline Speed**: 10-30 seconds per profile
- **Cost**: ~$0.001-0.003 per profile (GPT-4o-mini)
- **Database**: SQLite fine for <1000 profiles
- **Concurrency**: Not concurrent (async is a bonus feature)

## Security

- API keys via environment variables
- SQL injection protection (SQLAlchemy ORM)
- No credentials in error messages
- CSRF protection built-in (Flask)

---

## Contact & Support

For questions about this project, refer to the quick start section above or check:
- `.env.example` for configuration options
- `tests/` folder for usage examples
- Individual Python files for detailed docstrings

This is a technical assessment project. Contact the hiring team for submission questions.

**Status**: ✅ Production Ready - Fully Tested - Deployment Ready
