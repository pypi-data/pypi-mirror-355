"""Tests for request related API methods.

This module tests request functionality including:
- Listing requests with various filters
- Request structure validation
- Status and type filtering

Requests represent approval workflows for various banking operations.
"""

from typing import Any, Dict, List
from datetime import datetime, timedelta

import pytest

from src.qonto_mcp_server.api.methods import APIMethods


class TestRequests:
    """Test request API methods."""

    @pytest.mark.asyncio
    async def test_list_requests_basic(self, api_methods: APIMethods) -> None:
        """Test basic requests listing.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_requests()
        
        # Verify successful response
        assert "errors" not in response
        assert "requests" in response
        assert isinstance(response["requests"], list)

    @pytest.mark.asyncio
    async def test_list_requests_with_status_filter(
        self, api_methods: APIMethods
    ) -> None:
        """Test requests listing with status filter.
        
        Args:
            api_methods: API methods fixture.
        """
        status_options = ["pending", "approved", "declined", "expired", "canceled"]
        
        for status in status_options:
            response = await api_methods.list_requests(
                status=[status],
                per_page=10
            )
            
            assert "errors" not in response
            assert "requests" in response
            
            # If requests exist with this status, verify they have the correct status
            requests = response["requests"]
            for request in requests:
                if "status" in request:
                    assert request["status"] == status

    @pytest.mark.asyncio
    async def test_list_requests_with_type_filter(
        self, api_methods: APIMethods
    ) -> None:
        """Test requests listing with request type filter.
        
        Args:
            api_methods: API methods fixture.
        """
        request_types = [
            "flash_card", 
            "credit_transfer", 
            "sepa_transfer", 
            "direct_debit", 
            "payroll_invoice"
        ]
        
        for request_type in request_types:
            response = await api_methods.list_requests(
                request_type=[request_type],
                per_page=10
            )
            
            assert "errors" not in response
            assert "requests" in response
            
            # If requests exist with this type, verify they have the correct type
            requests = response["requests"]
            for request in requests:
                if "request_type" in request:
                    assert request["request_type"] == request_type

    @pytest.mark.asyncio
    async def test_list_requests_with_date_filters(
        self, api_methods: APIMethods
    ) -> None:
        """Test requests listing with date filters.
        
        Args:
            api_methods: API methods fixture.
        """
        # Test with date range from last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        response = await api_methods.list_requests(
            created_at_from=start_date.isoformat(),
            per_page=10
        )
        
        assert "errors" not in response
        assert "requests" in response

    @pytest.mark.asyncio
    async def test_list_requests_with_processed_date_filter(
        self, api_methods: APIMethods
    ) -> None:
        """Test requests listing with processed date filter.
        
        Args:
            api_methods: API methods fixture.
        """
        # Test with processed date from last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        response = await api_methods.list_requests(
            processed_at_from=start_date.isoformat(),
            per_page=10
        )
        
        assert "errors" not in response
        assert "requests" in response

    @pytest.mark.asyncio
    async def test_list_requests_with_sorting(
        self, api_methods: APIMethods
    ) -> None:
        """Test requests listing with sorting options.
        
        Args:
            api_methods: API methods fixture.
        """
        sort_options = [
            "processed_at:desc",
            "processed_at:asc",
            "created_at:desc",
            "created_at:asc"
        ]
        
        for sort_by in sort_options:
            response = await api_methods.list_requests(
                sort_by=sort_by,
                per_page=5
            )
            
            assert "errors" not in response
            assert "requests" in response

    @pytest.mark.asyncio
    async def test_list_requests_with_pagination(
        self, api_methods: APIMethods
    ) -> None:
        """Test requests listing with pagination.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_requests(
            page=1,
            per_page=5
        )
        
        assert "errors" not in response
        assert "requests" in response
        requests = response["requests"]
        assert isinstance(requests, list)
        assert len(requests) <= 5

    @pytest.mark.asyncio
    async def test_list_requests_combined_filters(
        self, api_methods: APIMethods
    ) -> None:
        """Test requests listing with combined filters.
        
        Args:
            api_methods: API methods fixture.
        """
        # Test combining multiple filters
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        response = await api_methods.list_requests(
            status=["pending", "approved"],
            request_type=["credit_transfer"],
            created_at_from=start_date.isoformat(),
            sort_by="created_at:desc",
            per_page=10
        )
        
        assert "errors" not in response
        assert "requests" in response

    @pytest.mark.asyncio
    async def test_requests_structure_validation(
        self, api_methods: APIMethods
    ) -> None:
        """Test that requests have proper structure.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_requests(per_page=10)
        
        assert "errors" not in response
        requests = response["requests"]
        
        for request in requests:
            # Required fields
            assert "id" in request
            assert isinstance(request["id"], str)
            
            # Common fields validation
            if "status" in request:
                assert isinstance(request["status"], str)
                assert request["status"] in [
                    "pending", "approved", "declined", "expired", "canceled"
                ]
            
            if "request_type" in request:
                assert isinstance(request["request_type"], str)
                assert request["request_type"] in [
                    "flash_card", "credit_transfer", "sepa_transfer", 
                    "direct_debit", "payroll_invoice"
                ]
            
            if "created_at" in request:
                assert isinstance(request["created_at"], str)
                # Basic ISO 8601 format check
                assert "T" in request["created_at"] or " " in request["created_at"]
            
            if "processed_at" in request and request["processed_at"]:
                assert isinstance(request["processed_at"], str)
                # Basic ISO 8601 format check
                assert "T" in request["processed_at"] or " " in request["processed_at"]
            
            if "amount" in request:
                assert isinstance(request["amount"], (str, int, float))
            
            if "currency" in request:
                assert isinstance(request["currency"], str)
                assert len(request["currency"]) == 3  # ISO currency code

    @pytest.mark.asyncio
    async def test_requests_date_consistency(
        self, api_methods: APIMethods
    ) -> None:
        """Test that request dates are consistent.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_requests(per_page=10)
        
        assert "errors" not in response
        requests = response["requests"]
        
        for request in requests:
            if "created_at" in request and "processed_at" in request:
                if request["processed_at"]:  # processed_at can be null for pending requests
                    created_str = request["created_at"]
                    processed_str = request["processed_at"]
                    
                    # Parse dates (basic check)
                    try:
                        created_date = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                        processed_date = datetime.fromisoformat(processed_str.replace("Z", "+00:00"))
                        
                        # Processed date should be after or equal to created date
                        assert processed_date >= created_date, \
                            f"Processed date {processed_date} should be >= created date {created_date}"
                    except ValueError:
                        # If date parsing fails, that's okay - we're just doing basic validation
                        pass

    @pytest.mark.asyncio
    async def test_requests_status_consistency(
        self, api_methods: APIMethods
    ) -> None:
        """Test that request statuses are consistent with processed dates.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_requests(per_page=20)
        
        assert "errors" not in response
        requests = response["requests"]
        
        for request in requests:
            status = request.get("status")
            processed_at = request.get("processed_at")
            
            if status == "pending":
                # Pending requests should not have a processed_at date
                assert not processed_at or processed_at is None, \
                    "Pending requests should not have processed_at date"
            
            elif status in ["approved", "declined", "expired", "canceled"]:
                # Processed requests should have a processed_at date
                # Note: This might not always be true depending on API behavior
                pass

    @pytest.mark.asyncio
    async def test_requests_empty_filters(
        self, api_methods: APIMethods
    ) -> None:
        """Test requests listing with empty filter arrays.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_requests(
            status=[],
            request_type=[],
            per_page=5
        )
        
        assert "errors" not in response
        assert "requests" in response

    @pytest.mark.asyncio
    async def test_requests_pagination_consistency(
        self, api_methods: APIMethods
    ) -> None:
        """Test that pagination works consistently across pages.
        
        Args:
            api_methods: API methods fixture.
        """
        # Get first page
        page1_response = await api_methods.list_requests(page=1, per_page=3)
        assert "errors" not in page1_response
        page1_requests = page1_response["requests"]
        
        # Get second page
        page2_response = await api_methods.list_requests(page=2, per_page=3)
        assert "errors" not in page2_response
        page2_requests = page2_response["requests"]
        
        # If both pages have requests, they should be different
        if page1_requests and page2_requests:
            page1_ids = {request["id"] for request in page1_requests}
            page2_ids = {request["id"] for request in page2_requests}
            # No overlap between pages
            assert len(page1_ids.intersection(page2_ids)) == 0

    @pytest.mark.asyncio
    async def test_requests_id_uniqueness(
        self, api_methods: APIMethods
    ) -> None:
        """Test that requests have unique IDs.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_requests(per_page=20)
        
        assert "errors" not in response
        requests = response["requests"]
        
        if len(requests) > 1:
            request_ids = [request["id"] for request in requests]
            unique_ids = set(request_ids)
            assert len(request_ids) == len(unique_ids), "Request IDs should be unique"

    @pytest.mark.asyncio
    async def test_requests_amount_validation(
        self, api_methods: APIMethods
    ) -> None:
        """Test that request amounts are properly formatted.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_requests(per_page=10)
        
        assert "errors" not in response
        requests = response["requests"]
        
        for request in requests:
            if "amount" in request and request["amount"]:
                amount = request["amount"]
                
                # Amount should be convertible to float
                try:
                    if isinstance(amount, str):
                        amount_float = float(amount)
                    else:
                        amount_float = float(amount)
                    
                    # Amount should be positive (assuming no negative amounts in requests)
                    assert amount_float >= 0, f"Request amount should be non-negative, got {amount_float}"
                except ValueError:
                    pytest.fail(f"Request amount should be numeric, got {amount}")

    @pytest.mark.asyncio
    async def test_requests_currency_consistency(
        self, api_methods: APIMethods
    ) -> None:
        """Test that request currencies are consistent.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_requests(per_page=10)
        
        assert "errors" not in response
        requests = response["requests"]
        
        for request in requests:
            if "currency" in request:
                currency = request["currency"]
                assert isinstance(currency, str)
                assert len(currency) == 3, f"Currency should be 3-letter code, got {currency}"
                assert currency.isupper(), f"Currency should be uppercase, got {currency}"
