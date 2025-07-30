"""Tests for external transfer related API methods.

This module tests external transfer functionality including:
- Listing external transfers with various filters
- Retrieving individual external transfers
- Parameter validation and error handling

External transfers represent outbound payments to external beneficiaries.
"""

from typing import Any, Dict, List
from datetime import datetime, timedelta

import pytest

from src.qonto_mcp_server.api.methods import APIMethods


class TestExternalTransfers:
    """Test external transfer API methods."""

    @pytest.mark.asyncio
    async def test_list_external_transfers_basic(self, api_methods: APIMethods) -> None:
        """Test basic external transfers listing.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_external_transfers()
        
        # Verify successful response
        assert "errors" not in response
        assert "external_transfers" in response
        assert isinstance(response["external_transfers"], list)

    @pytest.mark.asyncio
    async def test_list_external_transfers_with_pagination(
        self, api_methods: APIMethods
    ) -> None:
        """Test external transfers listing with pagination.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_external_transfers(
            page="1",
            per_page="5"
        )
        
        assert "errors" not in response
        assert "external_transfers" in response
        transfers = response["external_transfers"]
        assert isinstance(transfers, list)
        assert len(transfers) <= 5

    @pytest.mark.asyncio
    async def test_list_external_transfers_with_status_filter(
        self, api_methods: APIMethods
    ) -> None:
        """Test external transfers listing with status filter.
        
        Args:
            api_methods: API methods fixture.
        """
        # Test with common status values
        for status in ["pending", "processing", "settled", "canceled", "declined"]:
            response = await api_methods.list_external_transfers(
                status=[status],
                per_page="10"
            )
            
            assert "errors" not in response
            assert "external_transfers" in response
            
            # If transfers exist with this status, verify they have the correct status
            transfers = response["external_transfers"]
            for transfer in transfers:
                if "status" in transfer:
                    assert transfer["status"] == status

    @pytest.mark.asyncio
    async def test_list_external_transfers_with_date_filters(
        self, api_methods: APIMethods
    ) -> None:
        """Test external transfers listing with date filters.
        
        Args:
            api_methods: API methods fixture.
        """
        # Test with date range from last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        response = await api_methods.list_external_transfers(
            updated_at_from=start_date.isoformat(),
            updated_at_to=end_date.isoformat(),
            per_page="10"
        )
        
        assert "errors" not in response
        assert "external_transfers" in response

    @pytest.mark.asyncio
    async def test_list_external_transfers_with_sorting(
        self, api_methods: APIMethods
    ) -> None:
        """Test external transfers listing with sorting options.
        
        Args:
            api_methods: API methods fixture.
        """
        sort_options = [
            "updated_at:asc",
            "updated_at:desc",
            "scheduled_date:asc",
            "scheduled_date:desc"
        ]
        
        for sort_by in sort_options:
            response = await api_methods.list_external_transfers(
                sort_by=sort_by,
                per_page="5"
            )
            
            assert "errors" not in response
            assert "external_transfers" in response

    @pytest.mark.asyncio
    async def test_retrieve_an_external_transfer(
        self, api_methods: APIMethods, external_transfer_id: str
    ) -> None:
        """Test retrieving a specific external transfer.
        
        Args:
            api_methods: API methods fixture.
            external_transfer_id: External transfer ID fixture.
        """
        response = await api_methods.retrieve_an_external_transfer(external_transfer_id)
        
        # Verify successful response
        assert "errors" not in response
        assert "external_transfer" in response
        
        # Verify transfer structure
        transfer = response["external_transfer"]
        assert "id" in transfer
        assert transfer["id"] == external_transfer_id
        
        # Verify common fields
        assert "status" in transfer
        assert "amount" in transfer
        assert "currency" in transfer

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_external_transfer(
        self, api_methods: APIMethods
    ) -> None:
        """Test retrieving a non-existent external transfer.
        
        Args:
            api_methods: API methods fixture.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_methods.retrieve_an_external_transfer(fake_id)
        
        # Should return an error for non-existent transfer
        assert "errors" in response

    @pytest.mark.asyncio
    async def test_external_transfer_structure(
        self, external_transfers: List[Dict[str, Any]]
    ) -> None:
        """Test that external transfers have proper structure.
        
        Args:
            external_transfers: External transfers fixture.
        """
        for transfer in external_transfers:
            # Required fields
            assert "id" in transfer
            assert isinstance(transfer["id"], str)
            
            # Common fields that should be present
            if "status" in transfer:
                assert isinstance(transfer["status"], str)
                assert transfer["status"] in [
                    "pending", "processing", "canceled", "declined", "settled"
                ]
            
            if "amount" in transfer:
                assert isinstance(transfer["amount"], (str, int, float))
            
            if "currency" in transfer:
                assert isinstance(transfer["currency"], str)
            
            if "beneficiary_id" in transfer:
                assert isinstance(transfer["beneficiary_id"], str)

    @pytest.mark.asyncio
    async def test_list_external_transfers_with_beneficiary_filter(
        self, api_methods: APIMethods, beneficiaries: List[Dict[str, Any]]
    ) -> None:
        """Test external transfers listing filtered by beneficiary.
        
        Args:
            api_methods: API methods fixture.
            beneficiaries: Beneficiaries fixture.
        """
        if not beneficiaries:
            pytest.skip("No beneficiaries available for filtering test")
        
        # Use first beneficiary ID for filtering
        beneficiary_id = beneficiaries[0]["id"]
        
        response = await api_methods.list_external_transfers(
            beneficiary_ids=[beneficiary_id],
            per_page="10"
        )
        
        assert "errors" not in response
        assert "external_transfers" in response
        
        # If transfers exist, they should be associated with the specified beneficiary
        transfers = response["external_transfers"]
        for transfer in transfers:
            if "beneficiary_id" in transfer:
                assert transfer["beneficiary_id"] == beneficiary_id

    @pytest.mark.asyncio
    async def test_list_external_transfers_empty_filters(
        self, api_methods: APIMethods
    ) -> None:
        """Test external transfers listing with empty filter arrays.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_external_transfers(
            status=[],
            beneficiary_ids=[],
            per_page="5"
        )
        
        assert "errors" not in response
        assert "external_transfers" in response

    @pytest.mark.asyncio
    async def test_external_transfer_detailed_retrieve(
        self, api_methods: APIMethods, external_transfer_id: str
    ) -> None:
        """Test detailed retrieval of external transfer with all fields.
        
        Args:
            api_methods: API methods fixture.
            external_transfer_id: External transfer ID fixture.
        """
        response = await api_methods.retrieve_an_external_transfer(external_transfer_id)
        
        assert "errors" not in response
        transfer = response["external_transfer"]
        
        # Verify detailed fields are present and have correct types
        field_type_mapping = {
            "id": str,
            "status": str,
            "amount": (str, int, float),
            "currency": str,
            "reference": str,
            "created_at": str,
            "updated_at": str,
        }
        
        for field, expected_type in field_type_mapping.items():
            if field in transfer:
                assert isinstance(transfer[field], expected_type), \
                    f"Field {field} should be {expected_type}, got {type(transfer[field])}"

    @pytest.mark.asyncio
    async def test_list_external_transfers_scheduled_date_filter(
        self, api_methods: APIMethods
    ) -> None:
        """Test external transfers listing with scheduled date filters.
        
        Args:
            api_methods: API methods fixture.
        """
        # Test with scheduled date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        response = await api_methods.list_external_transfers(
            scheduled_date_from=start_date.isoformat(),
            scheduled_date_to=end_date.isoformat(),
            per_page="10"
        )
        
        assert "errors" not in response
        assert "external_transfers" in response
        
        # Verify transfers are within the date range if scheduled_date is present
        transfers = response["external_transfers"]
        for transfer in transfers:
            if "scheduled_date" in transfer and transfer["scheduled_date"]:
                scheduled_date = datetime.fromisoformat(
                    transfer["scheduled_date"].replace("Z", "+00:00")
                )
                assert start_date <= scheduled_date <= end_date
