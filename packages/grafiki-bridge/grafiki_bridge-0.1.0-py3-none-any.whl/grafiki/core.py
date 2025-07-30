import base64
import gzip
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from IPython.display import HTML, display


class GrafikiBridge:
    """Python plugin for compressing pandas DataFrames and generating web app links for visualization.

    This class provides functionality to compress pandas DataFrames into base64-encoded gzip format
    and generate URLs for visualization in a web application. It includes browser compatibility
    checking and compression statistics.

    Attributes:
        BROWSER_LIMITS (Dict[str, int]): URL length limits for different browsers in bytes.
        base_url (str): The base URL of the web application.
    """

    # Browser URL length limits (bytes)
    BROWSER_LIMITS = {
        "chrome": 2048000,
        "firefox": 65536,
        "safari": 80000,
        "edge": 2048000,
        "default": 65536,
    }

    def __init__(self, base_url: str = "https://www.grafiki.app"):
        """Initialize the GrafikiBridge with a web app base URL.

        Args:
            base_url (str, optional): The base URL of the web application.
                Defaults to "https://www.grafiki.app".
        """
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def compress_dataframe(
        df: pd.DataFrame, name: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> str:
        """Compress a pandas DataFrame to base64 encoded gzip format.

        Args:
            df (pd.DataFrame): The DataFrame to compress.
            name (Optional[str], optional): Name for the dataset. If None, generates a
                timestamp-based name. Defaults to None.
            tags (Optional[List[str]], optional): List of tags to associate with the dataset.
                Defaults to None.

        Returns:
            str: Base64 encoded gzip compressed string representation of the DataFrame.
        """
        dataset = {
            "data": df.to_dict("records"),
            "name": name or f"Dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "tags": tags or [],
        }

        json_str = json.dumps({"dataset": dataset}, default=str)
        compressed_data = gzip.compress(json_str.encode("utf-8"))
        return base64.b64encode(compressed_data).decode("utf-8")

    def create_webapp_link(
        self,
        df: pd.DataFrame,
        name: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Create a web app link with compressed DataFrame data.

        Args:
            df (pd.DataFrame): The DataFrame to create a link for.
            name (Optional[str], optional): Name for the dataset. If None, generates a
                timestamp-based name. Defaults to None.
            tags (Optional[List[str]], optional): List of tags to associate with the dataset.
                Defaults to None.

        Returns:
            str: Complete URL for the web application with compressed data as fragment.
        """
        compressed_data = self.compress_dataframe(df, name, tags)
        return f"{self.base_url}/d#{compressed_data}"

    def _get_compression_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate compression statistics for a DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame to analyze.

        Returns:
            Dict[str, Any]: Dictionary containing compression statistics with keys:
                - compression_ratio (float): Ratio of original to compressed size
                - space_saved_percent (float): Percentage of space saved through compression
        """
        original_json = json.dumps(df.to_dict("records"), default=str)
        original_size = len(original_json.encode("utf-8"))
        compressed_size = len(self.compress_dataframe(df).encode("utf-8"))

        return {
            "compression_ratio": (
                original_size / compressed_size if compressed_size > 0 else 0
            ),
            "space_saved_percent": (
                ((original_size - compressed_size) / original_size * 100)
                if original_size > 0
                else 0
            ),
        }

    def _check_url_compatibility(self, url: str) -> Dict[str, Any]:
        """Check URL compatibility across different browsers.

        Args:
            url (str): The URL to check for browser compatibility.

        Returns:
            Dict[str, Any]: Dictionary containing compatibility information with keys:
                - url_length (int): Length of the URL in characters
                - compatible_browsers (List[str]): List of compatible browser names
                - has_compatibility_issues (bool): True if compatible with fewer than 3 browsers
        """
        url_length = len(url)

        # Check major browsers
        compatible_browsers = []
        for browser, limit in self.BROWSER_LIMITS.items():
            if browser != "default" and url_length <= limit:
                compatible_browsers.append(browser)

        return {
            "url_length": url_length,
            "compatible_browsers": compatible_browsers,
            "has_compatibility_issues": len(compatible_browsers)
            < 3,  # Less than 3 major browsers
        }

    def display_link(
        self,
        df: pd.DataFrame,
        name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        link_text: str = "Open Dataset",
    ) -> None:
        """Display an interactive dataset link with comprehensive statistics and browser compatibility info.

        Creates an HTML widget that shows dataset information, compression statistics,
        browser compatibility, and provides a clickable link to open the dataset in the web app.

        Args:
            df (pd.DataFrame): The DataFrame to create a display link for.
            name (Optional[str], optional): Name for the dataset. If None, generates a
                timestamp-based name. Defaults to None.
            tags (Optional[List[str]], optional): List of tags to associate with the dataset.
                Defaults to None.
            link_text (str, optional): Text to display on the link button.
                Defaults to "Open Dataset".

        Returns:
            None: Displays HTML content directly in the Jupyter notebook.
        """

        url = self.create_webapp_link(df, name, tags)
        dataset_name = name or f"Dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Get statistics
        compression_stats = self._get_compression_stats(df)
        url_info = self._check_url_compatibility(url)

        # Determine status
        if not url_info["compatible_browsers"]:
            status_class = "error"
            status_text = "URL too long for browser compatibility"
            button_disabled = True
        elif url_info["has_compatibility_issues"]:
            status_class = "warning"
            status_text = f"Limited compatibility ({len(url_info['compatible_browsers'])} browsers)"
            button_disabled = False
        else:
            status_class = "success"
            status_text = "Compatible with all major browsers"
            button_disabled = False

        # JavaScript for browser detection and dynamic updates
        js_code = f"""
        <script>
        (function() {{
            const userAgent = navigator.userAgent.toLowerCase();
            let browser = 'unknown';

            if (userAgent.includes('chrome') && !userAgent.includes('edg')) browser = 'chrome';
            else if (userAgent.includes('firefox')) browser = 'firefox';
            else if (userAgent.includes('safari') && !userAgent.includes('chrome')) browser = 'safari';
            else if (userAgent.includes('edg')) browser = 'edge';

            const browserSpan = document.querySelector('.detected-browser');
            if (browserSpan) {{
                browserSpan.textContent = browser.charAt(0).toUpperCase() + browser.slice(1);

                // Update compatibility for user's browser
                const limits = {json.dumps(self.BROWSER_LIMITS)};
                const urlLength = {url_info['url_length']};
                const userLimit = limits[browser] || limits.default;
                const percentage = ((urlLength / userLimit) * 100).toFixed(1);

                const statusSpan = document.querySelector('.browser-status');
                if (statusSpan) {{
                    if (urlLength > userLimit) {{
                        statusSpan.innerHTML = `<span style="color: #dc3545;">⚠️ May not work (${{percentage}}% of limit)</span>`;
                    }} else {{
                        statusSpan.innerHTML = `<span style="color: #28a745;">✓ Compatible (${{percentage}}% of limit)</span>`;
                    }}
                }}
            }}
        }})();
        </script>
        """

        html_content = f"""
        <div style="
            border: 1px solid #e1e5e9;
            border-radius: 6px;
            padding: 20px;
            margin: 15px 0;
            background: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <h3 style="margin: 0; color: #24292e; font-size: 16px; font-weight: 600;">
                    📊 {dataset_name}
                </h3>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; font-size: 14px; color: #586069;">
                <div>
                    <div><strong>Rows:</strong> {df.shape[0]:,}</div>
                    <div><strong>Columns:</strong> {df.shape[1]}</div>
                    <div><strong>Memory:</strong> {df.memory_usage(deep=True).sum() / 1024:.1f} KB</div>
                </div>
                <div>
                    <div><strong>Compression:</strong> {compression_stats['compression_ratio']:.1f}x</div>
                    <div><strong>Space Saved:</strong> {compression_stats['space_saved_percent']:.1f}%</div>
                    <div><strong>Your Browser:</strong> <span class="detected-browser">Detecting...</span></div>
                </div>
            </div>

            <div style="
                padding: 12px;
                border-radius: 4px;
                margin-bottom: 16px;
                font-size: 13px;
                background-color: {'#f8f9fa' if status_class == 'success' else '#fff3cd' if status_class == 'warning' else '#f8d7da'};
                color: {'#155724' if status_class == 'success' else '#856404' if status_class == 'warning' else '#721c24'};
                border: 1px solid {'#d4edda' if status_class == 'success' else '#ffeaa7' if status_class == 'warning' else '#f5c6cb'};
            ">
                <div><strong>Status:</strong> {status_text}</div>
                <div><strong>URL Length:</strong> {url_info['url_length']:,} characters</div>
                <div class="browser-status">Checking browser compatibility...</div>
            </div>

            <a href="{url if not button_disabled else '#'}"
               target="_blank"
               style="
                   display: inline-block;
                   background-color: {'#0366d6' if not button_disabled else '#6c757d'};
                   color: white;
                   padding: 8px 16px;
                   text-decoration: none;
                   border-radius: 4px;
                   font-size: 14px;
                   font-weight: 500;
                   transition: background-color 0.15s ease;
                   {'cursor: not-allowed;' if button_disabled else ''}
               "
               {'onclick="return false;"' if button_disabled else ''}
               onmouseover="if (!this.onclick) this.style.backgroundColor='#0256cc'"
               onmouseout="if (!this.onclick) this.style.backgroundColor='#0366d6'">
                {link_text} {'🔗' if not button_disabled else '🚫'}
            </a>
        </div>
        {js_code}
        """

        display(HTML(html_content))


# Convenience functions for easy use
def bridge_df(
    df: pd.DataFrame,
    name: Optional[str] = None,
    tags: Optional[List[str]] = None,
    base_url: str = "https://www.grafiki.app",
) -> str:
    """Convenience function to compress a DataFrame and return the webapp link.

    This is a simplified interface to the GrafikiBridge functionality that creates
    a compressed representation of a DataFrame and returns the corresponding web app URL.

    Args:
        df (pd.DataFrame): The DataFrame to compress and create a link for.
        name (Optional[str], optional): Name for the dataset. If None, generates a
            timestamp-based name. Defaults to None.
        tags (Optional[List[str]], optional): List of tags to associate with the dataset.
            Defaults to None.
        base_url (str, optional): The base URL of the web application.
            Defaults to "https://www.grafiki.app".

    Returns:
        str: Complete URL for the web application with compressed DataFrame data.

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        >>> url = bridge_df(df, name="My Dataset", tags=["sample", "test"])
        >>> print(url)
        https://www.grafiki.app/d#eJy...
    """
    bridge = GrafikiBridge(base_url)
    return bridge.create_webapp_link(df, name, tags)


def show_bridge_link(
    df: pd.DataFrame,
    name: Optional[str] = None,
    tags: Optional[List[str]] = None,
    base_url: str = "https://www.grafiki.app",
    link_text: str = "Open in Web App",
) -> None:
    """Convenience function to display a clickable link for a DataFrame with statistics.

    This function creates and displays an interactive HTML widget in a Jupyter notebook
    that shows DataFrame statistics, compression information, browser compatibility,
    and provides a clickable link to open the dataset in the web application.

    Args:
        df (pd.DataFrame): The DataFrame to create a display link for.
        name (Optional[str], optional): Name for the dataset. If None, generates a
            timestamp-based name. Defaults to None.
        tags (Optional[List[str]], optional): List of tags to associate with the dataset.
            Defaults to None.
        base_url (str, optional): The base URL of the web application.
            Defaults to "https://www.grafiki.app".
        link_text (str, optional): Text to display on the link button.
            Defaults to "Open in Web App".

    Returns:
        None: Displays HTML content directly in the Jupyter notebook.

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        >>> show_bridge_link(df, name="My Dataset", tags=["sample", "test"])
        # Displays an interactive widget with dataset information and link
    """
    bridge = GrafikiBridge(base_url)
    bridge.display_link(df, name, tags, link_text=link_text)
