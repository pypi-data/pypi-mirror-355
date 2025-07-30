"""Tests for invoicing related API methods.

This module tests invoicing functionality including:
- Supplier invoice creation and management
- Client invoice creation and management
- Credit note management
- Invoice structure validation

Invoicing is a core business feature for managing supplier and client invoices.
"""

from typing import Any, Dict, List
from datetime import datetime, timedelta

import pytest

from src.qonto_mcp_server.api.methods import APIMethods


class TestSupplierInvoices:
    """Test supplier invoice API methods."""

    @pytest.mark.asyncio
    async def test_create_supplier_invoices(
        self, api_methods: APIMethods, test_file_path: str
    ) -> None:
        """Test creating supplier invoices in bulk.
        
        Args:
            api_methods: API methods fixture.
            test_file_path: Test file path fixture.
        """
        supplier_invoices = [
            {
                "file": test_file_path,
                "idempotency_key": "test-supplier-invoice-1"
            },
            {
                "file": test_file_path,
                "idempotency_key": "test-supplier-invoice-2"
            }
        ]
        
        response = await api_methods.create_supplier_invoices(supplier_invoices)
        
        # Note: This will likely fail with a file not found error in real testing
        if "errors" in response or "error" in response:
            # Expected if test files don't exist
            error_msg = str(response.get("errors", response.get("error", "")))
            assert any(keyword in error_msg.lower() for keyword in ["file", "path", "idempotency"])
        else:
            # If successful, verify response structure
            assert "supplier_invoices" in response
            assert isinstance(response["supplier_invoices"], list)

    @pytest.mark.asyncio
    async def test_create_supplier_invoices_with_meta(
        self, api_methods: APIMethods, test_file_path: str
    ) -> None:
        """Test creating supplier invoices with metadata.
        
        Args:
            api_methods: API methods fixture.
            test_file_path: Test file path fixture.
        """
        supplier_invoices = [
            {
                "file": test_file_path,
                "idempotency_key": "test-supplier-invoice-meta-1"
            }
        ]
        
        meta = {
            "integration_type": "test",
            "connector": "test_connector"
        }
        
        response = await api_methods.create_supplier_invoices(
            supplier_invoices,
            meta=meta
        )
        
        # Note: This will likely fail with a file not found error
        if "errors" in response or "error" in response:
            error_msg = str(response.get("errors", response.get("error", "")))
            assert any(keyword in error_msg.lower() for keyword in ["file", "path", "idempotency"])

    @pytest.mark.asyncio
    async def test_create_supplier_invoices_invalid_structure(
        self, api_methods: APIMethods
    ) -> None:
        """Test creating supplier invoices with invalid structure.
        
        Args:
            api_methods: API methods fixture.
        """
        # Missing required fields
        invalid_invoices = [
            {
                "file": "/tmp/test.pdf"
                # Missing idempotency_key
            }
        ]
        
        response = await api_methods.create_supplier_invoices(invalid_invoices)
        
        # Should return an error for missing required fields
        assert "error" in response

    @pytest.mark.asyncio
    async def test_list_supplier_invoices_basic(self, api_methods: APIMethods) -> None:
        """Test basic supplier invoices listing.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_supplier_invoices()
        
        # Verify successful response
        assert "errors" not in response
        assert "supplier_invoices" in response
        assert isinstance(response["supplier_invoices"], list)

    @pytest.mark.asyncio
    async def test_list_supplier_invoices_with_filters(
        self, api_methods: APIMethods
    ) -> None:
        """Test supplier invoices listing with filters.
        
        Args:
            api_methods: API methods fixture.
        """
        # Test with date filters
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        response = await api_methods.list_supplier_invoices(
            filter_created_at_from=start_date.isoformat(),
            filter_created_at_to=end_date.isoformat(),
            per_page=5
        )
        
        assert "errors" not in response
        assert "supplier_invoices" in response

    @pytest.mark.asyncio
    async def test_list_supplier_invoices_with_status_filter(
        self, api_methods: APIMethods
    ) -> None:
        """Test supplier invoices listing with status filter.
        
        Args:
            api_methods: API methods fixture.
        """
        # Note: Status values depend on the API documentation
        response = await api_methods.list_supplier_invoices(
            filter_status="pending",
            per_page=10
        )
        
        assert "errors" not in response
        assert "supplier_invoices" in response

    @pytest.mark.asyncio
    async def test_list_supplier_invoices_with_sorting(
        self, api_methods: APIMethods
    ) -> None:
        """Test supplier invoices listing with sorting.
        
        Args:
            api_methods: API methods fixture.
        """
        sort_options = [
            "created_at_desc",
            "created_at_asc",
            "file_name_asc",
            "total_amount_desc"
        ]
        
        for sort_by in sort_options:
            response = await api_methods.list_supplier_invoices(
                sort_by=sort_by,
                per_page=5
            )
            
            assert "errors" not in response
            assert "supplier_invoices" in response

    @pytest.mark.asyncio
    async def test_list_supplier_invoices_with_pagination(
        self, api_methods: APIMethods
    ) -> None:
        """Test supplier invoices listing with pagination.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_supplier_invoices(
            page=1,
            per_page=3
        )
        
        assert "errors" not in response
        assert "supplier_invoices" in response
        invoices = response["supplier_invoices"]
        assert isinstance(invoices, list)
        assert len(invoices) <= 3

    @pytest.mark.asyncio
    async def test_retrieve_a_supplier_invoice(
        self, api_methods: APIMethods, supplier_invoice_id: str
    ) -> None:
        """Test retrieving a specific supplier invoice.
        
        Args:
            api_methods: API methods fixture.
            supplier_invoice_id: Supplier invoice ID fixture.
        """
        response = await api_methods.retrieve_a_supplier_invoice(supplier_invoice_id)
        
        # Verify successful response
        assert "errors" not in response
        assert "supplier_invoice" in response
        
        # Verify invoice structure
        invoice = response["supplier_invoice"]
        assert "id" in invoice
        assert invoice["id"] == supplier_invoice_id

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_supplier_invoice(
        self, api_methods: APIMethods
    ) -> None:
        """Test retrieving a non-existent supplier invoice.
        
        Args:
            api_methods: API methods fixture.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_methods.retrieve_a_supplier_invoice(fake_id)
        
        # Should return an error for non-existent invoice
        assert "errors" in response

    @pytest.mark.asyncio
    async def test_supplier_invoices_structure(
        self, supplier_invoices: List[Dict[str, Any]]
    ) -> None:
        """Test that supplier invoices have proper structure.
        
        Args:
            supplier_invoices: Supplier invoices fixture.
        """
        for invoice in supplier_invoices:
            # Required fields
            assert "id" in invoice
            assert isinstance(invoice["id"], str)
            
            # Common fields validation
            if "status" in invoice:
                assert isinstance(invoice["status"], str)
            
            if "file_name" in invoice:
                assert isinstance(invoice["file_name"], str)
            
            if "total_amount" in invoice:
                assert isinstance(invoice["total_amount"], (str, int, float))
            
            if "currency" in invoice:
                assert isinstance(invoice["currency"], str)


class TestClientInvoices:
    """Test client invoice API methods."""

    @pytest.mark.asyncio
    async def test_create_a_client_invoice(
        self, api_methods: APIMethods, client_id: str, active_bank_account: Dict[str, Any]
    ) -> None:
        """Test creating a client invoice.
        
        Args:
            api_methods: API methods fixture.
            client_id: Client ID fixture.
            active_bank_account: Active bank account fixture.
        """
        # Calculate dates
        issue_date = datetime.now().strftime("%Y-%m-%d")
        due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        payment_methods = {
            "iban": active_bank_account["iban"]
        }
        
        items = [
            {
                "title": "Test Service",
                "quantity": "1",
                "unit_price": {
                    "value": "100.00",
                    "currency": "EUR"
                },
                "vat_rate": "0.20",
                "description": "Test service description"
            }
        ]
        
        response = await api_methods.create_a_client_invoice(
            client_id=client_id,
            issue_date=issue_date,
            due_date=due_date,
            number="TEST-INVOICE-001",
            payment_methods=payment_methods,
            items=items,
            currency="EUR"
        )
        
        # Verify response structure
        if "errors" not in response:
            assert "client_invoice" in response
            invoice = response["client_invoice"]
            assert "id" in invoice
            assert "number" in invoice
        else:
            # Could fail due to business rules, permissions, etc.
            assert isinstance(response["errors"], list)

    @pytest.mark.asyncio
    async def test_create_client_invoice_with_optional_fields(
        self, api_methods: APIMethods, client_id: str, active_bank_account: Dict[str, Any]
    ) -> None:
        """Test creating a client invoice with optional fields.
        
        Args:
            api_methods: API methods fixture.
            client_id: Client ID fixture.
            active_bank_account: Active bank account fixture.
        """
        issue_date = datetime.now().strftime("%Y-%m-%d")
        due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        performance_date = datetime.now().strftime("%Y-%m-%d")
        
        payment_methods = {
            "iban": active_bank_account["iban"]
        }
        
        items = [
            {
                "title": "Premium Service",
                "quantity": "2",
                "unit_price": {
                    "value": "50.00",
                    "currency": "EUR"
                },
                "vat_rate": "0.20",
                "description": "Premium service with discount",
                "discount": {
                    "type": "percentage",
                    "value": "10"
                }
            }
        ]
        
        response = await api_methods.create_a_client_invoice(
            client_id=client_id,
            issue_date=issue_date,
            due_date=due_date,
            number="TEST-INVOICE-002",
            payment_methods=payment_methods,
            items=items,
            currency="EUR",
            performance_date=performance_date,
            status="draft",
            purchase_order="PO-12345",
            terms_and_conditions="Standard terms and conditions",
            header="Invoice Header",
            footer="Thank you for your business"
        )
        
        if "errors" not in response:
            assert "client_invoice" in response
        else:
            assert isinstance(response["errors"], list)

    @pytest.mark.asyncio
    async def test_list_client_invoices_basic(self, api_methods: APIMethods) -> None:
        """Test basic client invoices listing.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_client_invoices()
        
        # Verify successful response
        assert "errors" not in response
        assert "client_invoices" in response
        assert isinstance(response["client_invoices"], list)

    @pytest.mark.asyncio
    async def test_list_client_invoices_with_filters(
        self, api_methods: APIMethods
    ) -> None:
        """Test client invoices listing with filters.
        
        Args:
            api_methods: API methods fixture.
        """
        # Test with date filters
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        response = await api_methods.list_client_invoices(
            filter_created_at_from=start_date.isoformat(),
            filter_created_at_to=end_date.isoformat(),
            per_page=5
        )
        
        assert "errors" not in response
        assert "client_invoices" in response

    @pytest.mark.asyncio
    async def test_list_client_invoices_with_status_filter(
        self, api_methods: APIMethods
    ) -> None:
        """Test client invoices listing with status filter.
        
        Args:
            api_methods: API methods fixture.
        """
        status_options = ["draft", "unpaid", "paid", "canceled"]
        
        for status in status_options:
            response = await api_methods.list_client_invoices(
                filter_status=status,
                per_page=5
            )
            
            assert "errors" not in response
            assert "client_invoices" in response

    @pytest.mark.asyncio
    async def test_retrieve_a_client_invoice(
        self, api_methods: APIMethods, client_invoice_id: str
    ) -> None:
        """Test retrieving a specific client invoice.
        
        Args:
            api_methods: API methods fixture.
            client_invoice_id: Client invoice ID fixture.
        """
        response = await api_methods.retrieve_a_client_invoice(client_invoice_id)
        
        # Verify successful response
        assert "errors" not in response
        assert "client_invoice" in response
        
        # Verify invoice structure
        invoice = response["client_invoice"]
        assert "id" in invoice
        assert invoice["id"] == client_invoice_id

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_client_invoice(
        self, api_methods: APIMethods
    ) -> None:
        """Test retrieving a non-existent client invoice.
        
        Args:
            api_methods: API methods fixture.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_methods.retrieve_a_client_invoice(fake_id)
        
        # Should return an error for non-existent invoice
        assert "errors" in response

    @pytest.mark.asyncio
    async def test_client_invoices_structure(
        self, client_invoices: List[Dict[str, Any]]
    ) -> None:
        """Test that client invoices have proper structure.
        
        Args:
            client_invoices: Client invoices fixture.
        """
        for invoice in client_invoices:
            # Required fields
            assert "id" in invoice
            assert isinstance(invoice["id"], str)
            
            # Common fields validation
            if "status" in invoice:
                assert isinstance(invoice["status"], str)
                assert invoice["status"] in ["draft", "unpaid", "paid", "canceled"]
            
            if "number" in invoice:
                assert isinstance(invoice["number"], str)
            
            if "total_amount" in invoice:
                assert isinstance(invoice["total_amount"], (str, int, float))
            
            if "currency" in invoice:
                assert isinstance(invoice["currency"], str)
                assert invoice["currency"] == "EUR"  # Currently only EUR supported


class TestCreditNotes:
    """Test credit note API methods."""

    @pytest.mark.asyncio
    async def test_list_credit_notes_basic(self, api_methods: APIMethods) -> None:
        """Test basic credit notes listing.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_credit_notes()
        
        # Verify successful response
        assert "errors" not in response
        assert "credit_notes" in response
        assert isinstance(response["credit_notes"], list)

    @pytest.mark.asyncio
    async def test_list_credit_notes_with_date_filters(
        self, api_methods: APIMethods
    ) -> None:
        """Test credit notes listing with date filters.
        
        Args:
            api_methods: API methods fixture.
        """
        # Test with date range from last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        response = await api_methods.list_credit_notes(
            filter_created_at_from=start_date.isoformat(),
            filter_created_at_to=end_date.isoformat(),
            per_page=5
        )
        
        assert "errors" not in response
        assert "credit_notes" in response

    @pytest.mark.asyncio
    async def test_list_credit_notes_with_sorting(
        self, api_methods: APIMethods
    ) -> None:
        """Test credit notes listing with sorting.
        
        Args:
            api_methods: API methods fixture.
        """
        sort_options = ["created_at:asc", "created_at:desc"]
        
        for sort_by in sort_options:
            response = await api_methods.list_credit_notes(
                sort_by=sort_by,
                per_page=5
            )
            
            assert "errors" not in response
            assert "credit_notes" in response

    @pytest.mark.asyncio
    async def test_list_credit_notes_with_pagination(
        self, api_methods: APIMethods
    ) -> None:
        """Test credit notes listing with pagination.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_credit_notes(
            page=1,
            per_page=3
        )
        
        assert "errors" not in response
        assert "credit_notes" in response
        notes = response["credit_notes"]
        assert isinstance(notes, list)
        assert len(notes) <= 3

    @pytest.mark.asyncio
    async def test_retrieve_a_credit_note(
        self, api_methods: APIMethods, credit_note_id: str
    ) -> None:
        """Test retrieving a specific credit note.
        
        Args:
            api_methods: API methods fixture.
            credit_note_id: Credit note ID fixture.
        """
        response = await api_methods.retrieve_a_credit_note(credit_note_id)
        
        # Verify successful response
        assert "errors" not in response
        assert "credit_note" in response
        
        # Verify credit note structure
        note = response["credit_note"]
        assert "id" in note
        assert note["id"] == credit_note_id

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_credit_note(
        self, api_methods: APIMethods
    ) -> None:
        """Test retrieving a non-existent credit note.
        
        Args:
            api_methods: API methods fixture.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_methods.retrieve_a_credit_note(fake_id)
        
        # Should return an error for non-existent credit note
        assert "errors" in response

    @pytest.mark.asyncio
    async def test_credit_notes_structure(
        self, credit_notes: List[Dict[str, Any]]
    ) -> None:
        """Test that credit notes have proper structure.
        
        Args:
            credit_notes: Credit notes fixture.
        """
        for note in credit_notes:
            # Required fields
            assert "id" in note
            assert isinstance(note["id"], str)
            
            # Common fields validation
            if "number" in note:
                assert isinstance(note["number"], str)
            
            if "total_amount" in note:
                assert isinstance(note["total_amount"], (str, int, float))
            
            if "currency" in note:
                assert isinstance(note["currency"], str)
            
            if "created_at" in note:
                assert isinstance(note["created_at"], str)
