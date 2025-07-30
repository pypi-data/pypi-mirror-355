import base64
import gzip
import json
from unittest.mock import patch

import pandas as pd
import pytest
from IPython.display import HTML

from grafiki import GrafikiBridge, bridge_df, show_bridge_link


class TestGrafikiBridge:
    """Test suite for GrafikiBridge class."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "A": [1, 2, 3, 4, 5],
                "B": ["a", "b", "c", "d", "e"],
                "C": [1.1, 2.2, 3.3, 4.4, 5.5],
                "D": [True, False, True, False, True],
            }
        )

    @pytest.fixture
    def empty_dataframe(self):
        """Create an empty DataFrame for testing."""
        return pd.DataFrame()

    @pytest.fixture
    def large_dataframe(self):
        """Create a large DataFrame for testing URL limits."""
        data = {f"col_{i}": list(range(1000)) for i in range(50)}
        return pd.DataFrame(data)

    @pytest.fixture
    def bridge_instance(self):
        """Create a GrafikiBridge instance for testing."""
        return GrafikiBridge()

    @pytest.fixture
    def custom_bridge_instance(self):
        """Create a GrafikiBridge instance with custom base URL."""
        return GrafikiBridge(base_url="https://custom.example.com/")

    def test_init_default_url(self):
        """Test GrafikiBridge initialization with default URL."""
        bridge = GrafikiBridge()
        assert bridge.base_url == "https://www.grafiki.app"

    def test_init_custom_url(self):
        """Test GrafikiBridge initialization with custom URL."""
        custom_url = "https://custom.example.com/"
        bridge = GrafikiBridge(base_url=custom_url)
        assert bridge.base_url == "https://custom.example.com"

    def test_init_url_trailing_slash_removal(self):
        """Test that trailing slashes are removed from base URL."""
        bridge = GrafikiBridge(base_url="https://example.com///")
        assert bridge.base_url == "https://example.com"

    def test_compress_dataframe_basic(self, sample_dataframe):
        """Test basic DataFrame compression functionality."""
        compressed = GrafikiBridge.compress_dataframe(sample_dataframe)

        # Should return a string
        assert isinstance(compressed, str)

        # Should be base64 encoded (only contains valid base64 characters)
        try:
            base64.b64decode(compressed)
        except Exception:
            pytest.fail("Compressed data is not valid base64")

    def test_compress_dataframe_with_name_and_tags(self, sample_dataframe):
        """Test DataFrame compression with custom name and tags."""
        name = "TestDataset"
        tags = ["test", "sample", "data"]

        compressed = GrafikiBridge.compress_dataframe(
            sample_dataframe, name=name, tags=tags
        )

        # Decompress and verify content
        decoded = base64.b64decode(compressed)
        decompressed = gzip.decompress(decoded)
        data = json.loads(decompressed.decode("utf-8"))

        assert data["dataset"]["name"] == name
        assert data["dataset"]["tags"] == tags
        assert len(data["dataset"]["data"]) == len(sample_dataframe)

    def test_compress_dataframe_auto_name(self, sample_dataframe):
        """Test DataFrame compression with auto-generated name."""
        with patch("grafiki.core.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20231215_143022"

            compressed = GrafikiBridge.compress_dataframe(sample_dataframe)

            # Decompress and verify auto-generated name
            decoded = base64.b64decode(compressed)
            decompressed = gzip.decompress(decoded)
            data = json.loads(decompressed.decode("utf-8"))

            assert data["dataset"]["name"] == "Dataset_20231215_143022"

    def test_compress_dataframe_empty(self, empty_dataframe):
        """Test compression of empty DataFrame."""
        compressed = GrafikiBridge.compress_dataframe(empty_dataframe)

        # Should still work with empty DataFrame
        assert isinstance(compressed, str)

        # Verify content
        decoded = base64.b64decode(compressed)
        decompressed = gzip.decompress(decoded)
        data = json.loads(decompressed.decode("utf-8"))

        assert data["dataset"]["data"] == []

    def test_create_webapp_link_basic(self, bridge_instance, sample_dataframe):
        """Test basic webapp link creation."""
        link = bridge_instance.create_webapp_link(sample_dataframe)

        assert link.startswith("https://www.grafiki.app/d#")
        assert len(link) > len("https://www.grafiki.app/d#")

    def test_create_webapp_link_custom_params(self, bridge_instance, sample_dataframe):
        """Test webapp link creation with custom parameters."""
        name = "CustomDataset"
        tags = ["custom", "test"]

        link = bridge_instance.create_webapp_link(
            sample_dataframe, name=name, tags=tags
        )

        # Extract and verify compressed data
        compressed_data = link.split("#")[1]
        decoded = base64.b64decode(compressed_data)
        decompressed = gzip.decompress(decoded)
        data = json.loads(decompressed.decode("utf-8"))

        assert data["dataset"]["name"] == name
        assert data["dataset"]["tags"] == tags

    def test_create_webapp_link_custom_base_url(
        self, custom_bridge_instance, sample_dataframe
    ):
        """Test webapp link creation with custom base URL."""
        link = custom_bridge_instance.create_webapp_link(sample_dataframe)
        assert link.startswith("https://custom.example.com/d#")

    def test_get_compression_stats(self, bridge_instance, sample_dataframe):
        """Test compression statistics calculation."""
        stats = bridge_instance._get_compression_stats(sample_dataframe)

        assert "compression_ratio" in stats
        assert "space_saved_percent" in stats
        assert isinstance(stats["compression_ratio"], (int, float))
        assert isinstance(stats["space_saved_percent"], (int, float))
        assert stats["compression_ratio"] > 0
        assert -100 <= stats["space_saved_percent"] <= 100

    def test_get_compression_stats_empty_dataframe(
        self, bridge_instance, empty_dataframe
    ):
        """Test compression statistics with empty DataFrame."""
        stats = bridge_instance._get_compression_stats(empty_dataframe)

        # Should handle empty DataFrame gracefully
        assert "compression_ratio" in stats
        assert "space_saved_percent" in stats

    def test_check_url_compatibility_short_url(self, bridge_instance):
        """Test URL compatibility check with short URL."""
        short_url = "https://example.com/short"

        compatibility = bridge_instance._check_url_compatibility(short_url)

        assert "url_length" in compatibility
        assert "compatible_browsers" in compatibility
        assert "has_compatibility_issues" in compatibility

        assert compatibility["url_length"] == len(short_url)
        assert (
            len(compatibility["compatible_browsers"]) >= 3
        )  # Should be compatible with most browsers
        assert not compatibility["has_compatibility_issues"]

    def test_check_url_compatibility_long_url(self, bridge_instance):
        """Test URL compatibility check with very long URL."""
        # Create a URL longer than safari limit (80000)
        long_url = "https://example.com/" + "x" * 90000

        compatibility = bridge_instance._check_url_compatibility(long_url)

        assert compatibility["url_length"] == len(long_url)
        assert (
            len(compatibility["compatible_browsers"]) < 4
        )  # Should have limited compatibility
        assert compatibility["has_compatibility_issues"]

    def test_browser_limits_constant(self):
        """Test that browser limits are properly defined."""
        limits = GrafikiBridge.BROWSER_LIMITS

        expected_browsers = ["chrome", "firefox", "safari", "edge", "default"]
        for browser in expected_browsers:
            assert browser in limits
            assert isinstance(limits[browser], int)
            assert limits[browser] > 0

    @patch("grafiki.core.display")
    def test_display_link_basic(self, mock_display, bridge_instance, sample_dataframe):
        """Test basic display link functionality."""
        bridge_instance.display_link(sample_dataframe)

        # Verify display was called
        mock_display.assert_called_once()

        # Verify HTML object was passed
        call_args = mock_display.call_args[0]
        assert len(call_args) == 1
        assert isinstance(call_args[0], HTML)

    @patch("grafiki.core.display")
    def test_display_link_with_params(
        self, mock_display, bridge_instance, sample_dataframe
    ):
        """Test display link with custom parameters."""
        name = "TestDisplay"
        tags = ["display", "test"]
        link_text = "Custom Link Text"

        bridge_instance.display_link(
            sample_dataframe, name=name, tags=tags, link_text=link_text
        )

        mock_display.assert_called_once()

        # Verify HTML content contains custom elements
        html_content = mock_display.call_args[0][0].data
        assert name in html_content
        assert link_text in html_content

    @patch("grafiki.core.display")
    def test_display_link_compatibility_warning(
        self, mock_display, bridge_instance, large_dataframe
    ):
        """Test display link shows compatibility warnings for large DataFrames."""
        bridge_instance.display_link(large_dataframe)

        mock_display.assert_called_once()
        html_content = mock_display.call_args[0][0].data

        # Should contain compatibility information
        assert any(
            word in html_content.lower()
            for word in ["compatibility", "warning", "status"]
        )


class TestConvenienceFunctions:
    """Test suite for convenience functions."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({"X": [1, 2, 3], "Y": ["a", "b", "c"]})

    def test_bridge_df_basic(self, sample_dataframe):
        """Test basic bridge_df functionality."""
        url = bridge_df(sample_dataframe)

        assert isinstance(url, str)
        assert url.startswith("https://www.grafiki.app/d#")

    def test_bridge_df_with_params(self, sample_dataframe):
        """Test bridge_df with custom parameters."""
        name = "ConvenienceTest"
        tags = ["convenience", "test"]
        base_url = "https://custom.test.com"

        url = bridge_df(sample_dataframe, name=name, tags=tags, base_url=base_url)

        assert url.startswith(f"{base_url}/d#")

        # Verify parameters are included
        compressed_data = url.split("#")[1]
        decoded = base64.b64decode(compressed_data)
        decompressed = gzip.decompress(decoded)
        data = json.loads(decompressed.decode("utf-8"))

        assert data["dataset"]["name"] == name
        assert data["dataset"]["tags"] == tags

    @patch("grafiki.core.display")
    def test_show_bridge_link_basic(self, mock_display, sample_dataframe):
        """Test basic show_bridge_link functionality."""
        show_bridge_link(sample_dataframe)

        mock_display.assert_called_once()
        assert isinstance(mock_display.call_args[0][0], HTML)

    @patch("grafiki.core.display")
    def test_show_bridge_link_with_params(self, mock_display, sample_dataframe):
        """Test show_bridge_link with custom parameters."""
        name = "ShowLinkTest"
        tags = ["show", "link", "test"]
        base_url = "https://show.test.com"
        link_text = "Custom Show Link"

        show_bridge_link(
            sample_dataframe,
            name=name,
            tags=tags,
            base_url=base_url,
            link_text=link_text,
        )

        mock_display.assert_called_once()
        html_content = mock_display.call_args[0][0].data

        assert name in html_content
        assert link_text in html_content


class TestEdgeCases:
    """Test suite for edge cases and error conditions."""

    def test_dataframe_with_special_characters(self):
        """Test DataFrame with special characters and unicode."""
        df = pd.DataFrame(
            {
                "unicode": ["éñ", "中文", "🎉", "café"],
                "special": ["<>&\"'", "\n\t\r", "\\/", "{}[]"],
                "numbers": [float("inf"), float("-inf"), 0, -1],
            }
        )

        # Should handle special characters without error
        compressed = GrafikiBridge.compress_dataframe(df)
        assert isinstance(compressed, str)

        # Should be decompressible
        decoded = base64.b64decode(compressed)
        decompressed = gzip.decompress(decoded)
        data = json.loads(decompressed.decode("utf-8"))

        assert len(data["dataset"]["data"]) == len(df)

    def test_dataframe_with_none_values(self):
        """Test DataFrame with None/NaN values."""
        df = pd.DataFrame(
            {
                "with_none": [1, None, 3, None],
                "with_nan": [1.0, float("nan"), 3.0, float("nan")],
                "mixed": ["a", None, "c", float("nan")],
            }
        )

        compressed = GrafikiBridge.compress_dataframe(df)
        assert isinstance(compressed, str)

    def test_dataframe_with_datetime(self):
        """Test DataFrame with datetime objects."""
        df = pd.DataFrame(
            {
                "dates": pd.date_range("2023-01-01", periods=5),
                "timestamps": pd.to_datetime(["2023-01-01 12:00:00"] * 5),
            }
        )

        # Should handle datetime objects (converted to string by default=str)
        compressed = GrafikiBridge.compress_dataframe(df)
        assert isinstance(compressed, str)

    def test_very_large_dataframe_handling(self):
        """Test handling of very large DataFrames that might exceed URL limits."""
        # Create a DataFrame that will definitely exceed URL limits
        large_data = {f"col_{i}": list(range(10000)) for i in range(100)}
        large_df = pd.DataFrame(large_data)

        bridge = GrafikiBridge()

        # Should still create a link (even if it's not browser-compatible)
        url = bridge.create_webapp_link(large_df)
        assert isinstance(url, str)
        assert url.startswith("https://www.grafiki.app/d#")

        # Should detect compatibility issues
        compatibility = bridge._check_url_compatibility(url)
        assert compatibility["has_compatibility_issues"]
        assert (
            len(compatibility["compatible_browsers"]) == 0
        )  # Too large for all browsers

    def test_empty_string_parameters(self):
        """Test handling of empty string parameters."""

        with patch("grafiki.core.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20231215_143022"

            df = pd.DataFrame({"A": [1, 2, 3]})

            compressed = GrafikiBridge.compress_dataframe(df, name="", tags=[])

            decoded = base64.b64decode(compressed)
            decompressed = gzip.decompress(decoded)
            data = json.loads(decompressed.decode("utf-8"))

            assert data["dataset"]["name"] == "Dataset_20231215_143022"
            assert data["dataset"]["tags"] == []


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_full_workflow(self):
        """Test the complete workflow from DataFrame to display."""
        # Create test data
        df = pd.DataFrame(
            {
                "category": ["A", "B", "C", "A", "B"],
                "value": [10, 20, 30, 15, 25],
                "is_active": [True, False, True, True, False],
            }
        )

        # Test compression
        compressed = GrafikiBridge.compress_dataframe(
            df, name="Integration Test", tags=["integration"]
        )
        assert isinstance(compressed, str)

        # Test bridge creation
        bridge = GrafikiBridge()
        url = bridge.create_webapp_link(
            df, name="Integration Test", tags=["integration"]
        )
        assert url.startswith("https://www.grafiki.app/d#")

        # Test statistics
        stats = bridge._get_compression_stats(df)
        assert stats["compression_ratio"] > 0

        # Test compatibility check
        compatibility = bridge._check_url_compatibility(url)
        assert "url_length" in compatibility

        # Test convenience functions
        convenience_url = bridge_df(df, name="Integration Test", tags=["integration"])
        assert convenience_url == url

    @patch("grafiki.core.display")
    def test_display_integration(self, mock_display):
        """Test display integration with various DataFrame types."""
        test_cases = [
            pd.DataFrame({"simple": [1, 2, 3]}),
            pd.DataFrame(),  # Empty
            pd.DataFrame({"complex": [{"nested": "data"}, {"nested": "more"}]}),
        ]

        bridge = GrafikiBridge()

        for i, df in enumerate(test_cases):
            bridge.display_link(df, name=f"Test Case {i}")

        # Should have called display for each test case
        assert mock_display.call_count == len(test_cases)


# Pytest configuration and fixtures
@pytest.fixture(scope="session")
def sample_data():
    """Session-scoped sample data for performance testing."""
    return pd.DataFrame(
        {
            "id": range(1000),
            "name": [f"item_{i}" for i in range(1000)],
            "value": [i * 1.5 for i in range(1000)],
            "category": [f"cat_{i % 10}" for i in range(1000)],
        }
    )


# Performance tests (marked for optional execution)
@pytest.mark.performance
class TestPerformance:
    """Performance tests for GrafikiBridge."""

    def test_compression_performance(self, sample_data):
        """Test compression performance with moderately large data."""
        import time

        start_time = time.time()
        compressed = GrafikiBridge.compress_dataframe(sample_data)
        end_time = time.time()

        # Should complete in reasonable time (< 5 seconds for 1000 rows)
        assert (end_time - start_time) < 5.0
        assert isinstance(compressed, str)

    def test_multiple_compressions_performance(self, sample_data):
        """Test performance of multiple compression operations."""
        import time

        start_time = time.time()

        # Perform multiple compressions
        for i in range(10):
            subset = sample_data.iloc[:100]  # Use smaller subsets
            GrafikiBridge.compress_dataframe(subset, name=f"test_{i}")

        end_time = time.time()

        # Should complete all operations in reasonable time
        assert (end_time - start_time) < 10.0


if __name__ == "__main__":
    # Run tests with: python -m pytest test_grafiki.py -v
    # Run with performance tests: python -m pytest test_grafiki.py -v -m performance
    pytest.main([__file__, "-v"])
