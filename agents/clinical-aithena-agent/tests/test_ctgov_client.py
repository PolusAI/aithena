"""
Integration tests for ClinicalTrials.gov API client.

These tests hit the real API to ensure endpoints work and responses parse correctly.
Run with: pytest tests/test_ctgov_client.py -v
"""
import pytest
from polus.aithena.clinical_aithena.clients.ctgov.client import CTGovClient


@pytest.fixture
def client():
    """Create a client instance for testing."""
    return CTGovClient()


@pytest.mark.asyncio
async def test_metadata(client):
    """Test fetching API metadata."""
    result = await client.metadata()
    assert "apiVersion" in result
    assert "dataTimestamp" in result
    print(f"API Version: {result['apiVersion']}")


@pytest.mark.asyncio
async def test_stats(client):
    """Test fetching API statistics."""
    result = await client.stats()
    assert "totalStudies" in result
    assert "averageSizeBytes" in result
    assert result["totalStudies"] > 0
    print(f"Total Studies: {result['totalStudies']}")


@pytest.mark.asyncio
async def test_studies_search(client):
    """Test searching studies with basic query."""
    response = await client.studies(
        query_cond="cancer",
        filter_overall_status=["RECRUITING"],
        page_size=5,
    )
    assert response is not None
    assert len(response.studies) <= 5
    
    # Check that we got valid study objects
    if response.studies:
        study = response.studies[0]
        assert study.protocolSection is not None
        assert study.protocolSection.identificationModule is not None
        print(f"Found study: {study.protocolSection.identificationModule.nctId}")


@pytest.mark.asyncio
async def test_studies_with_fields(client):
    """Test searching studies with specific fields."""
    response = await client.studies(
        query_cond="diabetes",
        page_size=3,
        fields=["NCTId", "BriefTitle", "OverallStatus"],
    )
    assert response is not None
    assert len(response.studies) <= 3


@pytest.mark.asyncio
async def test_single_study(client):
    """Test fetching a single study by NCT ID."""
    # Use a known NCT ID (this is a real study)
    nct_id = "NCT04852770"
    
    study = await client.study(nct_id)
    assert study is not None
    assert study.protocolSection is not None
    assert study.protocolSection.identificationModule is not None
    assert study.protocolSection.identificationModule.nctId == nct_id
    assert study.protocolSection.identificationModule.briefTitle is not None
    print(f"Study Title: {study.protocolSection.identificationModule.briefTitle}")


@pytest.mark.asyncio
async def test_single_study_with_fields(client):
    """Test fetching a single study with specific fields."""
    nct_id = "NCT04852770"
    
    study = await client.study(
        nct_id,
        fields=["NCTId", "BriefTitle", "OverallStatus"],
    )
    assert study is not None
    assert study.protocolSection is not None


@pytest.mark.asyncio
async def test_pagination_iterator(client):
    """Test pagination iterator for fetching multiple pages."""
    count = 0
    max_items = 15  # Fetch a few items across pages
    
    async for study in client.fetch_all_studies(
        query_cond="covid-19",
        page_size=5,
    ):
        count += 1
        assert study.protocolSection is not None
        if count >= max_items:
            break
    
    assert count == max_items
    print(f"Successfully iterated through {count} studies")


@pytest.mark.asyncio
async def test_field_values_stats(client):
    """Test fetching field value statistics."""
    result = await client.field_values_stats(
        types=["ENUM"],
        fields=["OverallStatus"],
    )
    assert result is not None
    assert isinstance(result, list)
    if result:
        assert "field" in result[0]
        print(f"Field stats: {result[0].get('field')}")


@pytest.mark.asyncio
async def test_list_field_sizes(client):
    """Test fetching list field sizes."""
    result = await client.list_field_sizes(fields=["Phase"])
    assert result is not None
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_studies_metadata(client):
    """Test fetching studies metadata."""
    result = await client.studies_metadata()
    assert result is not None
    assert isinstance(result, list)
    if result:
        assert "name" in result[0]
        print(f"First field: {result[0].get('name')}")


@pytest.mark.asyncio
async def test_search_areas(client):
    """Test fetching search areas."""
    result = await client.search_areas()
    assert result is not None
    assert isinstance(result, list)
    if result:
        assert "name" in result[0]


@pytest.mark.asyncio
async def test_enums(client):
    """Test fetching enum types."""
    result = await client.enums()
    assert result is not None
    assert isinstance(result, list)
    if result:
        assert "type" in result[0]
        assert "values" in result[0]
        print(f"First enum type: {result[0].get('type')}")


# Synchronous versions

def test_metadata_sync(client):
    """Test fetching API metadata (sync)."""
    result = client.metadata_sync()
    assert "apiVersion" in result
    assert "dataTimestamp" in result


def test_stats_sync(client):
    """Test fetching API statistics (sync)."""
    result = client.stats_sync()
    assert "totalStudies" in result
    assert "averageSizeBytes" in result
    assert result["totalStudies"] > 0


def test_studies_search_sync(client):
    """Test searching studies (sync)."""
    response = client.studies_sync(
        query_cond="cancer",
        filter_overall_status=["RECRUITING"],
        page_size=5,
    )
    assert response is not None
    assert len(response.studies) <= 5


def test_single_study_sync(client):
    """Test fetching a single study by NCT ID (sync)."""
    nct_id = "NCT04852770"
    
    study = client.study_sync(nct_id)
    assert study is not None
    assert study.protocolSection is not None
    assert study.protocolSection.identificationModule.nctId == nct_id


def test_pagination_iterator_sync(client):
    """Test pagination iterator (sync)."""
    count = 0
    max_items = 15
    
    for study in client.fetch_all_studies_sync(
        query_cond="covid-19",
        page_size=5,
    ):
        count += 1
        assert study.protocolSection is not None
        if count >= max_items:
            break
    
    assert count == max_items


# Test error handling

@pytest.mark.asyncio
async def test_invalid_nct_id(client):
    """Test that invalid NCT ID raises an error."""
    with pytest.raises(Exception):  # Should raise HTTP error
        await client.study("INVALID123")


@pytest.mark.asyncio
async def test_studies_response_structure(client):
    """Test that StudiesResponse structure is correct."""
    response = await client.studies(
        query_cond="alzheimer",
        page_size=2,
        count_total=True,
    )
    
    # Check response structure
    assert hasattr(response, "studies")
    assert hasattr(response, "nextPageToken")
    assert hasattr(response, "totalCount")
    
    # totalCount should be present when countTotal=True
    if response.totalCount:
        assert response.totalCount > 0
        print(f"Total matching studies: {response.totalCount}")


@pytest.mark.asyncio
async def test_study_sections(client):
    """Test that all major study sections parse correctly."""
    # Using a known study with comprehensive data
    nct_id = "NCT04852770"
    study = await client.study(nct_id)
    
    # Check major sections exist and are parsed
    assert study.protocolSection is not None
    
    # Check nested modules
    protocol = study.protocolSection
    assert protocol.identificationModule is not None
    assert protocol.statusModule is not None
    
    # Check that enums parse correctly
    if protocol.statusModule.overallStatus:
        from polus.aithena.clinical_aithena.clients.ctgov.models import Status
        assert isinstance(protocol.statusModule.overallStatus, Status)
        print(f"Status: {protocol.statusModule.overallStatus.value}")
    
    # Check nested objects
    if protocol.identificationModule.organization:
        assert protocol.identificationModule.organization.fullName is not None


@pytest.mark.asyncio
async def test_nct_id_extraction(client):
    """Test that nct_id is automatically extracted from protocolSection."""
    response = await client.studies(
        query_cond="hypertension",
        page_size=1,
    )
    
    if response.studies:
        study = response.studies[0]
        expected_nct = study.protocolSection.identificationModule.nctId
        assert study.nct_id == expected_nct
        print(f"NCT ID correctly extracted: {study.nct_id}")

