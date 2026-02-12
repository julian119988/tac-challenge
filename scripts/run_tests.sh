#!/usr/bin/env bash
# Test runner script for TAC Challenge project
# Runs Python and/or JavaScript tests with optional coverage reporting

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default options
RUN_PYTHON=true
RUN_FRONTEND=true
WITH_COVERAGE=false
VERBOSE=false

# Usage function
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run tests for the TAC Challenge project (Python backend and/or JavaScript frontend).

Options:
    -p, --python-only       Run only Python tests
    -f, --frontend-only     Run only frontend (JavaScript) tests
    -c, --coverage          Generate coverage reports
    -v, --verbose           Verbose output
    -h, --help              Show this help message

Examples:
    $(basename "$0")                  # Run all tests
    $(basename "$0") --python-only    # Run only Python tests
    $(basename "$0") --coverage       # Run all tests with coverage
    $(basename "$0") -p -c            # Run Python tests with coverage

EOF
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--python-only)
            RUN_PYTHON=true
            RUN_FRONTEND=false
            shift
            ;;
        -f|--frontend-only)
            RUN_PYTHON=false
            RUN_FRONTEND=true
            shift
            ;;
        -c|--coverage)
            WITH_COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            usage
            ;;
    esac
done

# Print header
echo -e "${BLUE}╔═══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     TAC Challenge Test Runner            ║${NC}"
echo -e "${BLUE}╔═══════════════════════════════════════════╗${NC}"
echo ""

# Track test results
PYTHON_RESULT=0
FRONTEND_RESULT=0

# Run Python tests
if [ "$RUN_PYTHON" = true ]; then
    echo -e "${YELLOW}Running Python tests...${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    cd "$PROJECT_ROOT"

    if [ "$WITH_COVERAGE" = true ]; then
        if [ "$VERBOSE" = true ]; then
            uv run pytest tests/ -v --cov=adws --cov=apps --cov-report=term-missing --cov-report=html || PYTHON_RESULT=$?
        else
            uv run pytest tests/ --cov=adws --cov=apps --cov-report=term --cov-report=html || PYTHON_RESULT=$?
        fi

        if [ $PYTHON_RESULT -eq 0 ]; then
            echo ""
            echo -e "${GREEN}Python coverage report generated: htmlcov/index.html${NC}"
        fi
    else
        if [ "$VERBOSE" = true ]; then
            uv run pytest tests/ -v || PYTHON_RESULT=$?
        else
            uv run pytest tests/ || PYTHON_RESULT=$?
        fi
    fi

    echo ""

    if [ $PYTHON_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ Python tests passed${NC}"
    else
        echo -e "${RED}✗ Python tests failed${NC}"
    fi

    echo ""
fi

# Run frontend tests
if [ "$RUN_FRONTEND" = true ]; then
    echo -e "${YELLOW}Running frontend tests...${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    cd "$PROJECT_ROOT/apps/frontend"

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        npm install
    fi

    if [ "$WITH_COVERAGE" = true ]; then
        npm run test:coverage || FRONTEND_RESULT=$?

        if [ $FRONTEND_RESULT -eq 0 ]; then
            echo ""
            echo -e "${GREEN}Frontend coverage report generated: apps/frontend/coverage/lcov-report/index.html${NC}"
        fi
    else
        npm test -- --passWithNoTests || FRONTEND_RESULT=$?
    fi

    echo ""

    if [ $FRONTEND_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ Frontend tests passed${NC}"
    else
        echo -e "${RED}✗ Frontend tests failed${NC}"
    fi

    echo ""
fi

# Print summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ "$RUN_PYTHON" = true ]; then
    if [ $PYTHON_RESULT -eq 0 ]; then
        echo -e "  Python:   ${GREEN}✓ PASSED${NC}"
    else
        echo -e "  Python:   ${RED}✗ FAILED${NC}"
    fi
fi

if [ "$RUN_FRONTEND" = true ]; then
    if [ $FRONTEND_RESULT -eq 0 ]; then
        echo -e "  Frontend: ${GREEN}✓ PASSED${NC}"
    else
        echo -e "  Frontend: ${RED}✗ FAILED${NC}"
    fi
fi

echo ""

# Exit with error if any tests failed
if [ $PYTHON_RESULT -ne 0 ] || [ $FRONTEND_RESULT -ne 0 ]; then
    echo -e "${RED}Some tests failed. See output above for details.${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
