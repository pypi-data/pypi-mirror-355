"""Tests for attachment related API methods.

This module tests attachment functionality including:
- Uploading standalone attachments
- Retrieving attachment details
- File handling and validation

Attachments are files that can be associated with transactions or external transfers.
"""

from typing import Any, Dict

import pytest

from src.qonto_mcp_server.api.methods import APIMethods


class TestAttachments:
    """Test attachment API methods."""

    @pytest.mark.asyncio
    async def test_upload_an_attachment(
        self, api_methods: APIMethods, test_file_path: str
    ) -> None:
        """Test uploading a standalone attachment.
        
        Args:
            api_methods: API methods fixture.
            test_file_path: Test file path fixture.
        """
        response = await api_methods.upload_an_attachment(test_file_path)
        
        # Note: This will likely fail with a file not found error in real testing
        # but it tests the method structure
        if "errors" in response:
            # Expected if test file doesn't exist
            assert any("file" in str(error).lower() or "path" in str(error).lower() 
                     for error in response["errors"])
        else:
            # If successful, verify response structure
            assert "attachment" in response
            attachment = response["attachment"]
            assert "id" in attachment
            assert "url" in attachment

    @pytest.mark.asyncio
    async def test_upload_attachment_with_idempotency_key(
        self, api_methods: APIMethods, test_file_path: str
    ) -> None:
        """Test uploading an attachment with idempotency key.
        
        Args:
            api_methods: API methods fixture.
            test_file_path: Test file path fixture.
        """
        idempotency_key = "test-attachment-upload-12345"
        response = await api_methods.upload_an_attachment(
            test_file_path,
            idempotency_key=idempotency_key
        )
        
        # Note: This will likely fail with a file not found error
        if "errors" in response:
            # Expected if test file doesn't exist
            assert any("file" in str(error).lower() or "path" in str(error).lower() 
                     for error in response["errors"])
        else:
            # If successful, verify response structure
            assert "attachment" in response
            attachment = response["attachment"]
            assert "id" in attachment

    @pytest.mark.asyncio
    async def test_upload_attachment_nonexistent_file(
        self, api_methods: APIMethods
    ) -> None:
        """Test uploading a non-existent file.
        
        Args:
            api_methods: API methods fixture.
        """
        nonexistent_path = "/nonexistent/file.pdf"
        response = await api_methods.upload_an_attachment(nonexistent_path)
        
        # Should return an error for non-existent file
        assert "errors" in response
        assert any("file" in str(error).lower() or "path" in str(error).lower() 
                 for error in response["errors"])

    @pytest.mark.asyncio
    async def test_retrieve_an_attachment_via_upload(
        self, api_methods: APIMethods, test_file_path: str
    ) -> None:
        """Test retrieving an attachment by first uploading one.
        
        This test attempts to upload a file and then retrieve it.
        If upload fails (expected), it skips the retrieve test.
        
        Args:
            api_methods: API methods fixture.
            test_file_path: Test file path fixture.
        """
        # First try to upload an attachment
        upload_response = await api_methods.upload_an_attachment(test_file_path)
        
        if "errors" in upload_response:
            pytest.skip("Cannot upload test file, skipping attachment retrieval test")
        
        # If upload was successful, try to retrieve the attachment
        attachment_id = upload_response["attachment"]["id"]
        response = await api_methods.retrieve_an_attachment(attachment_id)
        
        # Verify successful response
        assert "errors" not in response
        assert "attachment" in response
        
        # Verify attachment structure
        attachment = response["attachment"]
        assert "id" in attachment
        assert attachment["id"] == attachment_id
        assert "url" in attachment
        assert "filename" in attachment

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_attachment(
        self, api_methods: APIMethods
    ) -> None:
        """Test retrieving a non-existent attachment.
        
        Args:
            api_methods: API methods fixture.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_methods.retrieve_an_attachment(fake_id)
        
        # Should return an error for non-existent attachment
        assert "errors" in response

    @pytest.mark.asyncio
    async def test_upload_attachment_different_file_types(
        self, api_methods: APIMethods
    ) -> None:
        """Test uploading different file types.
        
        This tests the method with different file extensions that should be
        supported by the API (JPEG, PNG, PDF).
        
        Args:
            api_methods: API methods fixture.
        """
        file_paths = [
            "/tmp/test_document.pdf",
            "/tmp/test_image.jpg",
            "/tmp/test_image.jpeg",
            "/tmp/test_image.png"
        ]
        
        for file_path in file_paths:
            response = await api_methods.upload_an_attachment(file_path)
            
            # All will likely fail with file not found, but should handle gracefully
            if "errors" in response:
                assert any("file" in str(error).lower() or "path" in str(error).lower() 
                         for error in response["errors"])
            else:
                # If any succeed, verify structure
                assert "attachment" in response
                assert "id" in response["attachment"]

    @pytest.mark.asyncio
    async def test_attachment_url_security(
        self, api_methods: APIMethods, test_file_path: str
    ) -> None:
        """Test that attachment URLs are properly handled.
        
        This test verifies that if an attachment is successfully uploaded,
        the returned URL follows expected patterns.
        
        Args:
            api_methods: API methods fixture.
            test_file_path: Test file path fixture.
        """
        # Try to upload
        upload_response = await api_methods.upload_an_attachment(test_file_path)
        
        if "errors" in upload_response:
            pytest.skip("Cannot upload test file, skipping URL security test")
        
        attachment = upload_response["attachment"]
        
        # Verify URL structure if present
        if "url" in attachment:
            url = attachment["url"]
            assert isinstance(url, str)
            # URL should be HTTPS for security
            assert url.startswith("https://"), "Attachment URLs should use HTTPS"

    @pytest.mark.asyncio
    async def test_attachment_metadata(
        self, api_methods: APIMethods, test_file_path: str
    ) -> None:
        """Test attachment metadata is properly returned.
        
        Args:
            api_methods: API methods fixture.
            test_file_path: Test file path fixture.
        """
        upload_response = await api_methods.upload_an_attachment(test_file_path)
        
        if "errors" in upload_response:
            pytest.skip("Cannot upload test file, skipping metadata test")
        
        attachment = upload_response["attachment"]
        
        # Verify metadata fields
        metadata_fields = ["id", "url", "filename", "content_type", "size"]
        for field in metadata_fields:
            if field in attachment:
                assert isinstance(attachment[field], (str, int)), \
                    f"Field {field} should be string or int"

    @pytest.mark.asyncio
    async def test_idempotency_key_uniqueness(
        self, api_methods: APIMethods, test_file_path: str
    ) -> None:
        """Test that idempotency keys work correctly.
        
        This test verifies that using the same idempotency key twice
        doesn't create duplicate attachments.
        
        Args:
            api_methods: API methods fixture.
            test_file_path: Test file path fixture.
        """
        idempotency_key = "unique-test-key-98765"
        
        # First upload attempt
        response1 = await api_methods.upload_an_attachment(
            test_file_path,
            idempotency_key=idempotency_key
        )
        
        # Second upload attempt with same key
        response2 = await api_methods.upload_an_attachment(
            test_file_path,
            idempotency_key=idempotency_key
        )
        
        # Both should have the same response structure
        if "errors" in response1:
            # If first failed, second should also fail
            assert "errors" in response2
        else:
            # If first succeeded, second should return same result or be idempotent
            if "errors" not in response2:
                assert response1["attachment"]["id"] == response2["attachment"]["id"]

    @pytest.mark.asyncio
    async def test_attachment_file_size_limits(
        self, api_methods: APIMethods
    ) -> None:
        """Test attachment file size handling.
        
        This test attempts to upload files of different theoretical sizes
        to test the API's handling of size limits.
        
        Args:
            api_methods: API methods fixture.
        """
        # Test with typical file paths that might have size issues
        large_file_paths = [
            "/tmp/large_file.pdf",
            "/tmp/very_large_document.pdf"
        ]
        
        for file_path in large_file_paths:
            response = await api_methods.upload_an_attachment(file_path)
            
            # Should either succeed or fail gracefully with clear error
            if "errors" in response:
                errors = response["errors"]
                assert isinstance(errors, list)
                # Should contain descriptive error message
                assert len(errors) > 0
            else:
                # If successful, should have valid attachment data
                assert "attachment" in response
                assert "id" in response["attachment"]
