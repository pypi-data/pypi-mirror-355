"""
Developer Notes:

About Gai Web MCP Server

gai.mcp.web.mcp_server is a wrapper for gai.tools.web.client.WebClientAsync.
In other words, it is a wrapper for the client and is not the actual server.
Do not confuse this with the actual server: gai.tools.web.server, which you should run in a separate devcontainer.

The purpose of this server is to provide documentation to the LLM so that it can reason if the tool is a good candidate for the task at hand.
In other words, the comments are meant for AI and not for humans.

"""

import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("gai-mcp-web-svr")

import sys
from gai.tools.web.client import WebClientAsync
from gai.tools.web.lib import ParsedResponse, SearchResponse


@mcp.tool()
async def scrape(url: str) -> ParsedResponse:
    """
    Scrape a webpage and return the parsed response.

    Args:
        - url (str): The URL of the webpage to scrape.
    Returns:
        - source: Source of the parsed content
        - title: Title of the document
        - text: Main body of the document
        - authors: List of authors
        - summary: Summary of the document
        - keywords: Keywords associated with the document
        - categories: Categories the document belongs to
        - publish_date: Publication date of the document
        - length: Total length of the document in characters, computed from text
        - created_at: Creation timestamp of the parsed response
        - links: Dictionary of links related to the document
        - chunks: Optional list of text chunks parsed from the document
    """

    if not url:
        raise ValueError("URL is required for scraping.")
    try:
        web_client = WebClientAsync()
        print(f"mcp_server.scrape: url={url}")
        result = await web_client.scrape(
            url=url,
            headless=True,
            no_cache=False,
            chunk_size=1000,
            chunk_overlap=0.1,
            skip_char=500,
            skip_chunk=0,
            process_timeout=60,
        )
        return result
        # return json.dumps(result.model_dump(), indent=4, default=str)
    except Exception as e:
        print(f"mcp_server.search: error={e}")
        raise e


@mcp.tool()
async def search(search_query) -> SearchResponse:
    """
    The 'search' function is a powerful tool that allows the AI to gather external information from the internet using Google search. It can be invoked when the AI needs to answer a question or provide information that requires up-to-date, comprehensive, and diverse sources which are not inherently known by the AI. For instance, it can be used to find current news, weather updates, latest sports scores, trending topics, specific facts, or even the current date and time. The usage of this tool should be considered when the user's query implies or explicitly requests recent or wide-ranging data, or when the AI's inherent knowledge base may not have the required or most current information. The 'search_query' parameter should be a concise and accurate representation of the information needed.

    Args:
    - search_query (str): The query to search for on the web. This should be a concise and accurate representation of the information needed.

    Returns:
    - query: str
    - chunks: List[Chunk]
    """
    try:
        web_client = WebClientAsync()
        result = await web_client.search(
            search_query=search_query,
            link_limit=3,
            chunk_size=1000,
            chunk_overlap=0.1,
            skip_char=500,
            skip_chunk=0,
            chunk_limit=3,
        )
        return result
    except Exception as e:
        print(f"mcp_server.search: error={e}")
        raise e


@mcp.tool()
async def screenshot(url: str) -> str:
    """
    Take a screenshot of a webpage and save it to a temporary file.

    Use this tool when you need to:
    - Capture visual representation of websites
    - Get screenshots for documentation or analysis
    - Verify how a webpage appears visually
    - Capture dynamic content that may not be accessible via scraping
    - Create visual records of web pages

    Args:
        url (str): The URL of the webpage to screenshot

    Returns:
        str: Path to the temporary screenshot file (PNG format).
             IMPORTANT: You are responsible for cleaning up this file when done.

    Example usage:
        temp_path = await screenshot("https://example.com")
        # Process the screenshot...
        os.unlink(temp_path)  # Clean up when done
    """
    if not url:
        raise ValueError("URL is required for taking screenshot.")

    import tempfile

    try:
        web_client = WebClientAsync()
        print(f"mcp_server.screenshot: url={url}")

        # Get screenshot as bytes
        screenshot_bytes = await web_client.screenshot(
            url=url, headless=True, no_cache=False, process_timeout=60
        )

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=".png", prefix="screenshot_"
        )

        with open(temp_file.name, "wb") as f:
            f.write(screenshot_bytes)

        return temp_file.name

    except Exception as e:
        print(f"mcp_server.screenshot: error={e}")
        raise e


@mcp.tool()
async def download(url: str) -> str:
    """
    Download a file from the web and save it to a temporary location.

    Use this tool when you need to:
    - Download files (PDFs, images, videos, documents, archives, etc.) from URLs
    - Access file content that requires downloading rather than web scraping
    - Obtain binary files that cannot be processed through text-based scraping
    - Download files for further processing, analysis, or storage
    - Get files from direct download links, file servers, or content repositories

    Examples of when to use this tool:
    - "Download this PDF document from the URL"
    - "Get the image file from this link"
    - "Download the dataset file for analysis"
    - "Fetch the software installer from the download page"
    - "Download the CSV file containing the data"

    Do NOT use this for:
    - Scraping webpage content (use scrape() instead)
    - Taking screenshots of webpages (use screenshot() instead)
    - Reading text content from web pages (use scrape() instead)

    Args:
        url (str): Direct URL to the file you want to download

    Returns:
        str: Path to the downloaded temporary file.
             IMPORTANT: You are responsible for cleaning up this file when done.
             The file will persist until manually deleted.

    Example usage:
        temp_path = await download("https://example.com/document.pdf")
        # Process the file...
        os.unlink(temp_path)  # Clean up when done
    """
    if not url:
        raise ValueError("URL is required for downloading.")

    try:
        web_client = WebClientAsync()
        print(f"mcp_server.download: url={url}")

        result = await web_client.download(url=url)
        return result

    except Exception as e:
        print(f"mcp_server.download: error={e}")
        raise e


if __name__ == "__main__":
    mcp.run(transport="stdio")
