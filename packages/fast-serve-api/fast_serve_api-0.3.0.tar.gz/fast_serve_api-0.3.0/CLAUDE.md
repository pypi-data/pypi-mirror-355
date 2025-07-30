# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

fast-serve-api is a Python library that automatically transforms static methods of service classes into FastAPI endpoints. It simplifies REST API creation by handling endpoint generation, request/response models, and error handling.

## Common Development Commands

### Package Management
- Install dependencies: `uv sync`
- Install with test dependencies: `uv sync --extra test`
- Add dependency: `uv add <package>`
- Build package: `hatchling build`

### Running the Example
- Run test server: `uvicorn test:app --reload`

### Testing
- Run all tests: `uv run pytest`
- Run with coverage: `uv run pytest --cov=src/fast_serve_api --cov-report=term-missing`
- Run with HTML coverage report: `uv run pytest --cov=src/fast_serve_api --cov-report=html`
- Run specific test: `uv run pytest tests/test_fast_serve_api.py::TestFastServeApi::test_simple_string_endpoint`
- Run tests with verbose output: `uv run pytest -v`
- Run tests with print output: `uv run pytest -v -s`

## High-Level Architecture

The core architecture revolves around the `FastServeApi` base class that services inherit from:

1. **Automatic Endpoint Generation**: When a service class inherits from `FastServeApi`, all static methods are automatically registered as POST endpoints at `/{class_name_snake_case}/{method_name}`

2. **Dynamic Model Creation**: The system dynamically creates Pydantic request models from method signatures, supporting:
   - Basic types (str, int, float, bool)
   - Complex types (List, Dict, Tuple)
   - Optional parameters with defaults
   - Single-field requests that accept both raw values and object notation

3. **Standardized Response Models**:
   - All responses inherit from `FastServeApiModel` with `success`, `message`, and optional `status_code`
   - List responses use `FastServeApiListModel` with pagination fields
   - Errors return `FastServeApiErrorModel` with stack traces

4. **Error Handling**: All exceptions are caught and returned as standardized error responses with full stack traces for debugging.

## Key Implementation Details

- The `FastServeApi` class uses `__init_subclass__` to automatically register endpoints when subclassed
- Request models are created dynamically using `pydantic.create_model()`
- Single-field requests are handled specially to allow both `{"field": value}` and raw value formats
- CamelCase class names are converted to snake_case for endpoint paths
- All endpoints are POST methods to ensure consistent parameter handling

## Testing Approach

The project uses pytest with httpx for testing FastAPI endpoints. Tests are located in the `tests/` directory with the following structure:
- `conftest.py`: Shared test fixtures
- `test_fast_serve_api.py`: Comprehensive tests for the FastServeApi class

Tests cover:
- Endpoint registration and naming conventions
- Various parameter types (simple, complex, optional)
- Different return types (strings, numbers, lists, dicts, tuples)
- Error handling and validation
- Single-field request handling

When adding new features, write corresponding tests to ensure proper functionality and edge case handling.