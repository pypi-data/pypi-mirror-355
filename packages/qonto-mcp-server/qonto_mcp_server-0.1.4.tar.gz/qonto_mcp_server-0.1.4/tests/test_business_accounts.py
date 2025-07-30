"""Tests for business account related API methods.

This module tests business account functionality including:
- Listing business accounts with pagination
- Retrieving individual business accounts
- Account structure validation
- Permission and authorization handling

Business accounts represent the main banking accounts for the organization.
"""

from typing import Any, Dict, List

import pytest

from src.qonto_mcp_server.api.methods import APIMethods


class TestBusinessAccounts:
    """Test business account API methods."""

    @pytest.mark.asyncio
    async def test_list_business_accounts_basic(self, api_methods: APIMethods) -> None:
        """Test basic business accounts listing.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_business_accounts()
        
        # Verify successful response
        assert "errors" not in response
        assert "bank_accounts" in response
        assert isinstance(response["bank_accounts"], list)

    @pytest.mark.asyncio
    async def test_list_business_accounts_with_pagination(
        self, api_methods: APIMethods
    ) -> None:
        """Test business accounts listing with pagination.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_business_accounts(page=1, per_page=5)
        
        assert "errors" not in response
        assert "bank_accounts" in response
        accounts = response["bank_accounts"]
        assert isinstance(accounts, list)
        assert len(accounts) <= 5

    @pytest.mark.asyncio
    async def test_list_business_accounts_default_pagination(
        self, api_methods: APIMethods
    ) -> None:
        """Test business accounts listing with default pagination values.
        
        Args:
            api_methods: API methods fixture.
        """
        # Should use defaults: page=1, per_page=100
        response = await api_methods.list_business_accounts()
        
        assert "errors" not in response
        assert "bank_accounts" in response
        accounts = response["bank_accounts"]
        assert isinstance(accounts, list)
        assert len(accounts) <= 100

    @pytest.mark.asyncio
    async def test_list_business_accounts_pagination_bounds(
        self, api_methods: APIMethods
    ) -> None:
        """Test business accounts listing with pagination boundary values.
        
        Args:
            api_methods: API methods fixture.
        """
        # Test with minimum values
        response = await api_methods.list_business_accounts(page=1, per_page=1)
        assert "errors" not in response
        assert "bank_accounts" in response
        accounts = response["bank_accounts"]
        assert len(accounts) <= 1
        
        # Test with maximum values
        response = await api_methods.list_business_accounts(page=1, per_page=100)
        assert "errors" not in response
        assert "bank_accounts" in response
        accounts = response["bank_accounts"]
        assert len(accounts) <= 100

    @pytest.mark.asyncio
    async def test_get_a_business_account(
        self, api_methods: APIMethods, business_account_id: str
    ) -> None:
        """Test retrieving a specific business account.
        
        Args:
            api_methods: API methods fixture.
            business_account_id: Business account ID fixture.
        """
        response = await api_methods.get_a_business_account(business_account_id)
        
        # Verify successful response
        assert "errors" not in response
        assert "bank_account" in response
        
        # Verify account structure
        account = response["bank_account"]
        assert "id" in account
        assert account["id"] == business_account_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_business_account(
        self, api_methods: APIMethods
    ) -> None:
        """Test retrieving a non-existent business account.
        
        Args:
            api_methods: API methods fixture.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_methods.get_a_business_account(fake_id)
        
        # Should return an error for non-existent account
        assert "errors" in response

    @pytest.mark.asyncio
    async def test_business_accounts_structure(
        self, business_accounts: List[Dict[str, Any]]
    ) -> None:
        """Test that business accounts have proper structure.
        
        Args:
            business_accounts: Business accounts fixture.
        """
        for account in business_accounts:
            # Required fields available to all users
            assert "id" in account
            assert isinstance(account["id"], str)
            
            if "name" in account:
                assert isinstance(account["name"], str)
                assert len(account["name"].strip()) > 0
            
            if "status" in account:
                assert isinstance(account["status"], str)
                # Common status values
                assert account["status"] in ["active", "inactive", "pending", "closed"]
            
            if "main" in account:
                assert isinstance(account["main"], bool)
            
            if "organization_id" in account:
                assert isinstance(account["organization_id"], str)
            
            # Fields available to users with Balance Authorization Read
            if "currency" in account:
                assert isinstance(account["currency"], str)
                assert len(account["currency"]) == 3  # ISO currency code
            
            if "balance" in account:
                assert isinstance(account["balance"], (str, int, float))
            
            if "balance_cents" in account:
                assert isinstance(account["balance_cents"], (int, float))
            
            if "authorized_balance" in account:
                assert isinstance(account["authorized_balance"], (str, int, float))
            
            if "authorized_balance_cents" in account:
                assert isinstance(account["authorized_balance_cents"], (int, float))

    @pytest.mark.asyncio
    async def test_business_account_detailed_retrieve(
        self, api_methods: APIMethods, business_account_id: str
    ) -> None:
        """Test detailed retrieval of business account with all available fields.
        
        Args:
            api_methods: API methods fixture.
            business_account_id: Business account ID fixture.
        """
        response = await api_methods.get_a_business_account(business_account_id)
        
        assert "errors" not in response
        account = response["bank_account"]
        
        # Verify detailed fields are present and have correct types
        field_type_mapping = {
            "id": str,
            "name": str,
            "status": str,
            "main": bool,
            "organization_id": str,
            "currency": str,
            "balance": (str, int, float),
            "balance_cents": (int, float),
            "authorized_balance": (str, int, float),
            "authorized_balance_cents": (int, float),
            "iban": str,
            "bic": str,
            "created_at": str,
            "updated_at": str,
        }
        
        for field, expected_type in field_type_mapping.items():
            if field in account and account[field] is not None:
                assert isinstance(account[field], expected_type), \
                    f"Field {field} should be {expected_type}, got {type(account[field])}"

    @pytest.mark.asyncio
    async def test_business_account_balance_consistency(
        self, business_accounts: List[Dict[str, Any]]
    ) -> None:
        """Test that business account balances are consistent.
        
        Args:
            business_accounts: Business accounts fixture.
        """
        for account in business_accounts:
            # If both balance and balance_cents are present, they should be consistent
            if "balance" in account and "balance_cents" in account:
                balance = account["balance"]
                balance_cents = account["balance_cents"]
                
                # Convert balance to float if it's a string
                if isinstance(balance, str):
                    balance_float = float(balance)
                else:
                    balance_float = float(balance)
                
                # Balance in cents should be balance * 100 (allowing for small floating point differences)
                expected_cents = balance_float * 100
                assert abs(balance_cents - expected_cents) < 0.01, \
                    f"Balance mismatch: {balance} EUR should equal {balance_cents} cents"
            
            # Same check for authorized balance
            if "authorized_balance" in account and "authorized_balance_cents" in account:
                auth_balance = account["authorized_balance"]
                auth_balance_cents = account["authorized_balance_cents"]
                
                if isinstance(auth_balance, str):
                    auth_balance_float = float(auth_balance)
                else:
                    auth_balance_float = float(auth_balance)
                
                expected_auth_cents = auth_balance_float * 100
                assert abs(auth_balance_cents - expected_auth_cents) < 0.01, \
                    f"Authorized balance mismatch: {auth_balance} EUR should equal {auth_balance_cents} cents"

    @pytest.mark.asyncio
    async def test_business_accounts_uniqueness(
        self, business_accounts: List[Dict[str, Any]]
    ) -> None:
        """Test that business accounts have unique IDs.
        
        Args:
            business_accounts: Business accounts fixture.
        """
        if len(business_accounts) > 1:
            account_ids = [account["id"] for account in business_accounts]
            unique_ids = set(account_ids)
            assert len(account_ids) == len(unique_ids), "Business account IDs should be unique"

    @pytest.mark.asyncio
    async def test_business_account_status_validation(
        self, business_accounts: List[Dict[str, Any]]
    ) -> None:
        """Test that business account statuses are valid.
        
        Args:
            business_accounts: Business accounts fixture.
        """
        valid_statuses = {"active", "inactive", "pending", "closed", "suspended"}
        
        for account in business_accounts:
            if "status" in account:
                status = account["status"]
                assert isinstance(status, str)
                assert status in valid_statuses, \
                    f"Invalid status '{status}', should be one of {valid_statuses}"

    @pytest.mark.asyncio
    async def test_business_account_main_flag(
        self, business_accounts: List[Dict[str, Any]]
    ) -> None:
        """Test that main account flag is properly set.
        
        Args:
            business_accounts: Business accounts fixture.
        """
        main_accounts = [acc for acc in business_accounts if acc.get("main") is True]
        
        # There should be at most one main account
        assert len(main_accounts) <= 1, "There should be at most one main business account"
        
        for account in business_accounts:
            if "main" in account:
                assert isinstance(account["main"], bool)

    @pytest.mark.asyncio
    async def test_business_account_organization_consistency(
        self, business_accounts: List[Dict[str, Any]], organization_data: Dict[str, Any]
    ) -> None:
        """Test that business accounts belong to the authenticated organization.
        
        Args:
            business_accounts: Business accounts fixture.
            organization_data: Organization data fixture.
        """
        organization_id = organization_data["organization"]["id"]
        
        for account in business_accounts:
            if "organization_id" in account:
                assert account["organization_id"] == organization_id, \
                    "Business account should belong to the authenticated organization"

    @pytest.mark.asyncio
    async def test_business_account_iban_format(
        self, business_accounts: List[Dict[str, Any]]
    ) -> None:
        """Test that business account IBANs follow proper format.
        
        Args:
            business_accounts: Business accounts fixture.
        """
        for account in business_accounts:
            if "iban" in account and account["iban"]:
                iban = account["iban"]
                assert isinstance(iban, str)
                assert len(iban) >= 15, f"IBAN should be at least 15 characters, got {len(iban)}"
                assert len(iban) <= 34, f"IBAN should be at most 34 characters, got {len(iban)}"
                # First two characters should be country code (letters)
                assert iban[:2].isalpha(), f"IBAN should start with country code, got {iban[:2]}"

    @pytest.mark.asyncio
    async def test_business_account_currency_validation(
        self, business_accounts: List[Dict[str, Any]]
    ) -> None:
        """Test that business account currencies are valid ISO codes.
        
        Args:
            business_accounts: Business accounts fixture.
        """
        valid_currencies = {"EUR", "USD", "GBP", "CHF"}  # Common currencies, extend as needed
        
        for account in business_accounts:
            if "currency" in account:
                currency = account["currency"]
                assert isinstance(currency, str)
                assert len(currency) == 3, f"Currency should be 3-letter ISO code, got {currency}"
                assert currency.isupper(), f"Currency should be uppercase, got {currency}"
                # Note: We don't strictly enforce the valid_currencies set as Qonto may support more
