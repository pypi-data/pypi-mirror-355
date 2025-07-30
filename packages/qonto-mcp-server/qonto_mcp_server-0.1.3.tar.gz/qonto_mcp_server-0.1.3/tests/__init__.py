"""Test package for Qonto MCP server.

This package contains comprehensive integration tests for all Qonto API methods
exposed through the MCP server. The tests are organized by functional areas
and use real API calls to ensure compatibility and correctness.

Test Organization:
    - conftest.py: Shared fixtures and test configuration
    - test_*.py: Individual test modules for each functional area
    - Real API integration without mocking for maximum reliability
    - Comprehensive error handling and edge case coverage
    - Type-safe test implementations with full annotations

Usage:
    Run all tests: pytest
    Run specific module: pytest tests/test_transactions.py
    Run with coverage: pytest --cov=src/qonto_mcp_server
"""
