"""Tests for organization and bank account related API methods.

This module tests the core organizational functionality including:
- Organization data retrieval
- Bank account listing and management
- Membership operations

These are foundational operations that other tests depend on.
"""

from typing import Any, Dict, List

import pytest

from src.qonto_mcp_server.api.methods import APIMethods


class TestOrganization:
    """Test organization-related API methods."""

    @pytest.mark.asyncio
    async def test_retrieve_the_authenticated_organization_and_list_bank_accounts(
        self, api_methods: APIMethods
    ) -> None:
        """Test retrieving organization data and bank accounts.
        
        This is a fundamental operation that should always succeed for
        authenticated users.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.retrieve_the_authenticated_organization_and_list_bank_accounts()
        
        # Verify successful response
        assert "errors" not in response
        assert "organization" in response
        
        # Verify organization structure
        organization = response["organization"]
        assert "id" in organization
        assert "bank_accounts" in organization
        assert isinstance(organization["bank_accounts"], list)
        
        # Verify bank account structure if any exist
        if organization["bank_accounts"]:
            bank_account = organization["bank_accounts"][0]
            assert "id" in bank_account
            assert "iban" in bank_account
            assert "status" in bank_account

    @pytest.mark.asyncio
    async def test_retrieve_organization_with_external_accounts(
        self, api_methods: APIMethods
    ) -> None:
        """Test retrieving organization data including external accounts.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.retrieve_the_authenticated_organization_and_list_bank_accounts(
            include_external_accounts=True
        )
        
        # Verify successful response
        assert "errors" not in response
        assert "organization" in response
        
        organization = response["organization"]
        assert "bank_accounts" in organization
        assert isinstance(organization["bank_accounts"], list)

    @pytest.mark.asyncio
    async def test_organization_bank_accounts_have_required_fields(
        self, bank_accounts: List[Dict[str, Any]]
    ) -> None:
        """Test that bank accounts have all required fields.
        
        Args:
            bank_accounts: Bank accounts fixture.
        """
        assert len(bank_accounts) > 0, "Should have at least one bank account"
        
        for account in bank_accounts:
            # Required fields that should always be present
            assert "id" in account
            assert "iban" in account
            assert "status" in account
            assert "currency" in account
            
            # Verify field types
            assert isinstance(account["id"], str)
            assert isinstance(account["iban"], str)
            assert isinstance(account["status"], str)
            assert isinstance(account["currency"], str)
            
            # Verify IBAN format (basic check)
            assert len(account["iban"]) >= 15  # Minimum IBAN length
            assert account["iban"].isalnum() or " " in account["iban"]

    @pytest.mark.asyncio
    async def test_active_bank_account_properties(
        self, active_bank_account: Dict[str, Any]
    ) -> None:
        """Test that active bank account has expected properties.
        
        Args:
            active_bank_account: Active bank account fixture.
        """
        assert active_bank_account["status"] == "active"
        assert "balance_cents" in active_bank_account
        assert "authorized_balance_cents" in active_bank_account
        
        # Balance should be numeric
        assert isinstance(active_bank_account["balance_cents"], (int, float))
        assert isinstance(active_bank_account["authorized_balance_cents"], (int, float))


class TestMemberships:
    """Test membership-related API methods."""

    @pytest.mark.asyncio
    async def test_list_memberships(self, api_methods: APIMethods) -> None:
        """Test listing organization memberships.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_memberships()
        
        # Verify successful response
        assert "errors" not in response
        assert "memberships" in response
        assert isinstance(response["memberships"], list)
        
        # If memberships exist, verify structure
        if response["memberships"]:
            membership = response["memberships"][0]
            assert "id" in membership
            assert "user_id" in membership

    @pytest.mark.asyncio
    async def test_list_memberships_with_pagination(self, api_methods: APIMethods) -> None:
        """Test listing memberships with pagination parameters.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_memberships(page="1", per_page="5")
        
        # Verify successful response
        assert "errors" not in response
        assert "memberships" in response
        assert isinstance(response["memberships"], list)
        
        # Verify pagination metadata if present
        if "meta" in response:
            meta = response["meta"]
            if "total_pages" in meta:
                assert isinstance(meta["total_pages"], int)
            if "current_page" in meta:
                assert isinstance(meta["current_page"], int)

    @pytest.mark.asyncio
    async def test_memberships_structure(self, api_methods: APIMethods) -> None:
        """Test that memberships have proper structure when present.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_memberships(per_page="10")
        
        assert "errors" not in response
        memberships = response.get("memberships", [])
        
        for membership in memberships:
            # Required fields
            assert "id" in membership
            assert isinstance(membership["id"], str)
            
            # Common optional fields
            if "user_id" in membership:
                assert isinstance(membership["user_id"], str)
            if "role" in membership:
                assert isinstance(membership["role"], str)
            if "status" in membership:
                assert isinstance(membership["status"], str)
