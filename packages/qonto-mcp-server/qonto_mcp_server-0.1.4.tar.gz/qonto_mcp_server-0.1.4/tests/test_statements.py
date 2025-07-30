"""Tests for statement related API methods.

This module tests statement functionality including:
- Listing statements with various filters
- Retrieving individual statements
- Statement structure validation

Statements are periodic summaries of bank account activity.
"""

from typing import Any, Dict, List
from datetime import datetime, timedelta

import pytest

from src.qonto_mcp_server.api.methods import APIMethods


class TestStatements:
    """Test statement API methods."""

    @pytest.mark.asyncio
    async def test_list_statements_basic(self, api_methods: APIMethods) -> None:
        """Test basic statements listing.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_statements()
        
        # Verify successful response
        assert "errors" not in response
        assert "statements" in response
        assert isinstance(response["statements"], list)

    @pytest.mark.asyncio
    async def test_list_statements_with_bank_account_ids(
        self, api_methods: APIMethods, bank_accounts: List[Dict[str, Any]]
    ) -> None:
        """Test statements listing filtered by bank account IDs.
        
        Args:
            api_methods: API methods fixture.
            bank_accounts: Bank accounts fixture.
        """
        if not bank_accounts:
            pytest.skip("No bank accounts available for filtering test")
        
        # Use first bank account ID for filtering
        bank_account_ids = [bank_accounts[0]["id"]]
        
        response = await api_methods.list_statements(
            bank_account_ids=bank_account_ids,
            per_page=10
        )
        
        assert "errors" not in response
        assert "statements" in response
        
        # If statements exist, verify they belong to the specified account
        statements = response["statements"]
        for statement in statements:
            if "bank_account_id" in statement:
                assert statement["bank_account_id"] in bank_account_ids

    @pytest.mark.asyncio
    async def test_list_statements_with_ibans(
        self, api_methods: APIMethods, bank_accounts: List[Dict[str, Any]]
    ) -> None:
        """Test statements listing filtered by IBANs.
        
        Args:
            api_methods: API methods fixture.
            bank_accounts: Bank accounts fixture.
        """
        if not bank_accounts:
            pytest.skip("No bank accounts available for IBAN filtering test")
        
        # Use first bank account IBAN for filtering
        ibans = [bank_accounts[0]["iban"]]
        
        response = await api_methods.list_statements(
            ibans=ibans,
            per_page=10
        )
        
        assert "errors" not in response
        assert "statements" in response

    @pytest.mark.asyncio
    async def test_list_statements_with_period_filters(
        self, api_methods: APIMethods
    ) -> None:
        """Test statements listing with period filters.
        
        Args:
            api_methods: API methods fixture.
        """
        # Test with recent period range
        current_date = datetime.now()
        period_from = f"{current_date.month:02d}-{current_date.year}"
        period_to = period_from  # Same month
        
        response = await api_methods.list_statements(
            period_from=period_from,
            period_to=period_to,
            per_page=10
        )
        
        assert "errors" not in response
        assert "statements" in response

    @pytest.mark.asyncio
    async def test_list_statements_with_sorting(self, api_methods: APIMethods) -> None:
        """Test statements listing with sorting options.
        
        Args:
            api_methods: API methods fixture.
        """
        sort_options = ["period:asc", "period:desc"]
        
        for sort_by in sort_options:
            response = await api_methods.list_statements(
                sort_by=sort_by,
                per_page=5
            )
            
            assert "errors" not in response
            assert "statements" in response

    @pytest.mark.asyncio
    async def test_list_statements_with_pagination(
        self, api_methods: APIMethods
    ) -> None:
        """Test statements listing with pagination.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_statements(
            page=1,
            per_page=5
        )
        
        assert "errors" not in response
        assert "statements" in response
        statements = response["statements"]
        assert isinstance(statements, list)
        assert len(statements) <= 5

    @pytest.mark.asyncio
    async def test_list_statements_default_pagination(
        self, api_methods: APIMethods
    ) -> None:
        """Test statements listing with default pagination values.
        
        Args:
            api_methods: API methods fixture.
        """
        # Should use defaults: page=1, per_page=100
        response = await api_methods.list_statements()
        
        assert "errors" not in response
        assert "statements" in response
        statements = response["statements"]
        assert isinstance(statements, list)
        assert len(statements) <= 100

    @pytest.mark.asyncio
    async def test_retrieve_a_statement(
        self, api_methods: APIMethods, statement_id: str
    ) -> None:
        """Test retrieving a specific statement.
        
        Args:
            api_methods: API methods fixture.
            statement_id: Statement ID fixture.
        """
        response = await api_methods.retrieve_a_statement(statement_id)
        
        # Verify successful response
        assert "errors" not in response
        assert "statement" in response
        
        # Verify statement structure
        statement = response["statement"]
        assert "id" in statement
        assert statement["id"] == statement_id

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_statement(
        self, api_methods: APIMethods
    ) -> None:
        """Test retrieving a non-existent statement.
        
        Args:
            api_methods: API methods fixture.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_methods.retrieve_a_statement(fake_id)
        
        # Should return an error for non-existent statement
        assert "errors" in response

    @pytest.mark.asyncio
    async def test_statements_structure(
        self, statements: List[Dict[str, Any]]
    ) -> None:
        """Test that statements have proper structure.
        
        Args:
            statements: Statements fixture.
        """
        for statement in statements:
            # Required fields
            assert "id" in statement
            assert isinstance(statement["id"], str)
            
            # Common fields validation
            if "period" in statement:
                assert isinstance(statement["period"], str)
                # Period should be in MM-YYYY format
                assert len(statement["period"]) >= 7  # "MM-YYYY" minimum
                assert "-" in statement["period"]
            
            if "bank_account_id" in statement:
                assert isinstance(statement["bank_account_id"], str)
            
            if "iban" in statement:
                assert isinstance(statement["iban"], str)
                assert len(statement["iban"]) >= 15  # Minimum IBAN length
            
            if "opening_balance" in statement:
                assert isinstance(statement["opening_balance"], (str, int, float))
            
            if "closing_balance" in statement:
                assert isinstance(statement["closing_balance"], (str, int, float))
            
            if "currency" in statement:
                assert isinstance(statement["currency"], str)

    @pytest.mark.asyncio
    async def test_statement_detailed_retrieve(
        self, api_methods: APIMethods, statement_id: str
    ) -> None:
        """Test detailed retrieval of statement with all available fields.
        
        Args:
            api_methods: API methods fixture.
            statement_id: Statement ID fixture.
        """
        response = await api_methods.retrieve_a_statement(statement_id)
        
        assert "errors" not in response
        statement = response["statement"]
        
        # Verify detailed fields are present and have correct types
        field_type_mapping = {
            "id": str,
            "period": str,
            "bank_account_id": str,
            "iban": str,
            "opening_balance": (str, int, float),
            "closing_balance": (str, int, float),
            "currency": str,
            "created_at": str,
            "updated_at": str,
        }
        
        for field, expected_type in field_type_mapping.items():
            if field in statement and statement[field] is not None:
                assert isinstance(statement[field], expected_type), \
                    f"Field {field} should be {expected_type}, got {type(statement[field])}"

    @pytest.mark.asyncio
    async def test_statement_period_format(
        self, statements: List[Dict[str, Any]]
    ) -> None:
        """Test that statement periods follow expected format.
        
        Args:
            statements: Statements fixture.
        """
        for statement in statements:
            if "period" in statement:
                period = statement["period"]
                assert isinstance(period, str)
                
                # Period should be in MM-YYYY format
                parts = period.split("-")
                assert len(parts) == 2, f"Period should be MM-YYYY format, got {period}"
                
                month, year = parts
                assert month.isdigit() and len(month) == 2, f"Month should be 2 digits, got {month}"
                assert year.isdigit() and len(year) == 4, f"Year should be 4 digits, got {year}"
                
                month_int = int(month)
                assert 1 <= month_int <= 12, f"Month should be 1-12, got {month_int}"

    @pytest.mark.asyncio
    async def test_statement_balance_consistency(
        self, statements: List[Dict[str, Any]]
    ) -> None:
        """Test that statement balances are consistent.
        
        Args:
            statements: Statements fixture.
        """
        for statement in statements:
            if "opening_balance" in statement and "closing_balance" in statement:
                opening = statement["opening_balance"]
                closing = statement["closing_balance"]
                
                # Both should be numeric
                assert isinstance(opening, (str, int, float))
                assert isinstance(closing, (str, int, float))
                
                # Convert to float for comparison if they're strings
                if isinstance(opening, str):
                    opening = float(opening)
                if isinstance(closing, str):
                    closing = float(closing)
                
                # Both should be valid numbers
                assert not (opening != opening)  # Check for NaN
                assert not (closing != closing)  # Check for NaN

    @pytest.mark.asyncio
    async def test_statements_pagination_limits(
        self, api_methods: APIMethods
    ) -> None:
        """Test statement pagination with boundary values.
        
        Args:
            api_methods: API methods fixture.
        """
        # Test with minimum values
        response = await api_methods.list_statements(page=1, per_page=1)
        assert "errors" not in response
        assert "statements" in response
        statements = response["statements"]
        assert len(statements) <= 1
        
        # Test with maximum reasonable values
        response = await api_methods.list_statements(page=1, per_page=100)
        assert "errors" not in response
        assert "statements" in response
        statements = response["statements"]
        assert len(statements) <= 100

    @pytest.mark.asyncio
    async def test_statements_uniqueness(
        self, statements: List[Dict[str, Any]]
    ) -> None:
        """Test that statements have unique IDs.
        
        Args:
            statements: Statements fixture.
        """
        if len(statements) > 1:
            statement_ids = [statement["id"] for statement in statements]
            unique_ids = set(statement_ids)
            assert len(statement_ids) == len(unique_ids), "Statement IDs should be unique"

    @pytest.mark.asyncio
    async def test_list_statements_mutual_exclusivity(
        self, api_methods: APIMethods, bank_accounts: List[Dict[str, Any]]
    ) -> None:
        """Test that bank_account_ids and ibans are mutually exclusive.
        
        Args:
            api_methods: API methods fixture.
            bank_accounts: Bank accounts fixture.
        """
        if not bank_accounts:
            pytest.skip("No bank accounts available for mutual exclusivity test")
        
        # Using both should work (one or the other should be ignored, or it should error)
        response = await api_methods.list_statements(
            bank_account_ids=[bank_accounts[0]["id"]],
            ibans=[bank_accounts[0]["iban"]],
            per_page=5
        )
        
        # Should either work or return an error (depending on API implementation)
        assert isinstance(response, dict)
        if "errors" in response:
            # If it errors, that's expected behavior for mutual exclusivity
            assert isinstance(response["errors"], list)
        else:
            # If it works, it should return statements
            assert "statements" in response
