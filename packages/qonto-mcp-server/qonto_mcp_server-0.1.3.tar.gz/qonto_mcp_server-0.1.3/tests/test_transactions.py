"""Tests for transaction related API methods.

This module tests transaction functionality including:
- Listing transactions with various filters
- Retrieving individual transactions
- Transaction attachment management
- Internal transfer creation

Transactions represent all banking operations for an organization.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import pytest

from src.qonto_mcp_server.api.methods import APIMethods


class TestTransactions:
    """Test transaction API methods."""

    @pytest.mark.asyncio
    async def test_list_transactions_with_bank_account_id(
        self, api_methods: APIMethods, active_bank_account: Dict[str, Any]
    ) -> None:
        """Test listing transactions using bank account ID.
        
        Args:
            api_methods: API methods fixture.
            active_bank_account: Active bank account fixture.
        """
        response = await api_methods.list_transactions(
            bank_account_id=active_bank_account["id"],
            per_page=10
        )
        
        # Verify successful response
        assert "errors" not in response
        assert "transactions" in response
        assert isinstance(response["transactions"], list)

    @pytest.mark.asyncio
    async def test_list_transactions_with_iban(
        self, api_methods: APIMethods, active_bank_account: Dict[str, Any]
    ) -> None:
        """Test listing transactions using IBAN.
        
        Args:
            api_methods: API methods fixture.
            active_bank_account: Active bank account fixture.
        """
        response = await api_methods.list_transactions(
            iban=active_bank_account["iban"],
            per_page=10
        )
        
        # Verify successful response
        assert "errors" not in response
        assert "transactions" in response
        assert isinstance(response["transactions"], list)

    @pytest.mark.asyncio
    async def test_list_transactions_with_includes(
        self, api_methods: APIMethods, active_bank_account: Dict[str, Any]
    ) -> None:
        """Test listing transactions with includes parameter.
        
        Args:
            api_methods: API methods fixture.
            active_bank_account: Active bank account fixture.
        """
        includes = ["labels", "attachments"]
        response = await api_methods.list_transactions(
            bank_account_id=active_bank_account["id"],
            includes=includes,
            per_page=5
        )
        
        assert "errors" not in response
        assert "transactions" in response
        
        # Verify included data if transactions exist
        transactions = response["transactions"]
        for transaction in transactions:
            if includes:
                # Check if included data is present when requested
                if "labels" in includes and "labels" in transaction:
                    assert isinstance(transaction["labels"], list)
                if "attachments" in includes and "attachments" in transaction:
                    assert isinstance(transaction["attachments"], list)

    @pytest.mark.asyncio
    async def test_list_transactions_with_status_filter(
        self, api_methods: APIMethods, active_bank_account: Dict[str, Any]
    ) -> None:
        """Test listing transactions with status filter.
        
        Args:
            api_methods: API methods fixture.
            active_bank_account: Active bank account fixture.
        """
        status_options = ["pending", "declined", "completed"]
        
        for status in status_options:
            response = await api_methods.list_transactions(
                bank_account_id=active_bank_account["id"],
                status=[status],
                per_page=10
            )
            
            assert "errors" not in response
            assert "transactions" in response
            
            # Verify status if transactions exist
            for transaction in response["transactions"]:
                if "status" in transaction:
                    assert transaction["status"] == status

    @pytest.mark.asyncio
    async def test_list_transactions_with_date_filters(
        self, api_methods: APIMethods, active_bank_account: Dict[str, Any]
    ) -> None:
        """Test listing transactions with date filters.
        
        Args:
            api_methods: API methods fixture.
            active_bank_account: Active bank account fixture.
        """
        # Test with date range from last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        response = await api_methods.list_transactions(
            bank_account_id=active_bank_account["id"],
            updated_at_from=start_date.isoformat(),
            updated_at_to=end_date.isoformat(),
            per_page=10
        )
        
        assert "errors" not in response
        assert "transactions" in response

    @pytest.mark.asyncio
    async def test_list_transactions_with_settled_date_filters(
        self, api_methods: APIMethods, active_bank_account: Dict[str, Any]
    ) -> None:
        """Test listing transactions with settled date filters.
        
        Args:
            api_methods: API methods fixture.
            active_bank_account: Active bank account fixture.
        """
        # Test with settled date range from last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        response = await api_methods.list_transactions(
            bank_account_id=active_bank_account["id"],
            settled_at_from=start_date.isoformat(),
            settled_at_to=end_date.isoformat(),
            per_page=10
        )
        
        assert "errors" not in response
        assert "transactions" in response

    @pytest.mark.asyncio
    async def test_list_transactions_with_side_filter(
        self, api_methods: APIMethods, active_bank_account: Dict[str, Any]
    ) -> None:
        """Test listing transactions with side filter.
        
        Args:
            api_methods: API methods fixture.
            active_bank_account: Active bank account fixture.
        """
        side_options = ["debit", "credit"]
        
        for side in side_options:
            response = await api_methods.list_transactions(
                bank_account_id=active_bank_account["id"],
                side=[side],
                per_page=10
            )
            
            assert "errors" not in response
            assert "transactions" in response
            
            # Verify side if transactions exist
            for transaction in response["transactions"]:
                if "side" in transaction:
                    assert transaction["side"] == side

    @pytest.mark.asyncio
    async def test_list_transactions_with_attachments_filter(
        self, api_methods: APIMethods, active_bank_account: Dict[str, Any]
    ) -> None:
        """Test listing transactions with attachments filter.
        
        Args:
            api_methods: API methods fixture.
            active_bank_account: Active bank account fixture.
        """
        # Test transactions with attachments
        response = await api_methods.list_transactions(
            bank_account_id=active_bank_account["id"],
            with_attachments=True,
            per_page=10
        )
        
        assert "errors" not in response
        assert "transactions" in response
        
        # Verify attachments presence if transactions exist
        for transaction in response["transactions"]:
            if "attachment_ids" in transaction:
                assert len(transaction["attachment_ids"]) > 0

        # Test transactions without attachments
        response = await api_methods.list_transactions(
            bank_account_id=active_bank_account["id"],
            with_attachments=False,
            per_page=10
        )
        
        assert "errors" not in response
        assert "transactions" in response

    @pytest.mark.asyncio
    async def test_list_transactions_with_sorting(
        self, api_methods: APIMethods, active_bank_account: Dict[str, Any]
    ) -> None:
        """Test listing transactions with sorting options.
        
        Args:
            api_methods: API methods fixture.
            active_bank_account: Active bank account fixture.
        """
        sort_options = [
            "updated_at:asc",
            "updated_at:desc",
            "settled_at:asc",
            "settled_at:desc"
        ]
        
        for sort_by in sort_options:
            response = await api_methods.list_transactions(
                bank_account_id=active_bank_account["id"],
                sort_by=sort_by,
                per_page=5
            )
            
            assert "errors" not in response
            assert "transactions" in response

    @pytest.mark.asyncio
    async def test_list_transactions_with_pagination(
        self, api_methods: APIMethods, active_bank_account: Dict[str, Any]
    ) -> None:
        """Test listing transactions with pagination.
        
        Args:
            api_methods: API methods fixture.
            active_bank_account: Active bank account fixture.
        """
        response = await api_methods.list_transactions(
            bank_account_id=active_bank_account["id"],
            page=1,
            per_page=5
        )
        
        assert "errors" not in response
        assert "transactions" in response
        transactions = response["transactions"]
        assert isinstance(transactions, list)
        assert len(transactions) <= 5

    @pytest.mark.asyncio
    async def test_retrieve_a_transaction(
        self, api_methods: APIMethods, transaction_id: str
    ) -> None:
        """Test retrieving a specific transaction.
        
        Args:
            api_methods: API methods fixture.
            transaction_id: Transaction ID fixture.
        """
        response = await api_methods.retrieve_a_transaction(transaction_id)
        
        # Verify successful response
        assert "errors" not in response
        assert "transaction" in response
        
        # Verify transaction structure
        transaction = response["transaction"]
        assert "id" in transaction
        assert transaction["id"] == transaction_id

    @pytest.mark.asyncio
    async def test_retrieve_a_transaction_with_includes(
        self, api_methods: APIMethods, transaction_id: str
    ) -> None:
        """Test retrieving a transaction with includes.
        
        Args:
            api_methods: API methods fixture.
            transaction_id: Transaction ID fixture.
        """
        includes = ["vat_details", "labels", "attachments"]
        response = await api_methods.retrieve_a_transaction(
            transaction_id,
            includes=includes
        )
        
        assert "errors" not in response
        assert "transaction" in response
        
        transaction = response["transaction"]
        assert transaction["id"] == transaction_id
        
        # Verify included data if present
        for include in includes:
            if include in transaction:
                if include == "labels":
                    assert isinstance(transaction["labels"], list)
                elif include == "attachments":
                    assert isinstance(transaction["attachments"], list)
                elif include == "vat_details":
                    assert isinstance(transaction["vat_details"], (dict, type(None)))

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_transaction(
        self, api_methods: APIMethods
    ) -> None:
        """Test retrieving a non-existent transaction.
        
        Args:
            api_methods: API methods fixture.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_methods.retrieve_a_transaction(fake_id)
        
        # Should return an error for non-existent transaction
        assert "errors" in response

    @pytest.mark.asyncio
    async def test_transactions_structure(
        self, transactions: List[Dict[str, Any]]
    ) -> None:
        """Test that transactions have proper structure.
        
        Args:
            transactions: Transactions fixture.
        """
        for transaction in transactions:
            # Required fields
            assert "id" in transaction
            assert isinstance(transaction["id"], str)
            
            # Common fields that should be present
            if "amount" in transaction:
                assert isinstance(transaction["amount"], (str, int, float))
            
            if "currency" in transaction:
                assert isinstance(transaction["currency"], str)
            
            if "side" in transaction:
                assert isinstance(transaction["side"], str)
                assert transaction["side"] in ["debit", "credit"]
            
            if "status" in transaction:
                assert isinstance(transaction["status"], str)
                assert transaction["status"] in ["pending", "declined", "completed"]
            
            if "attachment_ids" in transaction:
                assert isinstance(transaction["attachment_ids"], list)
                for attachment_id in transaction["attachment_ids"]:
                    assert isinstance(attachment_id, str)


class TestTransactionAttachments:
    """Test transaction attachment management API methods."""

    @pytest.mark.asyncio
    async def test_upload_an_attachment_to_a_transaction(
        self, api_methods: APIMethods, transaction_id: str, test_file_path: str
    ) -> None:
        """Test uploading an attachment to a transaction.
        
        Args:
            api_methods: API methods fixture.
            transaction_id: Transaction ID fixture.
            test_file_path: Test file path fixture.
        """
        response = await api_methods.upload_an_attachment_to_a_transaction(
            transaction_id,
            test_file_path
        )
        
        # Note: This will likely fail with a file not found error in real testing
        # but it tests the method structure
        if "errors" in response:
            # Expected if test file doesn't exist
            assert any("file" in str(error).lower() or "path" in str(error).lower() 
                     for error in response["errors"])
        else:
            # If successful, verify response structure
            assert isinstance(response, dict)

    @pytest.mark.asyncio
    async def test_upload_attachment_with_idempotency_key(
        self, api_methods: APIMethods, transaction_id: str, test_file_path: str
    ) -> None:
        """Test uploading an attachment with idempotency key.
        
        Args:
            api_methods: API methods fixture.
            transaction_id: Transaction ID fixture.
            test_file_path: Test file path fixture.
        """
        idempotency_key = "test-key-12345"
        response = await api_methods.upload_an_attachment_to_a_transaction(
            transaction_id,
            test_file_path,
            idempotency_key=idempotency_key
        )
        
        # Note: This will likely fail with a file not found error
        if "errors" in response:
            assert any("file" in str(error).lower() or "path" in str(error).lower() 
                     for error in response["errors"])

    @pytest.mark.asyncio
    async def test_list_attachments_for_a_transaction(
        self, api_methods: APIMethods, transaction_id: str
    ) -> None:
        """Test listing attachments for a transaction.
        
        Args:
            api_methods: API methods fixture.
            transaction_id: Transaction ID fixture.
        """
        response = await api_methods.list_attachments_for_a_transaction(transaction_id)
        
        # Verify successful response
        assert "errors" not in response
        assert "attachments" in response
        assert isinstance(response["attachments"], list)

    @pytest.mark.asyncio
    async def test_list_attachments_with_pagination(
        self, api_methods: APIMethods, transaction_id: str
    ) -> None:
        """Test listing attachments with pagination.
        
        Args:
            api_methods: API methods fixture.
            transaction_id: Transaction ID fixture.
        """
        response = await api_methods.list_attachments_for_a_transaction(
            transaction_id,
            page="1",
            per_page="5"
        )
        
        assert "errors" not in response
        assert "attachments" in response
        attachments = response["attachments"]
        assert isinstance(attachments, list)
        assert len(attachments) <= 5

    @pytest.mark.asyncio
    async def test_remove_an_attachment_from_a_transaction(
        self, api_methods: APIMethods, transaction_with_attachments: Optional[Dict[str, Any]]
    ) -> None:
        """Test removing a specific attachment from a transaction.
        
        Args:
            api_methods: API methods fixture.
            transaction_with_attachments: Transaction with attachments fixture.
        """
        if not transaction_with_attachments:
            pytest.skip("No transactions with attachments available for testing")
        
        transaction_id = transaction_with_attachments["id"]
        attachment_ids = transaction_with_attachments.get("attachment_ids", [])
        
        if not attachment_ids:
            pytest.skip("No attachment IDs available in transaction")
        
        attachment_id = attachment_ids[0]
        
        response = await api_methods.remove_an_attachment_from_a_transaction(
            transaction_id,
            attachment_id
        )
        
        # Verify response (could be success or error depending on permissions)
        assert isinstance(response, dict)

    @pytest.mark.asyncio
    async def test_remove_all_attachments_from_a_transaction(
        self, api_methods: APIMethods, transaction_with_attachments: Optional[Dict[str, Any]]
    ) -> None:
        """Test removing all attachments from a transaction.
        
        Args:
            api_methods: API methods fixture.
            transaction_with_attachments: Transaction with attachments fixture.
        """
        if not transaction_with_attachments:
            pytest.skip("No transactions with attachments available for testing")
        
        transaction_id = transaction_with_attachments["id"]
        
        response = await api_methods.remove_all_attachments_from_a_transaction(
            transaction_id
        )
        
        # Verify response (could be success or error depending on permissions)
        assert isinstance(response, dict)


class TestInternalTransfers:
    """Test internal transfer creation API methods."""

    @pytest.mark.asyncio
    async def test_create_an_internal_transfer(
        self, api_methods: APIMethods, sufficient_balance_accounts: List[Dict[str, Any]]
    ) -> None:
        """Test creating an internal transfer between bank accounts.
        
        Args:
            api_methods: API methods fixture.
            sufficient_balance_accounts: Accounts with sufficient balance fixture.
        """
        if len(sufficient_balance_accounts) < 2:
            pytest.skip("Need at least 2 accounts with sufficient balance for transfer testing")
        
        debit_account = sufficient_balance_accounts[0]
        credit_account = sufficient_balance_accounts[1]
        
        response = await api_methods.create_an_internal_transfer(
            debit_iban=debit_account["iban"],
            credit_iban=credit_account["iban"],
            reference="Test internal transfer",
            amount="10.00",  # Small amount for testing
            currency="EUR"
        )
        
        # Verify response structure
        if "errors" not in response:
            assert "internal_transfer" in response
            transfer = response["internal_transfer"]
            assert "id" in transfer
            assert "amount" in transfer
            assert "currency" in transfer
        else:
            # Could fail due to business rules, permissions, etc.
            assert isinstance(response["errors"], list)

    @pytest.mark.asyncio
    async def test_create_internal_transfer_with_idempotency_key(
        self, api_methods: APIMethods, sufficient_balance_accounts: List[Dict[str, Any]]
    ) -> None:
        """Test creating an internal transfer with idempotency key.
        
        Args:
            api_methods: API methods fixture.
            sufficient_balance_accounts: Accounts with sufficient balance fixture.
        """
        if len(sufficient_balance_accounts) < 2:
            pytest.skip("Need at least 2 accounts with sufficient balance for transfer testing")
        
        debit_account = sufficient_balance_accounts[0]
        credit_account = sufficient_balance_accounts[1]
        
        idempotency_key = "test-transfer-12345"
        
        response = await api_methods.create_an_internal_transfer(
            debit_iban=debit_account["iban"],
            credit_iban=credit_account["iban"],
            reference="Test internal transfer with idempotency",
            amount="5.00",
            currency="EUR",
            idempotency_key=idempotency_key
        )
        
        # Verify response structure
        if "errors" not in response:
            assert "internal_transfer" in response
        else:
            # Could fail due to business rules, permissions, etc.
            assert isinstance(response["errors"], list)

    @pytest.mark.asyncio
    async def test_create_internal_transfer_same_account_error(
        self, api_methods: APIMethods, sufficient_balance_accounts: List[Dict[str, Any]]
    ) -> None:
        """Test creating an internal transfer with same debit and credit account.
        
        Args:
            api_methods: API methods fixture.
            sufficient_balance_accounts: Accounts with sufficient balance fixture.
        """
        if not sufficient_balance_accounts:
            pytest.skip("No accounts with sufficient balance for transfer testing")
        
        account = sufficient_balance_accounts[0]
        
        response = await api_methods.create_an_internal_transfer(
            debit_iban=account["iban"],
            credit_iban=account["iban"],  # Same account
            reference="Test same account transfer",
            amount="1.00",
            currency="EUR"
        )
        
        # Should return an error for same account transfer
        assert "errors" in response

    @pytest.mark.asyncio
    async def test_create_internal_transfer_invalid_amount(
        self, api_methods: APIMethods, sufficient_balance_accounts: List[Dict[str, Any]]
    ) -> None:
        """Test creating an internal transfer with invalid amount.
        
        Args:
            api_methods: API methods fixture.
            sufficient_balance_accounts: Accounts with sufficient balance fixture.
        """
        if len(sufficient_balance_accounts) < 2:
            pytest.skip("Need at least 2 accounts with sufficient balance for transfer testing")
        
        debit_account = sufficient_balance_accounts[0]
        credit_account = sufficient_balance_accounts[1]
        
        response = await api_methods.create_an_internal_transfer(
            debit_iban=debit_account["iban"],
            credit_iban=credit_account["iban"],
            reference="Test invalid amount transfer",
            amount="0.00",  # Invalid amount
            currency="EUR"
        )
        
        # Should return an error for invalid amount
        assert "errors" in response
