#!/bin/bash
# Smoke test script for Doctor+ Backend
# Tests all critical endpoints

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${1:-http://localhost:8000}"
API_KEY="${DOCTORPLUS_API_KEY:-test_key_123}"

echo "======================================"
echo "Doctor+ Backend Smoke Test"
echo "======================================"
echo "Base URL: $BASE_URL"
echo "API Key: ${API_KEY:0:8}..."
echo ""

# Helper functions
test_endpoint() {
    local method=$1
    local path=$2
    local expected_status=$3
    local name=$4
    local extra_args=$5
    
    echo -n "Testing $name... "
    
    response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$path" $extra_args)
    body=$(echo "$response" | head -n -1)
    status=$(echo "$response" | tail -n 1)
    
    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $status)"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (expected $expected_status, got $status)"
        echo "Response: $body"
        return 1
    fi
}

# Track results
PASSED=0
FAILED=0

# Test 1: Root endpoint
if test_endpoint "GET" "/" "200" "Root /"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test 2: Legacy health
if test_endpoint "GET" "/health" "200" "Legacy /health"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test 3: Legacy version
if test_endpoint "GET" "/version" "200" "Legacy /version"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test 4: V1 root
if test_endpoint "GET" "/v1" "200" "V1 root /v1"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test 5: V1 health
if test_endpoint "GET" "/v1/health" "200" "V1 /v1/health"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test 6: V1 version
if test_endpoint "GET" "/v1/version" "200" "V1 /v1/version"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test 7: V1 /doctorplus without auth (should be 401)
if test_endpoint "POST" "/v1/doctorplus" "401" "V1 /doctorplus (no auth)" \
    '-H "Content-Type: application/json" -d "{\"mode\":\"symptoms\",\"text\":\"test\"}"'; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test 8: V1 /doctorplus with X-API-Key
echo -n "Testing V1 /doctorplus (with X-API-Key)... "
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/v1/doctorplus" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"mode":"symptoms","text":"У меня болит голова"}')
body=$(echo "$response" | head -n -1)
status=$(echo "$response" | tail -n 1)

if [ "$status" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $status - AI configured)"
    ((PASSED++))
elif [ "$status" = "500" ] && echo "$body" | grep -q "AI_NOT_CONFIGURED"; then
    echo -e "${YELLOW}⚠ WARN${NC} (HTTP $status - GROQ_API_KEY not set, expected)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} (unexpected status $status)"
    echo "Response: $body"
    ((FAILED++))
fi

# Test 9: V1 /doctorplus with Bearer token
echo -n "Testing V1 /doctorplus (with Bearer)... "
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/v1/doctorplus" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d '{"mode":"analyses","text":"Анализ крови"}')
body=$(echo "$response" | head -n -1)
status=$(echo "$response" | tail -n 1)

if [ "$status" = "200" ] || ([ "$status" = "500" ] && echo "$body" | grep -q "AI_NOT_CONFIGURED"); then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $status)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} (unexpected status $status)"
    echo "Response: $body"
    ((FAILED++))
fi

# Summary
echo ""
echo "======================================"
echo "Test Summary"
echo "======================================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. ✗${NC}"
    exit 1
fi
