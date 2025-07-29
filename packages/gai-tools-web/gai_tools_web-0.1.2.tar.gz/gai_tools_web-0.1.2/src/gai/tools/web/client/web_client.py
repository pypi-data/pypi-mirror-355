import os
from typing import Union, Optional
from urllib.parse import urljoin, quote


from gai.lib.logging import getLogger
logger = getLogger(__name__)

from gai.lib.config import GaiClientConfig,config_helper
from gai.tools.web.lib.dtos import SearchRequest, SearchResponse, ScrapeRequest, ScreenshotRequest, ParsedResponse, CrawlRequest, CrawlJob
from gai.lib.http_utils import http_get_async, http_post_async

class WebClientAsync:
    
    def __init__(self, client_config: Optional[Union[GaiClientConfig, dict]] = None):
        if client_config is None:
            client_config = config_helper.get_client_config("tool-web")
        if isinstance(client_config, dict):
            client_config = config_helper.get_client_config(client_config)
        self.client_config = client_config
        self.url = client_config.url
        if not self.url.endswith("/"):
            self.url += "/"
            
    async def download(self, url: str) -> str:
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
        
        Parameters:
            url (str): Direct URL to the file you want to download
            
        Returns:
            str: Path to the downloaded temporary file. 
                IMPORTANT: You are responsible for cleaning up this file when done.
                The file will persist until manually deleted.
                
        Example usage:
            temp_path = await client.download("https://example.com/document.pdf")
            # Process the file...
            os.unlink(temp_path)  # Clean up when done
        """
        
        import requests
        import tempfile
        from urllib.parse import urlparse
        
        ## There is no server backend for this function. 
        ## Just HTTP get straight into a tempfile and return the tempfile name 
        
        try:
            # First, make a HEAD request to get Content-Type
            head_response = requests.head(url, allow_redirects=True)
            content_type = head_response.headers.get('content-type', '').lower()
            
            # Determine extension from Content-Type
            ext_map = {
                'application/pdf': '.pdf',
                'image/jpeg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'text/html': '.html',
                'application/zip': '.zip',
                'application/json': '.json',
                'text/plain': '.txt',
                'video/mp4': '.mp4',
                'audio/mpeg': '.mp3'
            }
            
            ext = ext_map.get(content_type.split(';')[0], '')
            
            # Fallback to URL extension if Content-Type doesn't help
            if not ext:
                parsed_url = urlparse(url)
                if '.' in os.path.basename(parsed_url.path):
                    _, ext = os.path.splitext(parsed_url.path)
            
        except:
            # If HEAD request fails, try to get extension from URL
            parsed_url = urlparse(url)
            if '.' in os.path.basename(parsed_url.path):
                _, ext = os.path.splitext(parsed_url.path)
            else:
                ext = ''
        
        # Create persistent temporary file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,  # This ensures the file persists after closing
            suffix=ext,    # Preserve file extension
            prefix='download_'
        )
        
        filename = temp_file.name
        temp_file.close()  # Close the file handle so we can write to it
        
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            return filename
            
        except Exception as e:
            # Clean up the temp file if download fails
            if os.path.exists(filename):
                os.unlink(filename)
            raise e
        
    async def scrape(self,
            url: str,
            headless: bool = True,
            no_cache: bool = False,
            chunk_size: int = 1000,
            chunk_overlap: float = 0.1,
            skip_char: int = 500,
            skip_chunk: int = 0,
            process_timeout: int = 60,
            html_only: bool = False
            ) -> Union[ParsedResponse, str]:
        """
        Scrape a webpage and return the parsed response.

        Parameters:
            url (str):
                The full URL of the page to scrape.
            headless (bool, optional):
                Whether to run the browser in headless mode. Defaults to True.
            no_cache (bool, optional):
                If True, bypass any server‐side or local caching. Defaults to False.
            chunk_size (int, optional):
                Maximum number of characters per text chunk. Defaults to 1000.
            chunk_overlap (float, optional):
                Fractional overlap between consecutive chunks (0.0–1.0). Defaults to 0.1.
            skip_char (int, optional):
                Number of initial characters to skip before chunking. Defaults to 500.
            skip_chunk (int, optional):
                Number of whole chunks to skip at the front. Defaults to 0.
            process_timeout (int, optional):
                Seconds to wait before timing out the scraping process. Defaults to 60.
        
        Output:
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
        if not self.url:
            raise ValueError("WebClientAsync: url is not set in the client config.")

        endpoint_url = urljoin(self.url, "scrape")
        req = ScrapeRequest(
            url=url,
            headless=headless,
            no_cache=no_cache,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            skip_char=skip_char,
            skip_chunk=skip_chunk,
            process_timeout=process_timeout,
            html_only=html_only
        ).model_dump()

        response = await http_post_async(endpoint_url, data=req, timeout=process_timeout)
        
        # Check if response is None before accessing json method
        if response is None:
            raise ValueError("No response received from the server")
        
        if isinstance(response.json(),str):
            return response.json()
        
        return ParsedResponse(**response.json())

    async def screenshot(self,
            url: str,
            headless: bool = True,
            no_cache: bool = False,
            process_timeout: int = 60,
            ) -> bytes:
        """
        Scrape a webpage and return the parsed response.

        Parameters:
            url (str):
                The full URL of the page to scrape.
            headless (bool, optional):
                Whether to run the browser in headless mode. Defaults to True.
            no_cache (bool, optional):
                If True, bypass any server‐side or local caching. Defaults to False.
            process_timeout (int, optional):
                Seconds to wait before timing out the scraping process. Defaults to 60.
        
        Output:
            - bytes: screenshot of the website       
        """
        if not self.url:
            raise ValueError("WebClientAsync: url is not set in the client config.")

        endpoint_url = urljoin(self.url, "screenshot")
        req = ScreenshotRequest(
            url=url,
            headless=headless,
            no_cache=no_cache,
            process_timeout=process_timeout,
        ).model_dump()

        response = await http_post_async(endpoint_url, data=req, timeout=process_timeout)
        
        # Check if response is None before accessing json method
        if response is None:
            raise ValueError("No response received from the server")
        
        # Check if the response indicates an error
        if response.status_code >= 400:
            try:
                error_detail = response.json()
                raise ValueError(f"Screenshot request failed: {error_detail}")
            except:
                raise ValueError(f"Screenshot request failed with status {response.status_code}: {response.text}")

        # Check if response contains binary data
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            raise ValueError(f"Expected image response, got content-type: {content_type}")

        # Return the binary content
        return response.content

    async def search(self,
            search_query,
            link_limit=3,
            chunk_size=1000,
            chunk_overlap=0.1,
            skip_char=500,
            skip_chunk=0,
            chunk_limit=3
            ) -> SearchResponse:
        """
        Run a web search via the remote service and return the parsed results in chunks and reranked by semantic scores.

        Parameters:
            search_query (str):
                The text to search for.
            link_limit (int, optional):
                Maximum number of search result links to retrieve. Defaults to 3.
            chunk_size (int, optional):
                Maximum number of characters per text chunk. Defaults to 1000.
            chunk_overlap (float, optional):
                Fractional overlap between consecutive chunks (0.0–1.0). Defaults to 0.1.
            skip_char (int, optional):
                Number of initial characters to skip before chunking. Defaults to 500.
            skip_chunk (int, optional):
                Number of full chunks to skip at the start. Defaults to 0.
            chunk_limit (int, optional):
                Maximum number of chunks to return per link. Defaults to 3.

        Returns:
            SearchResponse:
              - query: The normalized search query returned by the service.
              - chunks: A list of Chunk objects, each containing:
                  • text: The chunked snippet of content.
                  • source: Origin URL or identifier.
                  • index: Position of the chunk within its document.

        Raises:
            ValueError: If `self.url` is not set or if the HTTP request returns no response.
        """        

        if not self.url:
            raise ValueError("WebClientAsync: url is not set in the client config.")        

        endpoint_url = urljoin(self.url,f"websearch")
        req = SearchRequest(
            search_query=search_query,
            link_limit=link_limit,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            skip_char=skip_char,
            skip_chunk=skip_chunk,
            chunk_limit=chunk_limit
            ).model_dump() 
        
        response = await http_get_async(endpoint_url,data=req,timeout=6000)
        
        # Check if response is None before accessing json method
        if response is None:
            raise ValueError("No response received from the server")
        response = SearchResponse(**response.json())
        
        logger.info(f"RagClientAsync.web_search_async: query={response.query} chunks={len(response.chunks)}")
        return response
    

    async def create_job(self,
            root_url: str,
            max_depth: int = 3,
            max_count: int = 100,
            include_external: bool = False,
            force: bool = False
            ) -> CrawlJob:
        """
        Create a pending crawl job.
        """
        if not self.url:
            raise ValueError("WebClientAsync: url is not set in the client config.")        

        endpoint_url = urljoin(self.url, "crawl")
        req = CrawlRequest(
            root_url=root_url,
            max_depth=max_depth,
            max_count=max_count,
            include_external=include_external,
            force=force
        ).model_dump()

        response = await http_post_async(endpoint_url, data=req, timeout=6000)

        # Check if response is None before accessing json method
        if response is None:
            raise ValueError("No response received from the server")
       
        return CrawlJob(**response.json())

    async def get_crawl_job(self, job_id: str) -> CrawlJob:
        """
        Get job status by job_id.
        """
        if not self.url:
            raise ValueError("WebClientAsync: url is not set in the client config.")

        endpoint_url = urljoin(self.url, f"crawl/job/{job_id}")
        response = await http_get_async(endpoint_url, timeout=6000)
        
        # Check if response is None before accessing json method
        if response is None:
            raise ValueError("No response received from the server")
        
        return CrawlJob(**response.json())

    async def get_crawl_doc(self, job_id: str, url: str) -> CrawlJob:
        """
        Get the parsed document result by job_id and url.
        """
        if not self.url:
            raise ValueError("WebClientAsync: url is not set in the client config.")
        
        first_encoded = quote(url, safe='')
        double_encoded_url = quote(first_encoded, safe='')
        endpoint_url = f"{self.url.rstrip('/')}/crawl/job/{job_id}/{double_encoded_url}"        
        response = await http_get_async(endpoint_url, timeout=6000)
        
        # Check if response is None before accessing json method
        if response is None:
            raise ValueError("No response received from the server")
        
        return ParsedResponse(**response.json())

    # async def cancel_crawl_job_async(self, job_id: str) -> CrawlJob:
    #     endpoint_url = urljoin(self.url, f"crawl/job/cancel/{job_id}")
    #     response = await http_post_async(endpoint_url, timeout=6000)
    #     return CrawlJob(**response.json())

    # async def rerun_crawl_job_async(self, job_id: str) -> CrawlJob:
    #     endpoint_url = urljoin(self.url, f"crawl/job/rerun/{job_id}")
    #     response = await http_post_async(endpoint_url, timeout=6000)
    #     return CrawlJob(**response.json())
    