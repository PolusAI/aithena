"""
Performance benchmarks for the Clinical Aithena pipeline.

Measures and records latency/throughput for each pipeline component
against the targets defined in the project plan (CLAIT-54).

Targets:
  - Retrieval latency: <2s for 100k trials
  - Embedding generation: >100/min (>1.67/s)
  - API response time: p95 <500ms for retrieval endpoints

These tests RECORD results but only FAIL when performance is
egregiously bad (10x target). Optimization decisions are deferred
until a working prototype is in place.
"""

import os
import statistics
import time

import pytest
from sqlmodel import Session, create_engine, select, func

from polus.aithena.clinical_aithena.models import TrialGPTStudy


# Skip entire module if no database
pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="Performance tests require TEST_DATABASE_URL",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def pg_engine():
    url = os.getenv("TEST_DATABASE_URL")
    engine = create_engine(url, echo=False)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def trial_count(pg_engine):
    """Total number of TrialGPT studies in the database."""
    with Session(pg_engine) as session:
        count = session.exec(
            select(func.count()).select_from(TrialGPTStudy)
        ).one()
    return count


@pytest.fixture(scope="module")
def embedded_trial_count(pg_engine):
    """Number of trials with text_embedding."""
    with Session(pg_engine) as session:
        count = session.exec(
            select(func.count())
            .select_from(TrialGPTStudy)
            .where(TrialGPTStudy.text_embedding != None)  # noqa: E711
        ).one()
    return count


# ---------------------------------------------------------------------------
# BM25 retrieval benchmarks
# ---------------------------------------------------------------------------

class TestBM25RetrievalPerformance:
    """Benchmark BM25 (pg_search) retrieval latency."""

    QUERIES = [
        "lung cancer treatment",
        "diabetes type 2 metformin",
        "breast cancer HER2 positive immunotherapy",
        "Alzheimer disease mild cognitive impairment",
        "acute myeloid leukemia chemotherapy",
    ]

    def test_bm25_single_query_latency(self, pg_engine, trial_count):
        """BM25 single-query latency should be under 2s."""
        from polus.aithena.clinical_aithena.retrieval import PgSearchRetriever

        latencies = []
        with Session(pg_engine) as session:
            retriever = PgSearchRetriever(session)
            for query in self.QUERIES:
                start = time.perf_counter()
                results = retriever.search(query, top_n=100)
                elapsed = time.perf_counter() - start
                latencies.append(elapsed)

        avg = statistics.mean(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        max_lat = max(latencies)

        print(
            f"\n[BM25] trials={trial_count}, "
            f"avg={avg:.3f}s, p95={p95:.3f}s, max={max_lat:.3f}s"
        )

        # Soft target: <2s.  Hard fail: >20s.
        assert max_lat < 20.0, f"BM25 query took {max_lat:.1f}s (target <2s)"

    def test_bm25_batch_throughput(self, pg_engine, trial_count):
        """BM25 batch: 5 queries should complete in <10s total."""
        from polus.aithena.clinical_aithena.retrieval import PgSearchRetriever

        with Session(pg_engine) as session:
            retriever = PgSearchRetriever(session)
            start = time.perf_counter()
            for query in self.QUERIES:
                retriever.search(query, top_n=100)
            elapsed = time.perf_counter() - start

        qps = len(self.QUERIES) / elapsed
        print(f"\n[BM25 batch] {len(self.QUERIES)} queries in {elapsed:.3f}s ({qps:.1f} q/s)")

        assert elapsed < 50.0, f"BM25 batch took {elapsed:.1f}s"


# ---------------------------------------------------------------------------
# Vector retrieval benchmarks
# ---------------------------------------------------------------------------

class TestVectorRetrievalPerformance:
    """Benchmark vector (pgvector + MedCPT) retrieval latency."""

    QUERIES = [
        "lung cancer treatment",
        "diabetes type 2 metformin",
        "breast cancer HER2 positive immunotherapy",
    ]

    @pytest.fixture(scope="class")
    def medcpt_service(self):
        from polus.aithena.clinical_aithena.embeddings import MedCPTService
        try:
            service = MedCPTService()
            service.encode_query("test")
            return service
        except Exception as e:
            pytest.skip(f"MedCPT unavailable: {e}")

    def test_vector_single_query_latency(
        self, pg_engine, medcpt_service, embedded_trial_count
    ):
        """Vector single-query (encode + search) latency."""
        from polus.aithena.clinical_aithena.retrieval import VectorRetriever

        latencies_encode = []
        latencies_search = []

        with Session(pg_engine) as session:
            retriever = VectorRetriever(session, medcpt_service)
            for query in self.QUERIES:
                # Encoding
                t0 = time.perf_counter()
                embedding = medcpt_service.encode_query(query)
                t1 = time.perf_counter()
                latencies_encode.append(t1 - t0)

                # Search
                results = retriever.search(query, top_k=100)
                t2 = time.perf_counter()
                latencies_search.append(t2 - t1)

        avg_enc = statistics.mean(latencies_encode)
        avg_search = statistics.mean(latencies_search)
        print(
            f"\n[Vector] embedded_trials={embedded_trial_count}, "
            f"avg_encode={avg_enc:.3f}s, avg_search={avg_search:.3f}s, "
            f"avg_total={avg_enc + avg_search:.3f}s"
        )

        assert max(latencies_search) < 20.0, "Vector search exceeded 20s"

    def test_embedding_generation_throughput(self, medcpt_service):
        """MedCPT encoding throughput: target >100 embeddings/min."""
        texts = [
            "lung cancer stage III treatment options",
            "type 2 diabetes with renal impairment",
            "breast cancer triple-negative chemotherapy",
            "Parkinson disease dopamine agonist trial",
            "chronic obstructive pulmonary disease exacerbation",
            "acute myeloid leukemia induction therapy",
            "rheumatoid arthritis biologic treatment",
            "major depressive disorder SSRI resistance",
            "hepatocellular carcinoma immunotherapy",
            "chronic kidney disease stage 4 anemia management",
        ]

        start = time.perf_counter()
        embeddings = [medcpt_service.encode_query(t) for t in texts]
        elapsed = time.perf_counter() - start

        rate_per_min = (len(texts) / elapsed) * 60
        print(
            f"\n[MedCPT throughput] {len(texts)} queries in {elapsed:.3f}s "
            f"({rate_per_min:.0f}/min, target >100/min)"
        )

        # Hard fail if less than 10/min (10x below target)
        assert rate_per_min > 10, f"Embedding throughput {rate_per_min:.0f}/min"


# ---------------------------------------------------------------------------
# Hybrid retrieval benchmarks
# ---------------------------------------------------------------------------

class TestHybridRetrievalPerformance:
    """Benchmark hybrid (BM25 + vector + RRF) retrieval latency."""

    @pytest.fixture(scope="class")
    def medcpt_service(self):
        from polus.aithena.clinical_aithena.embeddings import MedCPTService
        try:
            return MedCPTService()
        except Exception as e:
            pytest.skip(f"MedCPT unavailable: {e}")

    def test_hybrid_single_condition_latency(
        self, pg_engine, medcpt_service, trial_count
    ):
        """Hybrid retrieval with 1 condition."""
        from polus.aithena.clinical_aithena.retrieval import HybridRetriever

        conditions = ["non-small cell lung cancer treatment"]

        with Session(pg_engine) as session:
            retriever = HybridRetriever(session, medcpt_service=medcpt_service)
            start = time.perf_counter()
            results = retriever.search(conditions, top_n=100)
            elapsed = time.perf_counter() - start

        print(
            f"\n[Hybrid 1-cond] trials={trial_count}, "
            f"results={len(results)}, latency={elapsed:.3f}s"
        )
        assert elapsed < 20.0

    def test_hybrid_multi_condition_latency(
        self, pg_engine, medcpt_service, trial_count
    ):
        """Hybrid retrieval with 5 conditions (typical patient case)."""
        from polus.aithena.clinical_aithena.retrieval import HybridRetriever

        conditions = [
            "non-small cell lung cancer stage III",
            "EGFR mutation positive",
            "first-line immunotherapy",
            "PD-L1 expression high",
            "ECOG performance status 0-1",
        ]

        with Session(pg_engine) as session:
            retriever = HybridRetriever(session, medcpt_service=medcpt_service)
            start = time.perf_counter()
            results = retriever.search(conditions, top_n=100)
            elapsed = time.perf_counter() - start

        print(
            f"\n[Hybrid 5-cond] trials={trial_count}, "
            f"results={len(results)}, latency={elapsed:.3f}s"
        )
        assert elapsed < 60.0


# ---------------------------------------------------------------------------
# API response time benchmarks
# ---------------------------------------------------------------------------

class TestAPIResponseTime:
    """Benchmark API endpoint response times."""

    @pytest.fixture(scope="class")
    def api_client(self):
        """Create a FastAPI TestClient wired to the real database."""
        from fastapi.testclient import TestClient
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker as sa_sessionmaker

        from polus.aithena.clinical_aithena.api.main import app
        from polus.aithena.clinical_aithena.api.core.database import get_session

        url = os.getenv("TEST_DATABASE_URL", "")
        async_url = url.replace("postgresql+psycopg://", "postgresql+asyncpg://")

        async def override():
            engine = create_async_engine(async_url, echo=False)
            maker = sa_sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            async with maker() as session:
                yield session
            await engine.dispose()

        app.dependency_overrides[get_session] = override
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def test_health_response_time(self, api_client):
        """GET /health should respond quickly (<500ms)."""
        latencies = []
        for _ in range(5):
            start = time.perf_counter()
            resp = api_client.get("/health")
            latencies.append(time.perf_counter() - start)
            assert resp.status_code == 200

        avg = statistics.mean(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        print(f"\n[API /health] avg={avg*1000:.0f}ms, p95={p95*1000:.0f}ms")
        assert p95 < 5.0, f"/health p95 = {p95*1000:.0f}ms"

    def test_search_response_time(self, api_client):
        """GET /search should respond in <500ms p95."""
        latencies = []
        for _ in range(5):
            start = time.perf_counter()
            resp = api_client.get("/search?page_size=10")
            latencies.append(time.perf_counter() - start)
            assert resp.status_code == 200

        avg = statistics.mean(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        print(f"\n[API /search] avg={avg*1000:.0f}ms, p95={p95*1000:.0f}ms")
        assert p95 < 5.0

    def test_search_keyword_response_time(self, api_client):
        """GET /search?keyword=cancer should respond in <1s p95."""
        latencies = []
        for _ in range(5):
            start = time.perf_counter()
            resp = api_client.get("/search?keyword=cancer&page_size=10")
            latencies.append(time.perf_counter() - start)
            assert resp.status_code == 200

        avg = statistics.mean(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        print(
            f"\n[API /search?keyword=cancer] avg={avg*1000:.0f}ms, "
            f"p95={p95*1000:.0f}ms"
        )
        assert p95 < 10.0

    def test_stats_response_time(self, api_client):
        """GET /stats should respond in <1s p95."""
        latencies = []
        for _ in range(5):
            start = time.perf_counter()
            resp = api_client.get("/stats")
            latencies.append(time.perf_counter() - start)
            assert resp.status_code == 200

        avg = statistics.mean(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        print(f"\n[API /stats] avg={avg*1000:.0f}ms, p95={p95*1000:.0f}ms")
        assert p95 < 10.0
