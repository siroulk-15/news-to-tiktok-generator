# 🚀 Conseils pour les Phases Suivantes (V0.2+)

## Vue d'Ensemble

Le MVP V0.1 est maintenant **complet et fonctionnel**. Voici comment procéder pour les versions suivantes.

## 📋 Leçons Apprises du MVP V0.1

### ✅ Ce qui a Bien Fonctionné

1. **Architecture Modulaire** 
   - L'interface `BaseNewsSource` a rendu facile l'ajout de sources
   - Les services découplés facilitent les tests et la maintenance
   
2. **Tests Complets**
   - 30 tests ont détecté des bugs rapidement
   - Les fixtures pytest ont simplifié la configuration
   
3. **Documentation**
   - README complet réduit les questions
   - Docstrings clairs facilitent la compréhension
   
4. **SQLAlchemy ORM**
   - Protection automatique SQL injection
   - Migrations faciles pour PostgreSQL

### ⚠️ Points à Améliorer

1. **Déduplication**
   - Le seuil 75% a généré de faux positifs
   - Envisager : weighted scoring, NLP, ML

2. **Logging**
   - SQLAlchemy logging verbose en DEBUG
   - Ajouter : structlog pour logging structuré

3. **Configuration**
   - Pas de profils (dev, prod, test)
   - Ajouter : Pydantic BaseSettings avec profiles

4. **Datetime**
   - Warnings sur `datetime.utcnow()` en Python 3.12
   - Migrer vers : `datetime.now(timezone.utc)`

## 🔄 Processus pour V0.2 (Scoring)

### Phase 1 : Planification (1-2 jours)

```
1. Définir formules de scoring
   ├─ insolite_score (0-1)
   ├─ relevance_score (0-1)
   ├─ virality_score (0-1)
   └─ confidence_score (0-1)

2. Identifier sources de données
   ├─ Métadonnées article (date, source)
   ├─ Patterns insolites (regexes, keywords)
   ├─ Popularité (mentions, shares)
   └─ Sources externes (APIs)

3. Définir seuils de filtrage
   ├─ MIN_INSOLITE_SCORE = 0.65
   ├─ MIN_CONFIDENCE_SCORE = 0.80
   └─ MIN_RELEVANCE_SCORE = 0.60
```

### Phase 2 : Implémentation (3-4 jours)

```
1. Créer app/services/scorer.py
   ├─ Classe: ScoreCalculator
   ├─ Méthodes: calculate_insolite_score()
   ├─ Méthodes: calculate_relevance_score()
   └─ Méthodes: calculate_confidence_score()

2. Ajouter dans Pydantic NewsArticle
   ├─ insolite_keywords: List[str]
   ├─ entity_confidence: float
   └─ source_reliability: float

3. Créer app/services/filters.py
   ├─ Classe: StoryFilter
   ├─ Méthodes: filter_by_score()
   ├─ Méthodes: filter_by_date()
   └─ Méthodes: filter_by_category()

4. Mettre à jour la CLI
   ├─ Nouvelle commande: python -m app score
   ├─ Nouvelle commande: python -m app filter
   └─ Nouvelle option: --min-score
```

### Phase 3 : Tests (1-2 jours)

```
1. Tests unitaires
   ├─ test_scorer.py (15+ tests)
   ├─ test_filters.py (10+ tests)
   └─ test_scoring_edge_cases.py

2. Tests d'intégration
   ├─ Vérifier scoring → filtering pipeline
   ├─ Vérifier scores dans DB
   └─ Vérifier CLI

3. Benchmarks
   ├─ Performance scoring pour 1000 articles
   ├─ Mémoire utilisée
   └─ Temps d'exécution
```

## 🎯 Stratégie pour V0.3 (Multi-sources)

### Ajouter GDELT

```python
# app/sources/gdelt.py
from app.sources.base import BaseNewsSource

class GDELTNewsSource(BaseNewsSource):
    """GDELT (Global Event Data on Locations and Tone)"""
    
    def __init__(self):
        super().__init__("GDELT")
        self.api_url = "https://gdelt.org/api/v3/events"
    
    def fetch(self):
        # Query GDELT API
        # Filter for unusual events
        # Return List[NewsArticle]
        pass
```

### Ajouter NewsAPI

```python
# app/sources/newsapi.py
class NewsAPISource(BaseNewsSource):
    """NewsAPI.org"""
    
    def __init__(self, api_key: str, category: str = "general"):
        super().__init__("NewsAPI")
        self.api_key = api_key
        self.category = category
    
    def fetch(self):
        # Query NewsAPI
        # Filter by keywords/category
        # Return List[NewsArticle]
        pass
```

### Fact-Checking Service

```python
# app/services/fact_checker.py
class FactChecker:
    """Verify claims using multiple sources"""
    
    def check_claim(self, claim: str) -> dict:
        """
        Vérify a claim against multiple sources
        
        Returns:
            {
                "status": "VERIFIED|PARTIALLY|FALSE",
                "confidence": 0.95,
                "sources": [list of verification sources]
            }
        """
        pass
```

## 🎬 Stratégie pour V0.4 (Script Gen)

### LLM Integration

```python
# app/services/script_generator.py
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

class ScriptGenerator:
    """Generate video scripts from stories"""
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.llm = OpenAI(model_name=model)
    
    def generate_script(self, story: Story) -> dict:
        """
        Generate video script for TikTok
        
        Format:
        {
            "hook": "...",
            "context": "...",
            "development": "...",
            "climax": "...",
            "conclusion": "...",
            "duration_estimate": 45  # seconds
        }
        """
        pass
```

### Text-to-Speech

```python
# app/services/tts_generator.py
class TTSGenerator:
    """Generate voice-over from script"""
    
    def __init__(self, provider: str = "elevenlabs"):
        self.provider = provider
    
    def generate_voice(
        self, 
        text: str, 
        voice_id: str = "default"
    ) -> str:
        """Generate audio file from text"""
        pass
```

### Subtitle Generation

```python
# app/services/subtitle_generator.py
class SubtitleGenerator:
    """Generate subtitles from audio"""
    
    def generate_subtitles(self, audio_path: str) -> str:
        """
        Use Whisper to generate subtitles
        
        Returns:
            Path to .srt file
        """
        pass
```

## 🎥 Stratégie pour V0.5 (Video Render)

### Media Download

```python
# app/services/media_downloader.py
class MediaDownloader:
    """Download media assets"""
    
    def download_from_pexels(self, query: str) -> List[str]:
        """Download from Pexels"""
        pass
    
    def download_from_pixabay(self, query: str) -> List[str]:
        """Download from Pixabay"""
        pass
```

### FFmpeg Integration

```python
# app/services/video_renderer.py
class VideoRenderer:
    """Render video with FFmpeg"""
    
    def render(
        self,
        clips: List[str],
        voice: str,
        subtitles: str,
        music: Optional[str] = None
    ) -> str:
        """
        Render video from components
        
        Output: MP4 1080x1920, H.264, AAC
        """
        pass
```

## 🌐 Stratégie pour V0.6 (Dashboard)

### FastAPI Web UI

```python
# app/api/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/stories")
def list_stories(status: Optional[str] = None):
    """List stories for validation"""
    pass

@app.post("/stories/{id}/approve")
def approve_story(id: str):
    """Approve story for publication"""
    pass

@app.post("/stories/{id}/reject")
def reject_story(id: str):
    """Reject story with reason"""
    pass

@app.get("/videos/{id}")
def get_video(id: str):
    """Get video preview"""
    pass
```

### Frontend (HTML/React)

```
app/static/
├── index.html
├── dashboard.html
├── css/style.css
└── js/app.js
```

## 🐦 Stratégie pour V0.7 (TikTok)

### OAuth Setup

```python
# app/services/tiktok_auth.py
class TikTokAuth:
    def get_auth_url(self):
        """Get OAuth authorization URL"""
        pass
    
    def exchange_code_for_token(self, code: str):
        """Exchange auth code for access token"""
        pass
```

### Content Publishing

```python
# app/services/tiktok_publisher.py
class TikTokPublisher:
    def publish_video(self, video_path: str, metadata: dict):
        """
        Publish video to TikTok
        
        Using: TikTok Content Posting API
        """
        pass
    
    def get_video_status(self, video_id: str):
        """Check video upload/processing status"""
        pass
```

## 📊 Stratégie pour V1.0 (Production)

### Orchestration

```python
# app/orchestrator.py
class PipelineOrchestrator:
    """Orchestrate full pipeline"""
    
    async def run_daily_cycle(self):
        """
        08:00 → Collection
        09:00 → Scoring & Filtering
        10:00 → Verification
        11:00 → Script Generation
        12:00 → Media Gathering
        13:00 → Video Rendering
        14:00 → Quality Check
        15:00 → Manual Validation
        18:00 → Publication
        """
        pass
```

### Monitoring & Alerts

```python
# app/monitoring.py
class Monitor:
    def check_pipeline_health(self):
        """Verify all services working"""
        pass
    
    def send_alerts(self, level: str, message: str):
        """Send alerts via Slack, Email, etc."""
        pass
```

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI/CD

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: pytest tests/ -v
      - name: Deploy to staging
        if: success()
        run: ./scripts/deploy-staging.sh
      - name: Deploy to production
        if: github.ref == 'refs/heads/main'
        run: ./scripts/deploy-production.sh
```

## 🛠️ Outillage Recommandé

### V0.2+
- [ ] DuckDB pour analytics
- [ ] Loguru pour structured logging
- [ ] Pydantic v2 BaseSettings avec profiles
- [ ] Pre-commit hooks

### V0.3+
- [ ] LangChain pour LLM
- [ ] Selenium pour web scraping
- [ ] BeautifulSoup pour HTML parsing

### V0.4+
- [ ] OpenAI/Anthropic API keys
- [ ] ElevenLabs pour TTS
- [ ] Whisper pour transcription

### V0.5+
- [ ] FFmpeg (system dependency)
- [ ] Pexels/Pixabay API keys
- [ ] ImageMagick pour image processing

### V0.6+
- [ ] React/Vue pour frontend
- [ ] WebSocket pour live updates
- [ ] PostgreSQL en production

### V0.7+
- [ ] TikTok API sandbox
- [ ] OAuth libraries
- [ ] Retry/backoff libraries

## 📝 Checklist pour Chaque Phase

### Pour chaque version:
- [ ] Feature branch créée
- [ ] Tests écrits avant code (TDD)
- [ ] Couverture de tests maintenue
- [ ] Documentation mise à jour
- [ ] README updaté
- [ ] CHANGELOG créé
- [ ] Code review fait
- [ ] Merge dans main
- [ ] Tag de version créé
- [ ] Release notes écrites

## 🎓 Points d'Amélioration Continus

1. **Performance**
   - Benchmark chaque version
   - Profiler le code
   - Optimiser hot paths

2. **Qualité**
   - Maintenir >80% test coverage
   - Zero hard-coded values
   - Type hints partout

3. **Sécurité**
   - Audit dépendances mensuels
   - Secrets rotation
   - Rate limiting API

4. **Documentation**
   - Architecture diagrams
   - API documentation
   - Deployment guide

## 🤝 Collaboration

Pour les agents/développeurs travaillant en parallèle:

1. **Agent 1 - Orchestrateur** (propriétaire du repo)
   - Merges les PRs
   - Maintient la cohérence
   - Releases les versions

2. **Agent 2-4** (features spécialisés)
   - Travaillent sur branches
   - Respectent l'interface
   - Écrivent tests

3. **Agent 5** (QA/Integration)
   - Tests d'intégration
   - Performance testing
   - Security scanning

---

**Status**: MVP V0.1 ✅ → Ready for V0.2
**Next Phase**: Scoring & Classification
**Estimated Timeline**: 2-3 semaines pour V0.2
