"""Tests for beneficiary related API methods.

This module tests beneficiary functionality including:
- Listing beneficiaries with various filters
- Retrieving individual beneficiaries
- Managing trusted beneficiaries
- SEPA-specific beneficiary operations

Beneficiaries are entities that can receive external transfers.
"""

from typing import Any, Dict, List
from datetime import datetime, timedelta

import pytest

from src.qonto_mcp_server.api.methods import APIMethods


class TestBeneficiaries:
    """Test beneficiary API methods (legacy endpoints)."""

    @pytest.mark.asyncio
    async def test_list_beneficiaries_basic(self, api_methods: APIMethods) -> None:
        """Test basic beneficiaries listing.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_beneficiaries()
        
        # Verify successful response
        assert "errors" not in response
        assert "beneficiaries" in response
        assert isinstance(response["beneficiaries"], list)

    @pytest.mark.asyncio
    async def test_list_beneficiaries_with_pagination(
        self, api_methods: APIMethods
    ) -> None:
        """Test beneficiaries listing with pagination.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_beneficiaries(
            page="1",
            per_page="5"
        )
        
        assert "errors" not in response
        assert "beneficiaries" in response
        beneficiaries_list = response["beneficiaries"]
        assert isinstance(beneficiaries_list, list)
        assert len(beneficiaries_list) <= 5

    @pytest.mark.asyncio
    async def test_list_beneficiaries_trusted_filter(
        self, api_methods: APIMethods
    ) -> None:
        """Test beneficiaries listing with trusted filter.
        
        Args:
            api_methods: API methods fixture.
        """
        # Test trusted beneficiaries
        response = await api_methods.list_beneficiaries(
            trusted=True,
            per_page="10"
        )
        
        assert "errors" not in response
        assert "beneficiaries" in response
        
        # Verify trusted status if present
        for beneficiary in response["beneficiaries"]:
            if "trusted" in beneficiary:
                assert beneficiary["trusted"] is True

        # Test non-trusted beneficiaries
        response = await api_methods.list_beneficiaries(
            trusted=False,
            per_page="10"
        )
        
        assert "errors" not in response
        assert "beneficiaries" in response
        
        # Verify non-trusted status if present
        for beneficiary in response["beneficiaries"]:
            if "trusted" in beneficiary:
                assert beneficiary["trusted"] is False

    @pytest.mark.asyncio
    async def test_list_beneficiaries_status_filter(
        self, api_methods: APIMethods
    ) -> None:
        """Test beneficiaries listing with status filter.
        
        Args:
            api_methods: API methods fixture.
        """
        status_options = ["pending", "validated", "declined"]
        
        for status in status_options:
            response = await api_methods.list_beneficiaries(
                status=[status],
                per_page="10"
            )
            
            assert "errors" not in response
            assert "beneficiaries" in response
            
            # Verify status if transfers exist
            for beneficiary in response["beneficiaries"]:
                if "status" in beneficiary:
                    assert beneficiary["status"] == status

    @pytest.mark.asyncio
    async def test_list_beneficiaries_iban_filter(
        self, api_methods: APIMethods, beneficiaries: List[Dict[str, Any]]
    ) -> None:
        """Test beneficiaries listing with IBAN filter.
        
        Args:
            api_methods: API methods fixture.
            beneficiaries: Beneficiaries fixture.
        """
        if not beneficiaries:
            pytest.skip("No beneficiaries available for IBAN filtering test")
        
        # Find a beneficiary with an IBAN
        test_iban = None
        for beneficiary in beneficiaries:
            if "iban" in beneficiary and beneficiary["iban"]:
                test_iban = beneficiary["iban"]
                break
        
        if not test_iban:
            pytest.skip("No beneficiaries with IBAN available for filtering test")
        
        response = await api_methods.list_beneficiaries(
            iban=[test_iban],
            per_page="10"
        )
        
        assert "errors" not in response
        assert "beneficiaries" in response
        
        # Verify IBAN matches
        for beneficiary in response["beneficiaries"]:
            if "iban" in beneficiary:
                assert beneficiary["iban"] == test_iban

    @pytest.mark.asyncio
    async def test_list_beneficiaries_date_filters(
        self, api_methods: APIMethods
    ) -> None:
        """Test beneficiaries listing with date filters.
        
        Args:
            api_methods: API methods fixture.
        """
        # Test with date range from last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        response = await api_methods.list_beneficiaries(
            updated_at_from=start_date.isoformat(),
            updated_at_to=end_date.isoformat(),
            per_page="10"
        )
        
        assert "errors" not in response
        assert "beneficiaries" in response

    @pytest.mark.asyncio
    async def test_list_beneficiaries_sorting(self, api_methods: APIMethods) -> None:
        """Test beneficiaries listing with sorting.
        
        Args:
            api_methods: API methods fixture.
        """
        sort_options = ["updated_at:asc", "updated_at:desc"]
        
        for sort_by in sort_options:
            response = await api_methods.list_beneficiaries(
                sort_by=sort_by,
                per_page="5"
            )
            
            assert "errors" not in response
            assert "beneficiaries" in response

    @pytest.mark.asyncio
    async def test_retrieve_a_beneficiary(
        self, api_methods: APIMethods, beneficiary_id: str
    ) -> None:
        """Test retrieving a specific beneficiary.
        
        Args:
            api_methods: API methods fixture.
            beneficiary_id: Beneficiary ID fixture.
        """
        response = await api_methods.retrieve_a_beneficiary(beneficiary_id)
        
        # Verify successful response
        assert "errors" not in response
        assert "beneficiary" in response
        
        # Verify beneficiary structure
        beneficiary = response["beneficiary"]
        assert "id" in beneficiary
        assert beneficiary["id"] == beneficiary_id

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_beneficiary(
        self, api_methods: APIMethods
    ) -> None:
        """Test retrieving a non-existent beneficiary.
        
        Args:
            api_methods: API methods fixture.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_methods.retrieve_a_beneficiary(fake_id)
        
        # Should return an error for non-existent beneficiary
        assert "errors" in response

    @pytest.mark.asyncio
    async def test_untrust_a_list_of_beneficiaries(
        self, api_methods: APIMethods, trusted_beneficiary_ids: List[str]
    ) -> None:
        """Test untrusting a list of beneficiaries.
        
        Args:
            api_methods: API methods fixture.
            trusted_beneficiary_ids: Trusted beneficiary IDs fixture.
        """
        if not trusted_beneficiary_ids:
            pytest.skip("No trusted beneficiaries available for untrusting test")
        
        # Test with a subset of trusted beneficiaries
        test_ids = trusted_beneficiary_ids[:2]  # Limit to 2 for testing
        
        response = await api_methods.untrust_a_list_of_beneficiaries(test_ids)
        
        # Verify response structure
        assert "errors" not in response or len(response.get("errors", [])) == 0
        
        # Note: In a real test environment, we might want to re-trust these
        # beneficiaries afterwards, but that functionality might not be available

    @pytest.mark.asyncio
    async def test_beneficiaries_structure(
        self, beneficiaries: List[Dict[str, Any]]
    ) -> None:
        """Test that beneficiaries have proper structure.
        
        Args:
            beneficiaries: Beneficiaries fixture.
        """
        for beneficiary in beneficiaries:
            # Required fields
            assert "id" in beneficiary
            assert isinstance(beneficiary["id"], str)
            
            # Common optional fields with type validation
            if "name" in beneficiary:
                assert isinstance(beneficiary["name"], str)
            
            if "iban" in beneficiary:
                assert isinstance(beneficiary["iban"], str)
                # Basic IBAN format check
                if beneficiary["iban"]:
                    assert len(beneficiary["iban"]) >= 15
            
            if "trusted" in beneficiary:
                assert isinstance(beneficiary["trusted"], bool)
            
            if "status" in beneficiary:
                assert isinstance(beneficiary["status"], str)
                assert beneficiary["status"] in ["pending", "validated", "declined"]


class TestSEPABeneficiaries:
    """Test SEPA beneficiary API methods (current endpoints)."""

    @pytest.mark.asyncio
    async def test_list_sepa_beneficiaries_basic(self, api_methods: APIMethods) -> None:
        """Test basic SEPA beneficiaries listing.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_sepa_beneficiaries()
        
        # Verify successful response
        assert "errors" not in response
        assert "beneficiaries" in response
        assert isinstance(response["beneficiaries"], list)

    @pytest.mark.asyncio
    async def test_list_sepa_beneficiaries_with_pagination(
        self, api_methods: APIMethods
    ) -> None:
        """Test SEPA beneficiaries listing with pagination.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_sepa_beneficiaries(
            page=1,
            per_page=5
        )
        
        assert "errors" not in response
        assert "beneficiaries" in response
        beneficiaries_list = response["beneficiaries"]
        assert isinstance(beneficiaries_list, list)
        assert len(beneficiaries_list) <= 5

    @pytest.mark.asyncio
    async def test_list_sepa_beneficiaries_iban_filter(
        self, api_methods: APIMethods, sepa_beneficiaries: List[Dict[str, Any]]
    ) -> None:
        """Test SEPA beneficiaries listing with IBAN filter.
        
        Args:
            api_methods: API methods fixture.
            sepa_beneficiaries: SEPA beneficiaries fixture.
        """
        if not sepa_beneficiaries:
            pytest.skip("No SEPA beneficiaries available for IBAN filtering test")
        
        # Find a beneficiary with an IBAN
        test_iban = None
        for beneficiary in sepa_beneficiaries:
            if "iban" in beneficiary and beneficiary["iban"]:
                test_iban = beneficiary["iban"]
                break
        
        if not test_iban:
            pytest.skip("No SEPA beneficiaries with IBAN available for filtering test")
        
        response = await api_methods.list_sepa_beneficiaries(
            iban=[test_iban],
            per_page=10
        )
        
        assert "errors" not in response
        assert "beneficiaries" in response
        
        # Verify IBAN matches
        for beneficiary in response["beneficiaries"]:
            if "iban" in beneficiary:
                assert beneficiary["iban"] == test_iban

    @pytest.mark.asyncio
    async def test_list_sepa_beneficiaries_status_filter(
        self, api_methods: APIMethods
    ) -> None:
        """Test SEPA beneficiaries listing with status filter.
        
        Args:
            api_methods: API methods fixture.
        """
        status_options = ["pending", "validated", "declined"]
        
        for status in status_options:
            response = await api_methods.list_sepa_beneficiaries(
                status=[status],
                per_page=10
            )
            
            assert "errors" not in response
            assert "beneficiaries" in response
            
            # Verify status if beneficiaries exist
            for beneficiary in response["beneficiaries"]:
                if "status" in beneficiary:
                    assert beneficiary["status"] == status

    @pytest.mark.asyncio
    async def test_list_sepa_beneficiaries_trusted_filter(
        self, api_methods: APIMethods
    ) -> None:
        """Test SEPA beneficiaries listing with trusted filter.
        
        Args:
            api_methods: API methods fixture.
        """
        # Test trusted beneficiaries
        response = await api_methods.list_sepa_beneficiaries(
            trusted=True,
            per_page=10
        )
        
        assert "errors" not in response
        assert "beneficiaries" in response
        
        # Verify trusted status if present
        for beneficiary in response["beneficiaries"]:
            if "trusted" in beneficiary:
                assert beneficiary["trusted"] is True

    @pytest.mark.asyncio
    async def test_list_sepa_beneficiaries_sorting(
        self, api_methods: APIMethods
    ) -> None:
        """Test SEPA beneficiaries listing with sorting.
        
        Args:
            api_methods: API methods fixture.
        """
        sort_options = ["updated_at:asc", "updated_at:desc"]
        
        for sort_by in sort_options:
            response = await api_methods.list_sepa_beneficiaries(
                sort_by=sort_by,
                per_page=5
            )
            
            assert "errors" not in response
            assert "beneficiaries" in response

    @pytest.mark.asyncio
    async def test_retrieve_a_sepa_beneficiary(
        self, api_methods: APIMethods, sepa_beneficiary_id: str
    ) -> None:
        """Test retrieving a specific SEPA beneficiary.
        
        Args:
            api_methods: API methods fixture.
            sepa_beneficiary_id: SEPA beneficiary ID fixture.
        """
        response = await api_methods.retrieve_a_sepa_beneficiary(sepa_beneficiary_id)
        
        # Verify successful response
        assert "errors" not in response
        assert "beneficiary" in response
        
        # Verify beneficiary structure
        beneficiary = response["beneficiary"]
        assert "id" in beneficiary
        assert beneficiary["id"] == sepa_beneficiary_id

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_sepa_beneficiary(
        self, api_methods: APIMethods
    ) -> None:
        """Test retrieving a non-existent SEPA beneficiary.
        
        Args:
            api_methods: API methods fixture.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_methods.retrieve_a_sepa_beneficiary(fake_id)
        
        # Should return an error for non-existent beneficiary
        assert "errors" in response

    @pytest.mark.asyncio
    async def test_sepa_beneficiaries_structure(
        self, sepa_beneficiaries: List[Dict[str, Any]]
    ) -> None:
        """Test that SEPA beneficiaries have proper structure.
        
        Args:
            sepa_beneficiaries: SEPA beneficiaries fixture.
        """
        for beneficiary in sepa_beneficiaries:
            # Required fields
            assert "id" in beneficiary
            assert isinstance(beneficiary["id"], str)
            
            # Common optional fields with type validation
            if "name" in beneficiary:
                assert isinstance(beneficiary["name"], str)
            
            if "iban" in beneficiary:
                assert isinstance(beneficiary["iban"], str)
                # Basic IBAN format check for SEPA
                if beneficiary["iban"]:
                    assert len(beneficiary["iban"]) >= 15
                    # SEPA IBANs should start with EU country codes
                    assert beneficiary["iban"][:2].isalpha()
            
            if "trusted" in beneficiary:
                assert isinstance(beneficiary["trusted"], bool)
            
            if "status" in beneficiary:
                assert isinstance(beneficiary["status"], str)
                assert beneficiary["status"] in ["pending", "validated", "declined"]

    @pytest.mark.asyncio
    async def test_sepa_beneficiary_detailed_retrieve(
        self, api_methods: APIMethods, sepa_beneficiary_id: str
    ) -> None:
        """Test detailed retrieval of SEPA beneficiary with all fields.
        
        Args:
            api_methods: API methods fixture.
            sepa_beneficiary_id: SEPA beneficiary ID fixture.
        """
        response = await api_methods.retrieve_a_sepa_beneficiary(sepa_beneficiary_id)
        
        assert "errors" not in response
        beneficiary = response["beneficiary"]
        
        # Verify detailed fields are present and have correct types
        field_type_mapping = {
            "id": str,
            "name": str,
            "iban": str,
            "status": str,
            "trusted": bool,
            "created_at": str,
            "updated_at": str,
        }
        
        for field, expected_type in field_type_mapping.items():
            if field in beneficiary:
                assert isinstance(beneficiary[field], expected_type), \
                    f"Field {field} should be {expected_type}, got {type(beneficiary[field])}"
