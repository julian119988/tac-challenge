#!/bin/bash

# Validation script for Vercel deployment routes
# Usage: ./scripts/validate_vercel_routes.sh <base-url>
# Example: ./scripts/validate_vercel_routes.sh https://tac-challenge.vercel.app

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <base-url>"
  echo "Example: $0 https://tac-challenge.vercel.app"
  exit 1
fi

BASE_URL="$1"
FAILED_TESTS=0
TOTAL_TESTS=0

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Validating Vercel Routes: $BASE_URL"
echo "========================================="
echo ""

# Helper function to test a URL
test_url() {
  local url="$1"
  local expected_status="$2"
  local description="$3"
  local check_header="$4"

  TOTAL_TESTS=$((TOTAL_TESTS + 1))

  echo -n "Testing: $description... "

  # Get HTTP response
  response=$(curl -s -o /dev/null -w "%{http_code}" -L "$url")

  if [ "$response" -eq "$expected_status" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"

    # Check for specific header if requested
    if [ -n "$check_header" ]; then
      header_check=$(curl -s -I -L "$url" | grep -i "$check_header" || echo "")
      if [ -n "$header_check" ]; then
        echo "  └─ Header found: $header_check"
      else
        echo -e "  └─ ${YELLOW}⚠ Warning: Header '$check_header' not found${NC}"
      fi
    fi
  else
    echo -e "${RED}✗ FAIL${NC} (Expected HTTP $expected_status, got HTTP $response)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
  fi
}

# Test health check endpoints
echo "--- Health Check Endpoints ---"
test_url "$BASE_URL/health" 200 "GET /health"
test_url "$BASE_URL/health/ready" 200 "GET /health/ready"
echo ""

# Test root path redirect
echo "--- Root Path Redirect ---"
test_url "$BASE_URL/" 200 "GET / (should redirect to /app)"
echo ""

# Test app entry point
echo "--- App Entry Point ---"
test_url "$BASE_URL/app" 200 "GET /app"
echo ""

# Test static assets
echo "--- Static Assets ---"
test_url "$BASE_URL/styles.css" 200 "GET /styles.css" "cache-control"
test_url "$BASE_URL/config.js" 200 "GET /config.js" "cache-control"
test_url "$BASE_URL/utils.js" 200 "GET /utils.js" "cache-control"
test_url "$BASE_URL/face-detection.js" 200 "GET /face-detection.js" "cache-control"
test_url "$BASE_URL/eye-tracker.js" 200 "GET /eye-tracker.js" "cache-control"
test_url "$BASE_URL/dataset-manager.js" 200 "GET /dataset-manager.js" "cache-control"
test_url "$BASE_URL/model-trainer.js" 200 "GET /model-trainer.js" "cache-control"
test_url "$BASE_URL/gaze-predictor.js" 200 "GET /gaze-predictor.js" "cache-control"
test_url "$BASE_URL/ui-controller.js" 200 "GET /ui-controller.js" "cache-control"
test_url "$BASE_URL/heatmap-viz.js" 200 "GET /heatmap-viz.js" "cache-control"
test_url "$BASE_URL/video-player.js" 200 "GET /video-player.js" "cache-control"
test_url "$BASE_URL/app.js" 200 "GET /app.js" "cache-control"
echo ""

# Test video assets (if they exist)
echo "--- Video Assets ---"
test_url "$BASE_URL/assets/skeleton-attention.mp4" 200 "GET /assets/skeleton-attention.mp4" "cache-control"
echo ""

# Summary
echo "========================================="
echo "Test Results:"
echo "Total: $TOTAL_TESTS tests"
echo -e "Passed: ${GREEN}$((TOTAL_TESTS - FAILED_TESTS))${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
echo "========================================="

if [ $FAILED_TESTS -eq 0 ]; then
  echo -e "${GREEN}All tests passed!${NC}"
  exit 0
else
  echo -e "${RED}Some tests failed.${NC}"
  exit 1
fi
