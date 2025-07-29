from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

class ScrapeRequest(BaseModel):
    headless:bool=True
    url:str
    no_cache:bool=False
    html_only:bool=False
    chunk_size:int=1000
    chunk_overlap:float=0.1
    skip_char:int=500
    skip_chunk:int=0
    process_timeout:int=60

class ScreenshotRequest(BaseModel):
    url:str
    headless:bool=True
    no_cache:bool=False
    process_timeout:int=60

class ParsedChunk(BaseModel):
    index: int = Field(..., description="The index of the chunk in the list of chunks.")
    link_title: str = Field(..., description="The title of the search result that this chunk belongs to and can be used for citation.")
    link:str = Field(..., description="The link can be used to reference the SearchResult that this chunk belongs to and can be used for citation.")
    chunk: str = Field(..., description="The text content of the chunk.")
    score: float = Field(..., description="The relevance score of this chunk.")

class ParsedResponse(BaseModel):
    source: str = Field(..., description="Source of the parsed content")
    title: str = Field(..., description="Title of the document")
    text: str = Field(..., description="Main body of the document")
    authors: list[str] = Field(default_factory=list, description="List of authors")
    summary: Optional[str] = Field(None, description="Summary of the document")
    keywords: list[str] = Field(default_factory=list, description="Keywords associated with the document")
    categories: list[str] = Field(default_factory=list, description="Categories the document belongs to")
    publish_date: Optional[str] = Field(None, description="Publication date of the document")
    length: int = Field(0, description="Total length of the document in characters, computed from text")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Creation timestamp of the parsed response")
    links: dict[str, str] = Field(default_factory=dict, description="Dictionary of links related to the document")
    chunks: Optional[list[ParsedChunk]] = Field(None, description="Optional list of text chunks parsed from the document")
    
class SearchRequest(BaseModel):
    search_query: str  # Search query
    link_limit: int = 3  # Number of links to return
    chunk_size: int = 1000  # Chunk size
    chunk_overlap: float = 0.1  # Chunk overlap %
    skip_char: int = 500  # Skip characters
    skip_chunk: int = 0  # Skip chunks
    chunk_limit: int = 3  # Chunk limit

class SearchResponse(BaseModel):
    query: str
    chunks: list[ParsedChunk]

class CrawlTreeNode(BaseModel):
    title: str
    url: str
    depth: int
    status: str = "PENDING"
    reason: Optional[str]=None
    parent: Optional[str]=None
    children: Optional[list]=[]

class CrawlJob(BaseModel):
    job_id: str
    root_url: str
    max_depth: int
    max_count: int
    include_external: bool
    status: str
    result: Optional[dict]
    root: Optional[CrawlTreeNode]=None
    
class CrawlRequest(BaseModel):
    root_url: str
    max_depth: int
    max_count: int
    include_external: bool
    force: Optional[bool] = False
    parser_type: Optional[str] = None

class UrlRequest(BaseModel):
    url: str
    
class EncodeRequest(BaseModel):
    text: str  # Text to encode

class EncodeResponse(BaseModel):
    encoded_data: list[float]  # The result of the encoding process