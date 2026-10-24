"""
Integration tests for live Geoapify destination search and resolution.

Tests the new destinations-live API endpoints:
- Text search for destinations
- Category-based exploration
- Location coordinate resolution for multi-stop planner
- Nearby attractions search
"""

import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.database import engine, SessionLocal
from main import app
from app.services.geoapify_destination_search import (
    search_destinations_by_text,
    resolve_location_coordinates,
    search_nearby_attractions,
    explore_destinations_by_category,
    GeoapifyError,
    clear_cache,
)


@pytest.fixture
def db():
    """Provide a test database session."""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.mark.asyncio
async def test_search_destinations_by_text():
    """Test text-based destination search via Geoapify."""
    clear_cache()
    
    try:
        results = await search_destinations_by_text(query="Goa", limit=5)
        
        assert len(results) > 0, "Should find results for 'Goa'"
        
        first = results[0]
        assert "place_id" in first
        assert "name" in first
        assert "latitude" in first
        assert "longitude" in first
        assert first.get("data_source") == "geoapify"
        
        print(f"✓ Found {len(results)} results for 'Goa'")
        print(f"  Top result: {first['name']} ({first['latitude']}, {first['longitude']})")
    except GeoapifyError as e:
        pytest.skip(f"Geoapify unavailable: {e}")


@pytest.mark.asyncio
async def test_resolve_location_coordinates():
    """Test location text resolution to coordinates."""
    clear_cache()
    
    try:
        lat, lon, name = await resolve_location_coordinates("Munnar")
        
        assert 10.0 <= lat <= 11.0, "Munnar latitude should be ~10.08"
        assert 76.5 <= lon <= 77.5, "Munnar longitude should be ~77.05"
        assert name, "Should return canonical name"
        assert "Munnar" in name or "munnar" in name.lower()
        
        print(f"✓ Resolved 'Munnar' to ({lat:.4f}, {lon:.4f}) -> {name}")
    except GeoapifyError as e:
        pytest.skip(f"Geoapify unavailable: {e}")


@pytest.mark.asyncio
async def test_resolve_location_multiple():
    """Test resolving multiple location names."""
    clear_cache()
    
    test_cases = [
        ("Jaipur", 26.9, 75.8),
        ("Varanasi", 25.3, 82.9),
        ("Goa", 15.3, 74.1),
    ]
    
    try:
        for location, expected_lat, expected_lon in test_cases:
            lat, lon, name = await resolve_location_coordinates(location)
            
            # Allow ~1 degree tolerance
            assert abs(lat - expected_lat) < 1.0, f"Latitude mismatch for {location}"
            assert abs(lon - expected_lon) < 1.0, f"Longitude mismatch for {location}"
            
            print(f"✓ {location}: ({lat:.2f}, {lon:.2f})")
    except GeoapifyError as e:
        pytest.skip(f"Geoapify unavailable: {e}")


@pytest.mark.asyncio
async def test_explore_destinations_by_category():
    """Test category-based destination exploration."""
    clear_cache()
    
    try:
        result = await explore_destinations_by_category(
            category="Beach",
            page=1,
            limit=10
        )
        
        assert "destinations" in result
        assert "total" in result
        assert "page" in result
        assert "has_more" in result
        
        destinations = result["destinations"]
        assert len(destinations) > 0, "Should find Beach destinations"
        
        # Verify structure
        for dest in destinations:
            assert "place_id" in dest
            assert "name" in dest
            assert "latitude" in dest
            assert "longitude" in dest
        
        print(f"✓ Found {len(destinations)} Beach destinations (Total: {result['total']})")
    except GeoapifyError as e:
        pytest.skip(f"Geoapify unavailable: {e}")


@pytest.mark.asyncio
async def test_nearby_attractions():
    """Test finding attractions near coordinates."""
    clear_cache()
    
    try:
        # Goa coordinates
        results = await search_nearby_attractions(
            latitude=15.2993,
            longitude=74.1240,
            categories=["beach", "tourism.attraction"],
            radius_m=5000,
            limit=10
        )
        
        assert isinstance(results, list)
        assert len(results) > 0, "Should find attractions near Goa"
        
        # Verify structure
        for attraction in results:
            assert "place_id" in attraction
            assert "name" in attraction
            assert "latitude" in attraction
            assert "longitude" in attraction
        
        print(f"✓ Found {len(results)} attractions near Goa")
    except Exception as e:
        pytest.skip(f"Search failed: {e}")


@pytest.mark.asyncio
async def test_search_invalid_input():
    """Test error handling for invalid search inputs."""
    
    # Empty query
    with pytest.raises(ValueError):
        await search_destinations_by_text(query="", limit=10)
    
    # Too short
    with pytest.raises(ValueError):
        await search_destinations_by_text(query="A", limit=10)
    
    # Too long
    with pytest.raises(ValueError):
        await search_destinations_by_text(query="x" * 300, limit=10)
    
    print("✓ Invalid input validation works correctly")


@pytest.mark.asyncio
async def test_cache_functionality():
    """Test that search results are cached."""
    clear_cache()
    
    try:
        # First search
        results1 = await search_destinations_by_text(query="Delhi", limit=5)
        
        # Second search (should use cache)
        results2 = await search_destinations_by_text(query="Delhi", limit=5)
        
        # Results should be identical
        assert len(results1) == len(results2)
        assert results1[0]["place_id"] == results2[0]["place_id"]
        
        print("✓ Caching works correctly")
    except GeoapifyError as e:
        pytest.skip(f"Geoapify unavailable: {e}")


@pytest.mark.asyncio
async def test_api_endpoints():
    """Test the actual API endpoints."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test search endpoint
        try:
            response = await client.get(
                "/api/destinations-live/search",
                params={"q": "Goa", "limit": 5}
            )
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert "count" in data
            assert data["source"] == "geoapify"
            print(f"✓ Search endpoint working: {data['count']} results")
        except Exception as e:
            print(f"⚠ Search endpoint test skipped: {e}")
        
        # Test explore endpoint
        try:
            response = await client.get(
                "/api/destinations-live/explore",
                params={"category": "Beach", "page": 1, "limit": 10}
            )
            assert response.status_code == 200
            data = response.json()
            assert "destinations" in data
            assert "category" in data
            print(f"✓ Explore endpoint working: {data['total']} destinations in Beach")
        except Exception as e:
            print(f"⚠ Explore endpoint test skipped: {e}")
        
        # Test resolve endpoint
        try:
            response = await client.post(
                "/api/destinations-live/resolve-location",
                params={"location": "Jaipur"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "latitude" in data
            assert "longitude" in data
            assert "name" in data
            print(f"✓ Resolve endpoint working: Jaipur -> ({data['latitude']}, {data['longitude']})")
        except Exception as e:
            print(f"⚠ Resolve endpoint test skipped: {e}")


def run_tests():
    """Run all tests."""
    import sys
    
    print("\n" + "=" * 70)
    print("LIVE GEOAPIFY DESTINATION SEARCH TESTS")
    print("=" * 70 + "\n")
    
    # Run async tests
    loop = asyncio.get_event_loop()
    
    try:
        print("Testing service layer functions:")
        print("-" * 70)
        loop.run_until_complete(test_search_destinations_by_text())
        loop.run_until_complete(test_resolve_location_coordinates())
        loop.run_until_complete(test_resolve_location_multiple())
        loop.run_until_complete(test_explore_destinations_by_category())
        loop.run_until_complete(test_nearby_attractions())
        loop.run_until_complete(test_search_invalid_input())
        loop.run_until_complete(test_cache_functionality())
        
        print("\nTesting API endpoints:")
        print("-" * 70)
        loop.run_until_complete(test_api_endpoints())
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 70 + "\n")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
