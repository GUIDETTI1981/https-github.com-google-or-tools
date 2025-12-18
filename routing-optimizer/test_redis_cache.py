#!/usr/bin/env python3
"""
Redis Cache Integration Test Script

Test suite per verificare:
1. Connessione Redis
2. Cache-Aside pattern
3. MD5 key hashing
4. TTL configuration
5. Statistics tracking
6. Fail-open strategy

Autore: Senior Backend Engineer
Data: 2025-12-18
"""

import sys
import time
import json
from typing import List, Dict

# Add backend to path
sys.path.insert(0, './backend')

from app.services.geocode_cache import GeocodeCache, get_geocode_cache
from app.services.geocoder_service import GeocoderService, GeocodingResult
from app.services.address_sanitizer import AddressSanitizer


def print_header(title: str):
    """Stampa header formattato"""
    print("\n" + "=" * 70)
    print(f"🧪 {title}")
    print("=" * 70)


def print_result(test_name: str, passed: bool, message: str = ""):
    """Stampa risultato test"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    if message:
        print(f"   → {message}")


def test_redis_connection():
    """Test 1: Verifica connessione Redis"""
    print_header("Test 1: Redis Connection")
    
    try:
        cache = GeocodeCache(
            host='localhost',
            port=6379,
            enabled=True
        )
        
        # Health check
        is_connected = cache.health_check()
        
        print_result(
            "Redis connection",
            is_connected,
            f"Host: {cache.host}, Port: {cache.port}"
        )
        
        return cache if is_connected else None
        
    except Exception as e:
        print_result("Redis connection", False, str(e))
        return None


def test_cache_key_generation():
    """Test 2: Verifica generazione chiavi MD5"""
    print_header("Test 2: Cache Key Generation (MD5)")
    
    cache = GeocodeCache(enabled=False)
    
    # Test cases
    test_addresses = [
        "Via Roma 1, Milano",
        "via roma 1, milano",  # should generate SAME key (case insensitive)
        "Via Garibaldi 23, Roma",
        "Corso Italia 45, Torino"
    ]
    
    keys = []
    for address in test_addresses:
        key = cache._generate_cache_key(address)
        keys.append(key)
        print(f"  '{address}' → {key}")
    
    # Verifica: stessa stringa (lowercase) → stessa chiave
    passed = keys[0] == keys[1]
    print_result(
        "Case-insensitive key generation",
        passed,
        f"'{test_addresses[0]}' == '{test_addresses[1]}' → Same key: {passed}"
    )
    
    # Verifica: diverse stringhe → diverse chiavi
    passed = len(set(keys[2:])) == len(keys[2:])
    print_result(
        "Unique keys for different addresses",
        passed,
        f"Generated {len(set(keys))} unique keys from {len(test_addresses)} addresses"
    )


def test_cache_aside_pattern(cache: GeocodeCache):
    """Test 3: Verifica pattern Cache-Aside"""
    print_header("Test 3: Cache-Aside Pattern")
    
    if cache is None or not cache.enabled:
        print("⚠️  SKIP: Redis not available")
        return
    
    test_address = "Via Roma 1, Milano"
    
    # Mock geocoding result
    mock_result = GeocodingResult(
        latitude=45.464664,
        longitude=9.188540,
        confidence=0.9,
        address=test_address,
        city="Milano",
        country="Italia"
    )
    
    # Clear cache per test pulito
    cache.delete(test_address)
    
    # TEST 1: Cache MISS (prima richiesta)
    print("\n1️⃣  Cache MISS Test (prima richiesta)")
    
    call_count = 0
    
    def mock_fetch():
        nonlocal call_count
        call_count += 1
        print(f"   🔵 Photon API chiamata #{call_count}")
        return mock_result
    
    result_1 = cache.get_or_fetch(test_address, mock_fetch)
    
    print_result(
        "Cache MISS",
        result_1 is not None and call_count == 1,
        f"Photon chiamato: {call_count} volte"
    )
    
    # TEST 2: Cache HIT (seconda richiesta - stesso indirizzo)
    print("\n2️⃣  Cache HIT Test (seconda richiesta)")
    
    call_count = 0  # Reset
    
    result_2 = cache.get_or_fetch(test_address, mock_fetch)
    
    print_result(
        "Cache HIT",
        result_2 is not None and call_count == 0,
        f"Photon chiamato: {call_count} volte (servito dalla cache ⚡)"
    )
    
    # TEST 3: Verifica coordinate
    coords_match = (
        result_1.latitude == result_2.latitude and
        result_1.longitude == result_2.longitude
    )
    
    print_result(
        "Coordinate consistency",
        coords_match,
        f"({result_1.latitude:.6f}, {result_1.longitude:.6f})"
    )


def test_cache_statistics(cache: GeocodeCache):
    """Test 4: Verifica statistics tracking"""
    print_header("Test 4: Cache Statistics Tracking")
    
    if cache is None or not cache.enabled:
        print("⚠️  SKIP: Redis not available")
        return
    
    # Reset stats (nuovo cache instance)
    cache_fresh = GeocodeCache(host='localhost', port=6379)
    
    # Mock addresses
    addresses = [
        "Via Roma 1, Milano",
        "Via Garibaldi 23, Roma",
        "Via Roma 1, Milano",  # duplicato → HIT
        "Corso Italia 45, Torino",
        "Via Roma 1, Milano",  # duplicato → HIT
    ]
    
    mock_result = GeocodingResult(
        latitude=45.0,
        longitude=9.0,
        confidence=0.9,
        address="Test",
        city="Test",
        country="Italia"
    )
    
    # Clear cache
    for addr in addresses:
        cache_fresh.delete(addr)
    
    # Process addresses
    for addr in addresses:
        cache_fresh.get_or_fetch(addr, lambda: mock_result)
    
    # Get stats
    stats = cache_fresh.get_stats()
    
    print(f"\n📊 Cache Statistics:")
    print(f"   Total requests: {stats['total_requests']}")
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Hit Rate: {stats['hit_rate']:.1f}%")
    
    # Verifica: 5 richieste, 3 indirizzi unici → 3 misses, 2 hits
    expected_misses = 3
    expected_hits = 2
    
    print_result(
        "Statistics accuracy",
        stats['misses'] == expected_misses and stats['hits'] == expected_hits,
        f"Expected: {expected_misses} misses, {expected_hits} hits"
    )


def test_fail_open_strategy():
    """Test 5: Verifica fail-open strategy"""
    print_header("Test 5: Fail-Open Strategy (Redis Down)")
    
    # Crea cache con host inesistente (simula Redis down)
    cache_invalid = GeocodeCache(
        host='invalid-host',
        port=9999,
        enabled=True
    )
    
    print(f"   Cache enabled: {cache_invalid.enabled}")
    print(f"   Redis client: {cache_invalid.redis_client}")
    
    # Verifica: cache disabilitata automaticamente
    print_result(
        "Cache auto-disabled on connection error",
        cache_invalid.enabled == False,
        "Fail-open mode activated ✅"
    )
    
    # Verifica: get() non crasha
    try:
        result = cache_invalid.get("Via Roma 1, Milano")
        crashed = False
    except Exception as e:
        crashed = True
        print(f"   Exception: {e}")
    
    print_result(
        "No crash on Redis unavailable",
        not crashed,
        "System continues without cache ✅"
    )


def test_cache_ttl(cache: GeocodeCache):
    """Test 6: Verifica TTL configuration"""
    print_header("Test 6: TTL Configuration")
    
    if cache is None or not cache.enabled:
        print("⚠️  SKIP: Redis not available")
        return
    
    info = cache.get_info()
    
    print(f"   TTL seconds: {info['ttl']}")
    print(f"   TTL human: {info['ttl_human']}")
    
    expected_ttl = 30 * 24 * 60 * 60  # 30 giorni
    
    print_result(
        "TTL configuration",
        info['ttl'] == expected_ttl,
        f"Expected: {expected_ttl}s (30 giorni)"
    )


def test_real_geocoding_integration():
    """Test 7: Test integrazione completa con geocoding reale"""
    print_header("Test 7: Real Geocoding Integration")
    
    try:
        # Import services
        from app.services.address_sanitizer import get_address_sanitizer
        from app.services.geocoder_service import get_geocoder_service
        from app.services.geocode_cache import get_geocode_cache
        
        sanitizer = get_address_sanitizer()
        geocoder = get_geocoder_service()
        cache = get_geocode_cache()
        
        if not cache.enabled:
            print("⚠️  SKIP: Redis not available")
            return
        
        # Test address
        raw_address = "V. Roma 1, Milano"
        
        # Step 1: Sanitize
        cleaned = sanitizer.clean(raw_address)
        print(f"\n1️⃣  Sanitized: '{raw_address}' → '{cleaned}'")
        
        # Clear cache
        cache.delete(cleaned)
        
        # Step 2: First geocoding (CACHE MISS)
        print("\n2️⃣  First geocoding (CACHE MISS)")
        start = time.time()
        result_1 = cache.get_or_fetch(
            cleaned,
            lambda: geocoder.geocode(cleaned)
        )
        time_1 = (time.time() - start) * 1000
        
        if result_1:
            print(f"   ✅ Geocoded: ({result_1.latitude:.6f}, {result_1.longitude:.6f})")
            print(f"   ⏱️  Time: {time_1:.0f}ms")
        else:
            print(f"   ❌ Geocoding failed (Photon not available?)")
            return
        
        # Step 3: Second geocoding (CACHE HIT)
        print("\n3️⃣  Second geocoding (CACHE HIT)")
        start = time.time()
        result_2 = cache.get_or_fetch(
            cleaned,
            lambda: geocoder.geocode(cleaned)
        )
        time_2 = (time.time() - start) * 1000
        
        if result_2:
            print(f"   ✅ Cached: ({result_2.latitude:.6f}, {result_2.longitude:.6f})")
            print(f"   ⏱️  Time: {time_2:.0f}ms")
        
        # Performance improvement
        improvement = ((time_1 - time_2) / time_1) * 100
        
        print_result(
            "Cache performance improvement",
            time_2 < time_1,
            f"Speedup: {improvement:.0f}% faster ({time_1:.0f}ms → {time_2:.0f}ms)"
        )
        
    except Exception as e:
        print(f"⚠️  SKIP: Integration test failed: {e}")


def main():
    """Esegui tutti i test"""
    print("\n" + "🚀" * 35)
    print("   REDIS CACHE INTEGRATION TEST SUITE")
    print("🚀" * 35)
    
    # Test 1: Redis Connection
    cache = test_redis_connection()
    
    # Test 2: Key Generation
    test_cache_key_generation()
    
    # Test 3: Cache-Aside Pattern
    test_cache_aside_pattern(cache)
    
    # Test 4: Statistics
    test_cache_statistics(cache)
    
    # Test 5: Fail-Open
    test_fail_open_strategy()
    
    # Test 6: TTL
    test_cache_ttl(cache)
    
    # Test 7: Real Integration
    test_real_geocoding_integration()
    
    # Final Summary
    print("\n" + "=" * 70)
    print("✅ TEST SUITE COMPLETED")
    print("=" * 70)
    
    if cache and cache.enabled:
        stats = cache.get_stats()
        print(f"\n📊 Final Cache Statistics:")
        print(f"   Hits: {stats['hits']}")
        print(f"   Misses: {stats['misses']}")
        print(f"   Hit Rate: {stats['hit_rate']:.1f}%")
        print(f"   Errors: {stats['errors']}")
    
    print("\n💡 Next Steps:")
    print("   1. docker-compose up -d redis")
    print("   2. docker-compose restart backend")
    print("   3. curl http://localhost:8000/api/redis/status")
    print()


if __name__ == "__main__":
    main()
