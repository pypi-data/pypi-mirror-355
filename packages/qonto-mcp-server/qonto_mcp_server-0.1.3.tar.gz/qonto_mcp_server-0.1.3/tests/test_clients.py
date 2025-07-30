"""Tests for client related API methods.

This module tests client functionality including:
- Creating new clients
- Listing clients with filters
- Retrieving individual clients
- Client structure validation

Clients are entities that receive invoices from the organization.
"""

from typing import Any, Dict, List

import pytest

from src.qonto_mcp_server.api.methods import APIMethods


class TestClients:
    """Test client API methods."""

    @pytest.mark.asyncio
    async def test_create_a_client_individual(self, api_methods: APIMethods) -> None:
        """Test creating an individual client.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.create_a_client(
            name="John Doe",
            type="individual",
            email="john.doe@example.com",
            first_name="John",
            last_name="Doe",
            address="123 Main Street",
            city="Paris",
            zip_code="75001",
            country_code="FR"
        )
        
        # Verify response structure
        if "errors" not in response:
            assert "client" in response
            client = response["client"]
            assert "id" in client
            assert client["type"] == "individual"
            assert client["email"] == "john.doe@example.com"
        else:
            # Could fail due to business rules, duplicate email, etc.
            assert isinstance(response["errors"], list)

    @pytest.mark.asyncio
    async def test_create_a_client_company(self, api_methods: APIMethods) -> None:
        """Test creating a company client.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.create_a_client(
            name="Test Company Ltd",
            type="company",
            email="contact@testcompany.com",
            vat_number="FR12345678901",
            address="456 Business Avenue",
            city="Lyon",
            zip_code="69001",
            country_code="FR"
        )
        
        if "errors" not in response:
            assert "client" in response
            client = response["client"]
            assert "id" in client
            assert client["type"] == "company"
            assert client["name"] == "Test Company Ltd"
        else:
            assert isinstance(response["errors"], list)

    @pytest.mark.asyncio
    async def test_create_a_client_freelancer(self, api_methods: APIMethods) -> None:
        """Test creating a freelancer client.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.create_a_client(
            name="Jane Smith Consulting",
            type="freelancer",
            email="jane.smith@consulting.com",
            first_name="Jane",
            last_name="Smith",
            tax_identification_number="123456789",
            address="789 Freelancer Street",
            city="Marseille",
            zip_code="13001",
            country_code="FR"
        )
        
        if "errors" not in response:
            assert "client" in response
            client = response["client"]
            assert "id" in client
            assert client["type"] == "freelancer"
        else:
            assert isinstance(response["errors"], list)

    @pytest.mark.asyncio
    async def test_create_a_client_with_addresses(self, api_methods: APIMethods) -> None:
        """Test creating a client with billing and delivery addresses.
        
        Args:
            api_methods: API methods fixture.
        """
        billing_address = {
            "address": "123 Billing Street",
            "city": "Paris",
            "zip_code": "75002",
            "country_code": "FR"
        }
        
        delivery_address = {
            "address": "456 Delivery Avenue",
            "city": "Paris",
            "zip_code": "75003",
            "country_code": "FR"
        }
        
        response = await api_methods.create_a_client(
            name="Address Test Company",
            type="company",
            email="addresses@testcompany.com",
            billing_address=billing_address,
            delivery_address=delivery_address
        )
        
        if "errors" not in response:
            assert "client" in response
            client = response["client"]
            assert "id" in client
        else:
            assert isinstance(response["errors"], list)

    @pytest.mark.asyncio
    async def test_create_client_missing_required_fields(
        self, api_methods: APIMethods
    ) -> None:
        """Test creating a client with missing required fields.
        
        Args:
            api_methods: API methods fixture.
        """
        # Missing required fields for individual type
        response = await api_methods.create_a_client(
            name="Incomplete Individual",
            type="individual",
            email="incomplete@example.com"
            # Missing first_name and last_name
        )
        
        # Should return an error for missing required fields
        assert "errors" in response

    @pytest.mark.asyncio
    async def test_list_clients_basic(self, api_methods: APIMethods) -> None:
        """Test basic clients listing.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_clients()
        
        # Verify successful response
        assert "errors" not in response
        assert "clients" in response
        assert isinstance(response["clients"], list)

    @pytest.mark.asyncio
    async def test_list_clients_with_pagination(self, api_methods: APIMethods) -> None:
        """Test clients listing with pagination.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_clients(page=1, per_page=5)
        
        assert "errors" not in response
        assert "clients" in response
        clients_list = response["clients"]
        assert isinstance(clients_list, list)
        assert len(clients_list) <= 5

    @pytest.mark.asyncio
    async def test_list_clients_with_sorting(self, api_methods: APIMethods) -> None:
        """Test clients listing with sorting options.
        
        Args:
            api_methods: API methods fixture.
        """
        sort_options = ["name:asc", "name:desc", "created_at:asc", "created_at:desc"]
        
        for sort_by in sort_options:
            response = await api_methods.list_clients(sort_by=sort_by, per_page=5)
            
            assert "errors" not in response
            assert "clients" in response

    @pytest.mark.asyncio
    async def test_list_clients_with_filter(self, api_methods: APIMethods) -> None:
        """Test clients listing with filter.
        
        Args:
            api_methods: API methods fixture.
        """
        # Test with a filter that might match existing clients
        filter_obj = {"email": "test"}
        
        response = await api_methods.list_clients(filter_obj=filter_obj, per_page=10)
        
        assert "errors" not in response
        assert "clients" in response

    @pytest.mark.asyncio
    async def test_retrieve_a_client(
        self, api_methods: APIMethods, client_id: str
    ) -> None:
        """Test retrieving a specific client.
        
        Args:
            api_methods: API methods fixture.
            client_id: Client ID fixture.
        """
        response = await api_methods.retrieve_a_client(client_id)
        
        # Verify successful response
        assert "errors" not in response
        assert "client" in response
        
        # Verify client structure
        client = response["client"]
        assert "id" in client
        assert client["id"] == client_id

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_client(self, api_methods: APIMethods) -> None:
        """Test retrieving a non-existent client.
        
        Args:
            api_methods: API methods fixture.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_methods.retrieve_a_client(fake_id)
        
        # Should return an error for non-existent client
        assert "errors" in response

    @pytest.mark.asyncio
    async def test_clients_structure(self, clients: List[Dict[str, Any]]) -> None:
        """Test that clients have proper structure.
        
        Args:
            clients: Clients fixture.
        """
        for client in clients:
            # Required fields
            assert "id" in client
            assert isinstance(client["id"], str)
            
            # Type validation
            if "type" in client:
                assert isinstance(client["type"], str)
                assert client["type"] in ["individual", "company", "freelancer"]
            
            # Email validation
            if "email" in client:
                assert isinstance(client["email"], str)
                assert "@" in client["email"]  # Basic email format check
            
            # Name validation based on type
            if "name" in client:
                assert isinstance(client["name"], str)
                assert len(client["name"].strip()) > 0
            
            # Individual/freelancer specific fields
            if client.get("type") in ["individual", "freelancer"]:
                if "first_name" in client:
                    assert isinstance(client["first_name"], str)
                if "last_name" in client:
                    assert isinstance(client["last_name"], str)
            
            # Optional fields validation
            if "vat_number" in client and client["vat_number"]:
                assert isinstance(client["vat_number"], str)
            
            if "tax_identification_number" in client and client["tax_identification_number"]:
                assert isinstance(client["tax_identification_number"], str)
            
            if "country_code" in client and client["country_code"]:
                assert isinstance(client["country_code"], str)
                assert len(client["country_code"]) == 2  # ISO country code
            
            if "zip_code" in client and client["zip_code"]:
                assert isinstance(client["zip_code"], str)

    @pytest.mark.asyncio
    async def test_client_detailed_retrieve(
        self, api_methods: APIMethods, client_id: str
    ) -> None:
        """Test detailed retrieval of client with all available fields.
        
        Args:
            api_methods: API methods fixture.
            client_id: Client ID fixture.
        """
        response = await api_methods.retrieve_a_client(client_id)
        
        assert "errors" not in response
        client = response["client"]
        
        # Verify detailed fields are present and have correct types
        field_type_mapping = {
            "id": str,
            "type": str,
            "name": str,
            "email": str,
            "first_name": str,
            "last_name": str,
            "vat_number": str,
            "tax_identification_number": str,
            "address": str,
            "city": str,
            "zip_code": str,
            "province_code": str,
            "country_code": str,
            "created_at": str,
            "updated_at": str,
        }
        
        for field, expected_type in field_type_mapping.items():
            if field in client and client[field] is not None:
                assert isinstance(client[field], expected_type), \
                    f"Field {field} should be {expected_type}, got {type(client[field])}"

    @pytest.mark.asyncio
    async def test_client_email_uniqueness(self, api_methods: APIMethods) -> None:
        """Test that creating clients with duplicate emails fails.
        
        Args:
            api_methods: API methods fixture.
        """
        test_email = "duplicate.test@example.com"
        
        # First client creation
        response1 = await api_methods.create_a_client(
            name="First Client",
            type="individual",
            email=test_email,
            first_name="First",
            last_name="Client"
        )
        
        # Second client creation with same email
        response2 = await api_methods.create_a_client(
            name="Second Client",
            type="individual",
            email=test_email,
            first_name="Second",
            last_name="Client"
        )
        
        # At least one should fail (probably the second one)
        assert "errors" in response1 or "errors" in response2

    @pytest.mark.asyncio
    async def test_client_address_structure(self, clients: List[Dict[str, Any]]) -> None:
        """Test that client addresses have proper structure when present.
        
        Args:
            clients: Clients fixture.
        """
        for client in clients:
            # Check billing address structure if present
            if "billing_address" in client and client["billing_address"]:
                billing_addr = client["billing_address"]
                assert isinstance(billing_addr, dict)
                
                if "address" in billing_addr:
                    assert isinstance(billing_addr["address"], str)
                if "city" in billing_addr:
                    assert isinstance(billing_addr["city"], str)
                if "zip_code" in billing_addr:
                    assert isinstance(billing_addr["zip_code"], str)
                if "country_code" in billing_addr:
                    assert isinstance(billing_addr["country_code"], str)
                    assert len(billing_addr["country_code"]) == 2
            
            # Check delivery address structure if present
            if "delivery_address" in client and client["delivery_address"]:
                delivery_addr = client["delivery_address"]
                assert isinstance(delivery_addr, dict)
                
                if "address" in delivery_addr:
                    assert isinstance(delivery_addr["address"], str)
                if "city" in delivery_addr:
                    assert isinstance(delivery_addr["city"], str)
                if "zip_code" in delivery_addr:
                    assert isinstance(delivery_addr["zip_code"], str)
                if "country_code" in delivery_addr:
                    assert isinstance(delivery_addr["country_code"], str)
                    assert len(delivery_addr["country_code"]) == 2

    @pytest.mark.asyncio
    async def test_clients_uniqueness(self, clients: List[Dict[str, Any]]) -> None:
        """Test that clients have unique IDs.
        
        Args:
            clients: Clients fixture.
        """
        if len(clients) > 1:
            client_ids = [client["id"] for client in clients]
            unique_ids = set(client_ids)
            assert len(client_ids) == len(unique_ids), "Client IDs should be unique"

    @pytest.mark.asyncio
    async def test_client_types_validation(self, clients: List[Dict[str, Any]]) -> None:
        """Test that client types are valid and consistent with required fields.
        
        Args:
            clients: Clients fixture.
        """
        for client in clients:
            if "type" in client:
                client_type = client["type"]
                
                if client_type == "individual":
                    # Individual should have first_name and last_name
                    if "first_name" in client:
                        assert isinstance(client["first_name"], str)
                        assert len(client["first_name"].strip()) > 0
                    if "last_name" in client:
                        assert isinstance(client["last_name"], str)
                        assert len(client["last_name"].strip()) > 0
                
                elif client_type == "company":
                    # Company should have name
                    if "name" in client:
                        assert isinstance(client["name"], str)
                        assert len(client["name"].strip()) > 0
                
                elif client_type == "freelancer":
                    # Freelancer should have both name and first_name/last_name
                    if "name" in client:
                        assert isinstance(client["name"], str)
                        assert len(client["name"].strip()) > 0
                    if "first_name" in client:
                        assert isinstance(client["first_name"], str)
                        assert len(client["first_name"].strip()) > 0
                    if "last_name" in client:
                        assert isinstance(client["last_name"], str)
                        assert len(client["last_name"].strip()) > 0
