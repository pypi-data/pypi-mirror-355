"""PyCaber Python Extension Stub File"""

from typing import Optional, Dict, List, Any, Union, AsyncGenerator
import asyncio

def configure(
    api_key: Any,
    caber_host: Any,
    config_override: Any,
    timeout_secs: Any,
    max_retries: Any,
    initial_backoff: Any,
    backoff_factor: Any
) -> Any:
    """
    Initialize the global configuration and the OBO processor.
    This should be called once at the start with API key and Caber host parameters.
    Both api_key and caber_host are optional - if not provided, will try to use environment variables.
    If neither parameters nor environment variables are set, will operate in offline mode.
    
    Initializes the global configuration for all processing functions and sets up
    the OBO processor for authorization handling. Must be called before using any
    other functions in the module.
    
    Args:
        api_key (str, optional): Caber API key for authentication. If None, uses CABER_API_KEY env var
        caber_host (str or list of str, optional): Caber host URL(s). Can be:
            - Single string: "https://api.caber.com"
            - List of strings: ["https://api1.caber.com", "https://api2.caber.com"]
            - If None, uses CABER_HOST env var
            - When multiple hosts provided, will test connectivity and use first working host
        timeout_secs (int, optional): Request timeout in seconds (default: 10)
        max_retries (int, optional): Maximum number of retries for failed requests (default: 10)
        initial_backoff (float, optional): Initial backoff delay in seconds (default: 1.0)
        backoff_factor (float, optional): Backoff multiplier for each retry (default: 1.5)
        config_override (dict, optional): ADVANCED: Configuration values to override built-in defaults. 
                                          Must be a nested Python dictionary matching the structure of the Caber 
                                          configuration file, with sections like "csi_genai_lib", "RKCQF", etc. 
                                          For example: {"csi_genai_lib": {"maxBodyLen": 1024}, "RKCQF": {"keyBits": 64}}.
    
    Returns:
        bool: True if initialization was successful
    
    Raises:
        RuntimeError: If configuration initialization fails
    
    Example:
        >>> import pycaber
        >>> # Configure with explicit parameters
        >>> success = pycaber.configure(
        ...     api_key="your_api_key_here",
        ...     caber_host="https://api.caber.com",
        ...     config_override={"chunker": {"min_chunk_size": 1024}}
        ... )
        >>> print(f"Configuration successful: {success}")
        >>>
        >>> # Configure with multiple hosts (automatic failover)
        >>> success = pycaber.configure(
        ...     api_key="your_api_key_here",
        ...     caber_host=["https://api1.caber.com", "https://api2.caber.com", "https://backup.caber.com"]
        ... )
        >>> # The system will test each host in order and use the first one that connects
        >>>
        >>> # Configure with custom timeout and retry parameters
        >>> success = pycaber.configure(
        ...     api_key="your_api_key_here",
        ...     caber_host="https://api.caber.com",
        ...     timeout_secs=30,
        ...     max_retries=5,
        ...     initial_backoff=2.0,
        ...     backoff_factor=2.0
        ... )
        >>>
        >>> # Configure using environment variables
        >>> success = pycaber.configure()  # Uses CABER_API_KEY and CABER_HOST env vars
    """
    ...

def original_call_terminated(
    api_user: Any,
    api_id: Any
) -> Any:
    """
    Mark an original call as terminated using the global OBO processor
    For testing purposes primarily
    
    Signals that an API call has been completed and any associated OBO processing
    sessions should be terminated. This is important for cleanup and resource
    management in long-running OBO processing scenarios.
    
    Args:
        api_user (str, optional): API user identifier. Defaults to "anonymous"
        api_id (str, optional): API identifier to terminate. Defaults to "default"
    
    Returns:
        bool: True if termination was successful, False otherwise
    
    Raises:
        RuntimeError: If OBO processor not initialized
    
    Example:
        >>> import pycaber
        >>> pycaber.configure(api_key="key", caber_host="host")
        >>> # ... process some data with OBO ...
        >>> success = await pycaber.original_call_terminated("user1", "api_call_123")
        >>> print(f"Termination successful: {success}")
    """
    ...

def post_object(
    filename: Any,
    owner: Any,
    data: Any,
    copy_from: Any,
    from_host: Any,
    bucket: Any,
    bucket_host: Any
) -> Any:
    """
    Post an object to storage and send an SQS notification
    
    Uploads data to object storage (S3-compatible) and sends a notification message
    via SQS. The data can be provided directly as bytes, from a file-like object,
    or by copying from an existing file path.
    
    Args:
        filename (str): Name/key for the object in storage
        owner (str): Owner identifier for the object
        data (bytes or file-like, optional): Data to upload. Can be bytes or object with read() method
        copy_from (str, optional): Local file path to copy data from (alternative to data parameter)
        from_host (str, optional): Source hostname for tracking
        bucket (str, optional): S3 bucket name (uses default if not specified)
        bucket_host (str, optional): S3 endpoint URL (uses default if not specified)
    
    Returns:
        bool: True if upload and notification were successful
    
    Raises:
        RuntimeError: If API not configured, upload fails, or notification fails
    
    Note:
        Requires valid API configuration via configure() function.
        Either 'data' or 'copy_from' must be provided, but not both.
    
    Example:
        >>> import pycaber
        >>> pycaber.configure(api_key="key", caber_host="host")
        >>>
        >>> # Upload bytes data
        >>> data = b"Hello, world!"
        >>> success = await pycaber.post_object("hello.txt", "user123", data=data)
        >>>
        >>> # Upload from file
        >>> success = await pycaber.post_object(
        ...     "document.pdf", "user123", copy_from="/path/to/file.pdf"
        ... )
    """
    ...

def process_json(
    filename_or_generator: Any
) -> Any:
    """
    Process data using JSON parsing using the global config
    For testing purposes primarily
    
    Parses JSON data from a generator and extracts key-value pairs into a flattened
    dictionary. Uses the globally configured JSON processor settings for parsing
    parameters and thresholds.
    
    Args:
        filename_or_generator: Iterator/generator yielding byte chunks containing JSON data, or filename string
    
    Returns:
        dict: Flattened dictionary where:
            - Keys are JSON object keys as bytes
            - Values are converted JSON values (strings as bytes, numbers, bools, etc.)
    
    Raises:
        RuntimeError: If configuration not initialized or JSON parsing fails
    
    Example:
        >>> import pycaber
        >>> pycaber.configure()
        >>> def json_gen():
        ...     yield b'{"name": "John", '
        ...     yield b'"age": 30}'
        >>> result = await pycaber.process_json(json_gen())
        >>> name = result[b'name']  # Returns b'John'
        
        >>> # Or with a filename:
        >>> result = await pycaber.process_json("/path/to/data.json")
    """
    ...

def process_sha256(
    filename_or_generator: Any
) -> Any:
    """
    Process data using SHA256 hashing using the global config
    
    Computes SHA256 hash of data from a generator using the globally configured
    SHA256 processor settings.
    
    Args:
        filename_or_generator: Iterator/generator yielding byte chunks, or filename string
    
    Returns:
        dict: Dictionary containing:
            - 'sha256': bytes - The final SHA256 hash
            - 'chunks': list - List of input byte chunks
    
    Raises:
        RuntimeError: If configuration not initialized or processing fails
    
    Example:
        >>> import pycaber
        >>> pycaber.configure()
        >>> def data_gen():
        ...     yield b"hello"
        ...     yield b"world"
        >>> result = await pycaber.process_sha256(data_gen())
        >>> hash_bytes = result['sha256']
        >>> chunks = result['chunks']
        
        >>> # Or with a filename:
        >>> result = await pycaber.process_sha256("/path/to/file.txt")
    """
    ...

def request_obo(
    chunk: Any,
    chunk_dict: Any,
    mime_type: Any,
    api_user: Any,
    api_id: Any
) -> Any:
    """
    Process OBO request for a chunk of data using the global config
    For testing purposes primarily
    
    Processes an On-Behalf-Of (OBO) authorization request for content chunks.
    This determines what user and API should be used for processing the content
    based on the nmers (content fingerprints) found in the data.
    
    Args:
        chunk (bytes): The raw data chunk being processed
        chunk_dict (dict): Dictionary mapping nmer integers to chunk bytes
        mime_type (str, optional): MIME type of the content. Defaults to "application/octet-stream"
        api_user (str, optional): Original API user. Defaults to "anonymous"
        api_id (str, optional): Original API identifier. Defaults to "default"
    
    Returns:
        dict: Dictionary containing OBO results:
            - 'obo.user.name': Resolved user name for processing
            - 'obo.api.id': Resolved API identifier for processing
            - 'obo.redact.nmers': List of nmers to redact (if any)
    
    Raises:
        RuntimeError: If OBO processor not initialized or processing fails
    
    Example:
        >>> import pycaber
        >>> pycaber.configure(api_key="key", caber_host="host")
        >>> chunk = b"test content"
        >>> nmers = {12345: b"content_piece"}
        >>> result = await pycaber.request_obo(chunk, nmers, "text/plain", "user1", "api1")
        >>> resolved_user = result['obo.user.name']
    """
    ...

def response_obo(
    chunk: Any,
    chunk_dict: Any,
    mime_type: Any,
    api_user: Any,
    api_id: Any,
    obo_user: Any,
    obo_api: Any
) -> Any:
    """
    Process OBO response for a chunk of data using the global config
    For testing purposes primarily
    
    Processes an On-Behalf-Of (OBO) authorization response for content chunks.
    This handles the response direction of OBO processing, validating that the
    content being returned matches the expected authorization context.
    
    Args:
        chunk (bytes): The raw data chunk being processed
        chunk_dict (dict): Dictionary mapping nmer integers to chunk bytes
        mime_type (str, optional): MIME type of the content. Defaults to "application/octet-stream"
        api_user (str, optional): Original API user. Defaults to "anonymous"
        api_id (str, optional): Original API identifier. Defaults to "default"
        obo_user (str, optional): Expected OBO user. Defaults to "anonymous"
        obo_api (str, optional): Expected OBO API. Defaults to "default"
    
    Returns:
        dict: Dictionary containing OBO results:
            - 'obo.user.name': Validated user name for processing
            - 'obo.api.id': Validated API identifier for processing
            - 'obo.redact.nmers': List of nmers to redact (if any)
    
    Raises:
        RuntimeError: If OBO processor not initialized or processing fails
    
    Example:
        >>> import pycaber
        >>> pycaber.configure(api_key="key", caber_host="host")
        >>> chunk = b"response content"
        >>> nmers = {67890: b"response_piece"}
        >>> result = await pycaber.response_obo(
        ...     chunk, nmers, "application/json", "user1", "api1", "obo_user", "obo_api"
        ... )
        >>> validated_user = result['obo.user.name']
    """
    ...

def stream_process(
    filename_or_generator: Any,
    mime_type: Any,
    direction: Any,
    api_user: Any,
    api_id: Any,
    obo_user: Any,
    obo_api: Any
) -> Any:
    """
    Processes data through a pipeline of processors: SHA256, JSON (optional), and chunking
    Uses the globally initialized configuration.
    
    This is the main processing function that handles streaming data through multiple
    processing stages including hashing, JSON parsing, content chunking, and optional
    OBO (On Behalf Of) processing.
    
    Args:
        filename_or_generator: Iterator/generator yielding byte chunks, or file path string
        mime_type (str, optional): MIME type of the data. Defaults to "application/octet-stream"
        direction (str, optional): Processing direction ("request" or "response"). Defaults to "request"
        api_user (str, optional): API user identifier. Defaults to "DISABLED"
        api_id (str, optional): API identifier. Defaults to "DISABLED"
        obo_user (str, optional): On-behalf-of user. Defaults to ""
        obo_api (str, optional): On-behalf-of API. Defaults to ""
    
    Returns:
        CsiResults: Object containing SHA256 hash, input blocks, JSON data (if applicable),
                   fingerprints dictionary, OBO results (if enabled), and optional index filename
    
    Raises:
        RuntimeError: If configuration not initialized or processing fails
    
    Example:
        >>> import pycaber
        >>> pycaber.configure(api_key="your_key", caber_host="host")
        >>> def data_generator():
        ...     yield b"chunk1"
        ...     yield b"chunk2"
        >>> result = await pycaber.stream_process(data_generator(), mime_type="text/plain")
        >>> print(len(result.fingerprints))
    """
    ...

class CsiResults:
    """
    Python class that holds the results from stream_process
    
    Container class for the comprehensive results returned by the stream_process function.
    Provides access to all computed data including hashes, fingerprints, JSON extracts,
    OBO results, and optional index files.
    
    Attributes:
        sha256 (bytes): SHA256 hash of the entire input data
        input_blocks (list): List of original input data chunks as bytes
        json (list or None): Extracted JSON key-value pairs (if JSON processing enabled)
        fingerprints (dict): Content fingerprints mapping hash integers to chunk bytes
        obo (dict or None): On-Behalf-Of processing results (if OBO enabled)
        index_filename (str or None): Path to generated CQF index file (if indexing enabled)
        nmer_to_edges (dict): Mapping of content fingerprints to graph edges
        edge_to_auth (dict): Mapping of graph edges to authorization information
    
    Example:
        >>> result = await pycaber.stream_process(data_generator())
        >>> print(f"SHA256: {result.sha256.hex()}")
        >>> print(f"Found {len(result.fingerprints)} content chunks")
        >>> if result.json:
        ...     print(f"Extracted {len(result.json)} JSON values")
        >>> if result.obo:
        ...     print(f"OBO user: {result.obo.get('obo.user.name')}")
    """
    __init__: Any
    edge_to_auth: Any
    fingerprints: Any
    index_filename: Any
    input_blocks: Any
    json: Any
    nmer_to_edges: Any
    obo: Any
    sha256: Any

class Fingerprinter:
    """
    Content fingerprinting processor for various chunking algorithms
    
    Provides methods for content-defined chunking using different algorithms.
    Each method processes data from generators/files and returns fingerprint mappings.
    
    Example:
        >>> import pycaber
        >>> pycaber.configure()
        >>> fingerprinter = pycaber.Fingerprinter()
        >>> def data_gen():
        ...     yield b"some content here that will be chunked"
        >>> result = fingerprinter.ae(data_gen())
        >>> for hash_int, chunk_bytes in result.items():
        ...     print(f"Hash: {hash_int}, Chunk size: {len(chunk_bytes)}")
    """
    __init__: Any
    ae: Any

class Index:
    """
    Wrapper for PyCQF that automatically uses global configuration
    
    Provides a Python interface to Counting Quotient Filter (CQF) functionality
    with automatic configuration from global settings. CQFs are space-efficient
    probabilistic data structures for storing and querying large sets of fingerprints.
    
    Note:
        This class is only available when compiled with the 'rkcqf' feature.
        All operations automatically use the key_bits, value_bits, and other settings
        from the global configuration.
    
    Example:
        >>> import pycaber
        >>> pycaber.configure()  # Sets up global CQF configuration
        >>> index = pycaber.Index()
        >>> hash_list = [12345, 67890, 11111]
        >>> index.from_hashlist("myindex.ccqf", hash_list)
        >>> metadata = index.metadata()
    """
    __init__: Any
    append_hashlist: Any
    close_file: Any
    count_key_value: Any
    dump_hashdict: Any
    filename: Any
    from_hashlist: Any
    metadata: Any
    read_file: Any
