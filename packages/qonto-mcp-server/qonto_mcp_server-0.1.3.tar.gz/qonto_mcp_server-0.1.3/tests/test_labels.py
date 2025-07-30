"""Tests for label related API methods.

This module tests label functionality including:
- Listing labels with pagination
- Retrieving individual labels
- Label structure validation

Labels are used to categorize and organize transactions and other entities.
"""

from typing import Any, Dict, List

import pytest

from src.qonto_mcp_server.api.methods import APIMethods


class TestLabels:
    """Test label API methods."""

    @pytest.mark.asyncio
    async def test_list_labels_basic(self, api_methods: APIMethods) -> None:
        """Test basic labels listing.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_labels()
        
        # Verify successful response
        assert "errors" not in response
        assert "labels" in response
        assert isinstance(response["labels"], list)

    @pytest.mark.asyncio
    async def test_list_labels_with_pagination(self, api_methods: APIMethods) -> None:
        """Test labels listing with pagination.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_labels(page="1", per_page="5")
        
        assert "errors" not in response
        assert "labels" in response
        labels_list = response["labels"]
        assert isinstance(labels_list, list)
        assert len(labels_list) <= 5

    @pytest.mark.asyncio
    async def test_list_labels_pagination_metadata(
        self, api_methods: APIMethods
    ) -> None:
        """Test that pagination metadata is included when available.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_labels(page="1", per_page="3")
        
        assert "errors" not in response
        assert "labels" in response
        
        # Check for pagination metadata if present
        if "meta" in response:
            meta = response["meta"]
            if "total_pages" in meta:
                assert isinstance(meta["total_pages"], int)
                assert meta["total_pages"] >= 0
            if "current_page" in meta:
                assert isinstance(meta["current_page"], int)
                assert meta["current_page"] >= 1
            if "total_count" in meta:
                assert isinstance(meta["total_count"], int)
                assert meta["total_count"] >= 0

    @pytest.mark.asyncio
    async def test_retrieve_a_label(
        self, api_methods: APIMethods, label_id: str
    ) -> None:
        """Test retrieving a specific label.
        
        Args:
            api_methods: API methods fixture.
            label_id: Label ID fixture.
        """
        response = await api_methods.retrieve_a_label(label_id)
        
        # Verify successful response
        assert "errors" not in response
        assert "label" in response
        
        # Verify label structure
        label = response["label"]
        assert "id" in label
        assert label["id"] == label_id

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_label(self, api_methods: APIMethods) -> None:
        """Test retrieving a non-existent label.
        
        Args:
            api_methods: API methods fixture.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_methods.retrieve_a_label(fake_id)
        
        # Should return an error for non-existent label
        assert "errors" in response

    @pytest.mark.asyncio
    async def test_labels_structure(self, labels: List[Dict[str, Any]]) -> None:
        """Test that labels have proper structure.
        
        Args:
            labels: Labels fixture.
        """
        for label in labels:
            # Required fields
            assert "id" in label
            assert isinstance(label["id"], str)
            
            # Common fields that should be present
            if "name" in label:
                assert isinstance(label["name"], str)
                assert len(label["name"]) > 0  # Name should not be empty
            
            if "color" in label:
                assert isinstance(label["color"], str)
                # Color should be a valid format (hex color or named color)
                color = label["color"]
                if color.startswith("#"):
                    # Hex color format
                    assert len(color) in [4, 7]  # #RGB or #RRGGBB
                    assert all(c in "0123456789ABCDEFabcdef" for c in color[1:])
                else:
                    # Named color should be non-empty string
                    assert len(color) > 0
            
            if "created_at" in label:
                assert isinstance(label["created_at"], str)
            
            if "updated_at" in label:
                assert isinstance(label["updated_at"], str)

    @pytest.mark.asyncio
    async def test_label_detailed_retrieve(
        self, api_methods: APIMethods, label_id: str
    ) -> None:
        """Test detailed retrieval of label with all available fields.
        
        Args:
            api_methods: API methods fixture.
            label_id: Label ID fixture.
        """
        response = await api_methods.retrieve_a_label(label_id)
        
        assert "errors" not in response
        label = response["label"]
        
        # Verify detailed fields are present and have correct types
        field_type_mapping = {
            "id": str,
            "name": str,
            "color": str,
            "created_at": str,
            "updated_at": str,
        }
        
        for field, expected_type in field_type_mapping.items():
            if field in label:
                assert isinstance(label[field], expected_type), \
                    f"Field {field} should be {expected_type}, got {type(label[field])}"

    @pytest.mark.asyncio
    async def test_list_labels_empty_organization(self, api_methods: APIMethods) -> None:
        """Test listing labels when organization might have no labels.
        
        This test ensures the API handles empty label lists gracefully.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_labels(per_page="100")
        
        assert "errors" not in response
        assert "labels" in response
        labels_list = response["labels"]
        assert isinstance(labels_list, list)
        # List can be empty, that's valid

    @pytest.mark.asyncio
    async def test_list_labels_large_page_size(self, api_methods: APIMethods) -> None:
        """Test listing labels with a large page size.
        
        Args:
            api_methods: API methods fixture.
        """
        response = await api_methods.list_labels(per_page="50")
        
        assert "errors" not in response
        assert "labels" in response
        labels_list = response["labels"]
        assert isinstance(labels_list, list)
        assert len(labels_list) <= 50

    @pytest.mark.asyncio
    async def test_list_labels_pagination_consistency(
        self, api_methods: APIMethods
    ) -> None:
        """Test that pagination works consistently across pages.
        
        Args:
            api_methods: API methods fixture.
        """
        # Get first page
        page1_response = await api_methods.list_labels(page="1", per_page="2")
        assert "errors" not in page1_response
        page1_labels = page1_response["labels"]
        
        # Get second page
        page2_response = await api_methods.list_labels(page="2", per_page="2")
        assert "errors" not in page2_response
        page2_labels = page2_response["labels"]
        
        # If both pages have labels, they should be different
        if page1_labels and page2_labels:
            page1_ids = {label["id"] for label in page1_labels}
            page2_ids = {label["id"] for label in page2_labels}
            # No overlap between pages
            assert len(page1_ids.intersection(page2_ids)) == 0

    @pytest.mark.asyncio
    async def test_label_name_validation(self, labels: List[Dict[str, Any]]) -> None:
        """Test that label names follow expected patterns.
        
        Args:
            labels: Labels fixture.
        """
        for label in labels:
            if "name" in label:
                name = label["name"]
                assert isinstance(name, str)
                assert len(name.strip()) > 0  # Should not be just whitespace
                assert len(name) <= 255  # Reasonable length limit

    @pytest.mark.asyncio
    async def test_label_color_formats(self, labels: List[Dict[str, Any]]) -> None:
        """Test that label colors follow valid formats.
        
        Args:
            labels: Labels fixture.
        """
        valid_hex_chars = set("0123456789ABCDEFabcdef")
        
        for label in labels:
            if "color" in label and label["color"]:
                color = label["color"]
                assert isinstance(color, str)
                
                if color.startswith("#"):
                    # Hex color validation
                    hex_part = color[1:]
                    assert len(hex_part) in [3, 6]  # RGB or RRGGBB
                    assert all(c in valid_hex_chars for c in hex_part)
                else:
                    # Named color should be non-empty
                    assert len(color.strip()) > 0

    @pytest.mark.asyncio
    async def test_labels_uniqueness(self, labels: List[Dict[str, Any]]) -> None:
        """Test that labels have unique IDs.
        
        Args:
            labels: Labels fixture.
        """
        if len(labels) > 1:
            label_ids = [label["id"] for label in labels]
            unique_ids = set(label_ids)
            assert len(label_ids) == len(unique_ids), "Label IDs should be unique"
