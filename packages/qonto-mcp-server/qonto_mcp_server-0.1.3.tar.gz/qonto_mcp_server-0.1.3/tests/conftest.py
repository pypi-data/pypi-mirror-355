"""Shared test fixtures and configuration for Qonto API integration tests.

This module provides comprehensive fixtures for testing all Qonto API methods
with real data. Fixtures are designed to be reusable across test modules and
handle the complex dependencies between different API endpoints.

The fixtures fetch real data from the API to ensure tests work with actual
production-like scenarios while maintaining test isolation and reliability.

Dependencies:
    - pytest: Test framework and fixture management
    - pytest-asyncio: Async test support
    - typing: Type annotations for fixture return types
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple

import pytest
import pytest_asyncio

from src.qonto_mcp_server.api.client import APIClient
from src.qonto_mcp_server.api.config import APIConfig
from src.qonto_mcp_server.api.methods import APIMethods


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """Create an event loop for the test session.
    
    Returns:
        asyncio.AbstractEventLoop: Event loop for async test execution.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def api_config() -> APIConfig:
    """Create API configuration for testing.
    
    Returns:
        APIConfig: Configured API client settings for the test environment.
    """
    return APIConfig()


@pytest_asyncio.fixture(scope="session")
async def api_client(api_config: APIConfig) -> APIClient:
    """Create API client for testing.
    
    Args:
        api_config: API configuration fixture.
        
    Returns:
        APIClient: Configured HTTP client for API requests.
    """
    return APIClient(api_config)


@pytest_asyncio.fixture(scope="session")
async def api_methods(api_client: APIClient) -> APIMethods:
    """Create API methods instance for testing.
    
    Args:
        api_client: HTTP client fixture.
        
    Returns:
        APIMethods: Instance with all API method implementations.
    """
    return APIMethods(api_client)


@pytest_asyncio.fixture(scope="session")
async def organization_data(api_methods: APIMethods) -> Dict[str, Any]:
    """Fetch organization data and bank accounts for testing.
    
    This fixture retrieves the authenticated organization details and its
    associated bank accounts, which are required for many other tests.
    
    Args:
        api_methods: API methods fixture.
        
    Returns:
        Dict[str, Any]: Organization data including bank accounts.
        
    Raises:
        pytest.skip: If organization data cannot be retrieved.
    """
    response = await api_methods.retrieve_the_authenticated_organization_and_list_bank_accounts()
    if "errors" in response:
        pytest.skip(f"Cannot retrieve organization data: {response['errors']}")
    return response


@pytest_asyncio.fixture(scope="session")
async def bank_accounts(organization_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract bank accounts from organization data.
    
    Args:
        organization_data: Organization data fixture.
        
    Returns:
        List[Dict[str, Any]]: List of bank account objects.
        
    Raises:
        pytest.skip: If no bank accounts are available.
    """
    accounts = organization_data.get("organization", {}).get("bank_accounts", [])
    if not accounts:
        pytest.skip("No bank accounts available for testing")
    return accounts


@pytest_asyncio.fixture(scope="session")
async def active_bank_account(bank_accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get the first active bank account for testing.
    
    Args:
        bank_accounts: Bank accounts fixture.
        
    Returns:
        Dict[str, Any]: Active bank account data.
        
    Raises:
        pytest.skip: If no active bank accounts are available.
    """
    active_accounts = [acc for acc in bank_accounts if acc.get("status") == "active"]
    if not active_accounts:
        pytest.skip("No active bank accounts available for testing")
    return active_accounts[0]


@pytest_asyncio.fixture(scope="session")
async def sufficient_balance_accounts(bank_accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get bank accounts with sufficient balance for transfers.
    
    Args:
        bank_accounts: Bank accounts fixture.
        
    Returns:
        List[Dict[str, Any]]: Accounts with sufficient balance (>= 100 EUR).
        
    Raises:
        pytest.skip: If no accounts with sufficient balance are available.
    """
    sufficient_accounts = [
        acc for acc in bank_accounts 
        if acc.get("status") == "active" 
        and acc.get("balance_cents", 0) >= 10000  # >= 100 EUR
        and acc.get("authorized_balance_cents", 0) >= 10000
    ]
    if len(sufficient_accounts) < 2:
        pytest.skip("Need at least 2 accounts with sufficient balance for transfer testing")
    return sufficient_accounts


@pytest_asyncio.fixture(scope="session")
async def external_transfers(api_methods: APIMethods) -> List[Dict[str, Any]]:
    """Fetch external transfers for testing.
    
    Args:
        api_methods: API methods fixture.
        
    Returns:
        List[Dict[str, Any]]: List of external transfer objects.
        
    Raises:
        pytest.skip: If no external transfers are available.
    """
    response = await api_methods.list_external_transfers(per_page="10")
    if "errors" in response:
        pytest.skip(f"Cannot retrieve external transfers: {response['errors']}")
    
    transfers = response.get("external_transfers", [])
    if not transfers:
        pytest.skip("No external transfers available for testing")
    return transfers


@pytest_asyncio.fixture(scope="session")
async def external_transfer_id(external_transfers: List[Dict[str, Any]]) -> str:
    """Get the first external transfer ID for testing.
    
    Args:
        external_transfers: External transfers fixture.
        
    Returns:
        str: External transfer ID.
    """
    return external_transfers[0]["id"]


@pytest_asyncio.fixture(scope="session")
async def beneficiaries(api_methods: APIMethods) -> List[Dict[str, Any]]:
    """Fetch beneficiaries for testing.
    
    Args:
        api_methods: API methods fixture.
        
    Returns:
        List[Dict[str, Any]]: List of beneficiary objects.
        
    Raises:
        pytest.skip: If no beneficiaries are available.
    """
    response = await api_methods.list_beneficiaries(per_page="10")
    if "errors" in response:
        pytest.skip(f"Cannot retrieve beneficiaries: {response['errors']}")
    
    beneficiaries_list = response.get("beneficiaries", [])
    if not beneficiaries_list:
        pytest.skip("No beneficiaries available for testing")
    return beneficiaries_list


@pytest_asyncio.fixture(scope="session")
async def beneficiary_id(beneficiaries: List[Dict[str, Any]]) -> str:
    """Get the first beneficiary ID for testing.
    
    Args:
        beneficiaries: Beneficiaries fixture.
        
    Returns:
        str: Beneficiary ID.
    """
    return beneficiaries[0]["id"]


@pytest_asyncio.fixture(scope="session")
async def trusted_beneficiaries(api_methods: APIMethods) -> List[Dict[str, Any]]:
    """Fetch trusted beneficiaries for testing.
    
    Args:
        api_methods: API methods fixture.
        
    Returns:
        List[Dict[str, Any]]: List of trusted beneficiary objects.
        
    Raises:
        pytest.skip: If no trusted beneficiaries are available.
    """
    response = await api_methods.list_beneficiaries(trusted=True, per_page="10")
    if "errors" in response:
        pytest.skip(f"Cannot retrieve trusted beneficiaries: {response['errors']}")
    
    trusted_list = response.get("beneficiaries", [])
    if not trusted_list:
        pytest.skip("No trusted beneficiaries available for testing")
    return trusted_list


@pytest_asyncio.fixture(scope="session")
async def trusted_beneficiary_ids(trusted_beneficiaries: List[Dict[str, Any]]) -> List[str]:
    """Get trusted beneficiary IDs for testing.
    
    Args:
        trusted_beneficiaries: Trusted beneficiaries fixture.
        
    Returns:
        List[str]: List of trusted beneficiary IDs.
    """
    return [b["id"] for b in trusted_beneficiaries[:3]]  # Limit to 3 for testing


@pytest_asyncio.fixture(scope="session")
async def sepa_beneficiaries(api_methods: APIMethods) -> List[Dict[str, Any]]:
    """Fetch SEPA beneficiaries for testing.
    
    Args:
        api_methods: API methods fixture.
        
    Returns:
        List[Dict[str, Any]]: List of SEPA beneficiary objects.
        
    Raises:
        pytest.skip: If no SEPA beneficiaries are available.
    """
    response = await api_methods.list_sepa_beneficiaries(per_page=10)
    if "errors" in response:
        pytest.skip(f"Cannot retrieve SEPA beneficiaries: {response['errors']}")
    
    sepa_list = response.get("beneficiaries", [])
    if not sepa_list:
        pytest.skip("No SEPA beneficiaries available for testing")
    return sepa_list


@pytest_asyncio.fixture(scope="session")
async def sepa_beneficiary_id(sepa_beneficiaries: List[Dict[str, Any]]) -> str:
    """Get the first SEPA beneficiary ID for testing.
    
    Args:
        sepa_beneficiaries: SEPA beneficiaries fixture.
        
    Returns:
        str: SEPA beneficiary ID.
    """
    return sepa_beneficiaries[0]["id"]


@pytest_asyncio.fixture(scope="session")
async def labels(api_methods: APIMethods) -> List[Dict[str, Any]]:
    """Fetch labels for testing.
    
    Args:
        api_methods: API methods fixture.
        
    Returns:
        List[Dict[str, Any]]: List of label objects.
        
    Raises:
        pytest.skip: If no labels are available.
    """
    response = await api_methods.list_labels(per_page="10")
    if "errors" in response:
        pytest.skip(f"Cannot retrieve labels: {response['errors']}")
    
    labels_list = response.get("labels", [])
    if not labels_list:
        pytest.skip("No labels available for testing")
    return labels_list


@pytest_asyncio.fixture(scope="session")
async def label_id(labels: List[Dict[str, Any]]) -> str:
    """Get the first label ID for testing.
    
    Args:
        labels: Labels fixture.
        
    Returns:
        str: Label ID.
    """
    return labels[0]["id"]


@pytest_asyncio.fixture(scope="session")
async def transactions(api_methods: APIMethods, active_bank_account: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fetch transactions for testing.
    
    Args:
        api_methods: API methods fixture.
        active_bank_account: Active bank account fixture.
        
    Returns:
        List[Dict[str, Any]]: List of transaction objects.
        
    Raises:
        pytest.skip: If no transactions are available.
    """
    response = await api_methods.list_transactions(
        bank_account_id=active_bank_account["id"],
        per_page=10
    )
    if "errors" in response:
        pytest.skip(f"Cannot retrieve transactions: {response['errors']}")
    
    transactions_list = response.get("transactions", [])
    if not transactions_list:
        pytest.skip("No transactions available for testing")
    return transactions_list


@pytest_asyncio.fixture(scope="session")
async def transaction_id(transactions: List[Dict[str, Any]]) -> str:
    """Get the first transaction ID for testing.
    
    Args:
        transactions: Transactions fixture.
        
    Returns:
        str: Transaction ID.
    """
    return transactions[0]["id"]


@pytest_asyncio.fixture(scope="session")
async def transaction_with_attachments(transactions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Get a transaction that has attachments for testing.
    
    Args:
        transactions: Transactions fixture.
        
    Returns:
        Optional[Dict[str, Any]]: Transaction with attachments, or None if not found.
    """
    for transaction in transactions:
        if transaction.get("attachment_ids") and len(transaction["attachment_ids"]) > 0:
            return transaction
    return None


@pytest_asyncio.fixture(scope="session")
async def clients(api_methods: APIMethods) -> List[Dict[str, Any]]:
    """Fetch clients for testing.
    
    Args:
        api_methods: API methods fixture.
        
    Returns:
        List[Dict[str, Any]]: List of client objects.
        
    Raises:
        pytest.skip: If no clients are available.
    """
    response = await api_methods.list_clients(per_page=10)
    if "errors" in response:
        pytest.skip(f"Cannot retrieve clients: {response['errors']}")
    
    clients_list = response.get("clients", [])
    if not clients_list:
        pytest.skip("No clients available for testing")
    return clients_list


@pytest_asyncio.fixture(scope="session")
async def client_id(clients: List[Dict[str, Any]]) -> str:
    """Get the first client ID for testing.
    
    Args:
        clients: Clients fixture.
        
    Returns:
        str: Client ID.
    """
    return clients[0]["id"]


@pytest_asyncio.fixture(scope="session")
async def supplier_invoices(api_methods: APIMethods) -> List[Dict[str, Any]]:
    """Fetch supplier invoices for testing.
    
    Args:
        api_methods: API methods fixture.
        
    Returns:
        List[Dict[str, Any]]: List of supplier invoice objects.
        
    Raises:
        pytest.skip: If no supplier invoices are available.
    """
    response = await api_methods.list_supplier_invoices(per_page=10)
    if "errors" in response:
        pytest.skip(f"Cannot retrieve supplier invoices: {response['errors']}")
    
    invoices_list = response.get("supplier_invoices", [])
    if not invoices_list:
        pytest.skip("No supplier invoices available for testing")
    return invoices_list


@pytest_asyncio.fixture(scope="session")
async def supplier_invoice_id(supplier_invoices: List[Dict[str, Any]]) -> str:
    """Get the first supplier invoice ID for testing.
    
    Args:
        supplier_invoices: Supplier invoices fixture.
        
    Returns:
        str: Supplier invoice ID.
    """
    return supplier_invoices[0]["id"]


@pytest_asyncio.fixture(scope="session")
async def client_invoices(api_methods: APIMethods) -> List[Dict[str, Any]]:
    """Fetch client invoices for testing.
    
    Args:
        api_methods: API methods fixture.
        
    Returns:
        List[Dict[str, Any]]: List of client invoice objects.
        
    Raises:
        pytest.skip: If no client invoices are available.
    """
    response = await api_methods.list_client_invoices(per_page=10)
    if "errors" in response:
        pytest.skip(f"Cannot retrieve client invoices: {response['errors']}")
    
    invoices_list = response.get("client_invoices", [])
    if not invoices_list:
        pytest.skip("No client invoices available for testing")
    return invoices_list


@pytest_asyncio.fixture(scope="session")
async def client_invoice_id(client_invoices: List[Dict[str, Any]]) -> str:
    """Get the first client invoice ID for testing.
    
    Args:
        client_invoices: Client invoices fixture.
        
    Returns:
        str: Client invoice ID.
    """
    return client_invoices[0]["id"]


@pytest_asyncio.fixture(scope="session")
async def credit_notes(api_methods: APIMethods) -> List[Dict[str, Any]]:
    """Fetch credit notes for testing.
    
    Args:
        api_methods: API methods fixture.
        
    Returns:
        List[Dict[str, Any]]: List of credit note objects.
        
    Raises:
        pytest.skip: If no credit notes are available.
    """
    response = await api_methods.list_credit_notes(per_page=10)
    if "errors" in response:
        pytest.skip(f"Cannot retrieve credit notes: {response['errors']}")
    
    notes_list = response.get("credit_notes", [])
    if not notes_list:
        pytest.skip("No credit notes available for testing")
    return notes_list


@pytest_asyncio.fixture(scope="session")
async def credit_note_id(credit_notes: List[Dict[str, Any]]) -> str:
    """Get the first credit note ID for testing.
    
    Args:
        credit_notes: Credit notes fixture.
        
    Returns:
        str: Credit note ID.
    """
    return credit_notes[0]["id"]


@pytest_asyncio.fixture(scope="session")
async def statements(api_methods: APIMethods) -> List[Dict[str, Any]]:
    """Fetch statements for testing.
    
    Args:
        api_methods: API methods fixture.
        
    Returns:
        List[Dict[str, Any]]: List of statement objects.
        
    Raises:
        pytest.skip: If no statements are available.
    """
    response = await api_methods.list_statements(per_page=10)
    if "errors" in response:
        pytest.skip(f"Cannot retrieve statements: {response['errors']}")
    
    statements_list = response.get("statements", [])
    if not statements_list:
        pytest.skip("No statements available for testing")
    return statements_list


@pytest_asyncio.fixture(scope="session")
async def statement_id(statements: List[Dict[str, Any]]) -> str:
    """Get the first statement ID for testing.
    
    Args:
        statements: Statements fixture.
        
    Returns:
        str: Statement ID.
    """
    return statements[0]["id"]


@pytest_asyncio.fixture(scope="session")
async def business_accounts(api_methods: APIMethods) -> List[Dict[str, Any]]:
    """Fetch business accounts for testing.
    
    Args:
        api_methods: API methods fixture.
        
    Returns:
        List[Dict[str, Any]]: List of business account objects.
        
    Raises:
        pytest.skip: If no business accounts are available.
    """
    response = await api_methods.list_business_accounts(per_page=10)
    if "errors" in response:
        pytest.skip(f"Cannot retrieve business accounts: {response['errors']}")
    
    accounts_list = response.get("bank_accounts", [])
    if not accounts_list:
        pytest.skip("No business accounts available for testing")
    return accounts_list


@pytest_asyncio.fixture(scope="session")
async def business_account_id(business_accounts: List[Dict[str, Any]]) -> str:
    """Get the first business account ID for testing.
    
    Args:
        business_accounts: Business accounts fixture.
        
    Returns:
        str: Business account ID.
    """
    return business_accounts[0]["id"]


@pytest.fixture
def test_file_path() -> str:
    """Provide a test file path for upload operations.
    
    Note: This is a placeholder path that will need to be replaced
    with actual file paths during testing.
    
    Returns:
        str: Test file path.
    """
    return "/tmp/test_file.pdf"
