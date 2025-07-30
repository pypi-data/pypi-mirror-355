import os
import argparse
import requests
import urllib3
import shutil
import re
from .llamaparse import parse_document_file, parse_document_to_markdown, extract_markdown_from_json
import json
import sys
from urllib.parse import urlparse

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define the download directory as a constant
DEFAULT_DOWNLOAD_DIR = "downloaded_documents"

def is_url(path):
    """
    Check if the given path is a URL
    
    Args:
        path: The path to check
        
    Returns:
        bool: True if the path is a URL, False otherwise
    """
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except:
        return False


def download_document(url, output_path):
    """
    Download a document from a URL and save it to the specified path.
    First tries a simple direct download, then falls back to browser simulation if needed.
    
    Args:
        url: URL of the document to download
        output_path: Path to save the downloaded document
    
    Returns:
        True if successful, False otherwise
    """
    # STEP 1: Try the simple direct approach first
    try:
        print("Step 1: Trying simple direct download...")
        # Send GET request to the URL with SSL verification disabled
        response = requests.get(url, verify=False)
        
        # Check if the request was successful
        if response.status_code == 200 and len(response.content) > 1000:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            # Write the content to a file
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Document downloaded successfully to {output_path}")
            return True
            
    except Exception as e:
        print(f"Simple download failed: {e}")
    
    # STEP 2: If simple approach failed, try browser simulation
    print("Step 2: Trying browser simulation approach...")
    
    try:
        # Fix URL by properly handling backslashes and ensuring proper path structure
        url = url.replace('\\', '/')
        
        # Make sure there's a slash between the directory and filename
        if 'UploadedFiles' in url and not '/UploadedFiles/' in url:
            url = url.replace('/UploadedFiles', '/UploadedFiles/')
        
        print(f"Attempting to download from: {url}")
        
        # Create a session to persist cookies
        session = requests.Session()
        
        # Browser-like headers to mimic a real browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': re.sub(r'/[^/]*$', '/', url),  # Set referer to the base URL path
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # First visit the base website to get cookies
        base_url = re.match(r'(https?://[^/]+)', url).group(1)
        print(f"Visiting base URL to establish session: {base_url}")
        session.get(base_url, headers=headers, verify=False)
        
        # Now try to download the file with the session cookies
        print("Downloading file with established session...")
        response = session.get(url, headers=headers, verify=False, allow_redirects=True)
        
        # Check if the request was successful
        if response.status_code == 200 and len(response.content) > 1000:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            # Write the content to a file
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Document downloaded successfully to {output_path}")
            return True
        else:
            print(f"Failed to download document. Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Browser simulation failed: {e}")
        return False


def delete_download_folder(folder_path):
    """
    Delete the download folder and all its contents
    
    Args:
        folder_path: Path to the folder to delete
    """
    try:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            print(f"Successfully deleted folder: {folder_path}")
        else:
            print(f"Folder does not exist: {folder_path}")
    except Exception as e:
        print(f"Error deleting folder {folder_path}: {e}")

def parse_to_document_link(document_link, download_path=None, json_output=None, md_output=None, 
                       parsing_instruction=None, format="json", extract_only=False,
                       llama_api_key=None, vendor_model=None, delete_downloads=True):
    """
    Process a document (from URL or local path) with LlamaParse
    
    Args:
        document_link: URL or local path of the document to process
        download_path: Path to save the downloaded document (default: derived from URL)
        json_output: Path to save the JSON output (default: derived from download_path)
        md_output: Path to save the markdown output (default: derived from download_path)
        parsing_instruction: Custom parsing instruction for LlamaParse
        format: Output format ('json' or 'md')
        extract_only: If True, only extract markdown from an existing JSON file
        llama_api_key: API key for LlamaParse
        vendor_model: Model to use for parsing (e.g., 'anthropic-sonnet-3.7')
        delete_downloads: If True, delete downloaded documents after processing (default: True)
        
    Returns:
        If successful: Tuple containing (True, markdown_content)
        If failed: Tuple containing (False, None)
    """
    # Create the download directory if it doesn't exist
    os.makedirs(DEFAULT_DOWNLOAD_DIR, exist_ok=True)
    
    # Ensure we have the API key
    api_key = llama_api_key or LLAMA_API_KEY
    if not api_key:
        print("LLAMA_API_KEY is required. Set it as an environment variable or pass it to the function.")
        return False, None
        
    # Check if document_link is a URL or local file path
    is_document_url = is_url(document_link)
    
    # If it's a local file, set the input path directly
    if not is_document_url and os.path.exists(document_link):
        input_path = document_link
        print(f"Using local file: {input_path}")
    else:
        # Determine download path if not specified (for URLs)
        if not download_path:
            # Extract filename from URL and use it as download path
            filename = os.path.basename(document_link.split('?')[0])
            download_path = os.path.join(DEFAULT_DOWNLOAD_DIR, filename if filename else "downloaded_document.pdf")
        elif not os.path.dirname(download_path):
            # If only a filename was provided without a directory, put it in the default download directory
            download_path = os.path.join(DEFAULT_DOWNLOAD_DIR, download_path)
        
        # Download the document if it's a URL and not in extract-only mode
        if is_document_url and not extract_only:
            download_success = download_document(document_link, download_path)
            if not download_success:
                return False, None
        
        input_path = download_path
    
    # If extract-only mode is requested, extract markdown from an existing JSON file
    if extract_only and input_path.endswith('.json'):
        # Determine default markdown output path if not provided
        if not md_output:
            md_output = os.path.join(DEFAULT_DOWNLOAD_DIR, os.path.splitext(os.path.basename(input_path))[0] + ".md")
        
        markdown = extract_markdown_from_json(input_path, md_output)
        
        # Read and return the markdown content
        if markdown is not None:
            try:
                with open(md_output, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                    
                # Delete DEFAULT_DOWNLOAD_DIR if delete_downloads is True
                if delete_downloads:
                    delete_download_folder(DEFAULT_DOWNLOAD_DIR)
                    
                return True, md_content
            except Exception as e:
                print(f"Error reading markdown file: {e}")
                return False, None
        return False, None
    
    # Set input path for LlamaParse
    print(f"Sending document directly to LlamaParse without format checks or conversion...")
    
    # Determine default output paths if not provided
    if not json_output:
        json_basename = os.path.splitext(os.path.basename(input_path))[0] + ".json"
        json_output = os.path.join(DEFAULT_DOWNLOAD_DIR, json_basename)
    
    if not md_output:
        md_basename = os.path.splitext(os.path.basename(input_path))[0] + ".md"
        md_output = os.path.join(DEFAULT_DOWNLOAD_DIR, md_basename)
    
    # Process to both formats using imported function
    success = parse_document_to_markdown(
        file_path=input_path,
        json_output_path=json_output,
        md_output_path=md_output,
        parsing_instruction=parsing_instruction,
        api_key=api_key,
        vendor_model=vendor_model
    )
    
    if success:
        try:
            # Read and return the markdown content
            with open(md_output, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Delete DEFAULT_DOWNLOAD_DIR if delete_downloads is True
            if delete_downloads:
                delete_download_folder(DEFAULT_DOWNLOAD_DIR)
            
            return True, md_content
        except Exception as e:
            print(f"Error reading markdown file: {e}")
            return False, None
    
    return False, None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download a document from S3 and process it with LlamaParse"
    )
    
    # Create argument groups
    s3_group = parser.add_argument_group("S3 Document Options")
    parse_group = parser.add_argument_group("LlamaParse Options")
    api_group = parser.add_argument_group("API Credentials")
    
    # S3 document arguments
    s3_group.add_argument("--s3-url", required=True, help="S3 URL of the document to download and process")
    s3_group.add_argument("--download-path", help=f"Path to save the downloaded document (default: {DEFAULT_DOWNLOAD_DIR}/filename)")
    
    # LlamaParse arguments
    parse_group.add_argument("--instruction", "-i", help="Custom parsing instruction for LlamaParse")
    parse_group.add_argument("--format", "-f", choices=["json", "md"], default="json", 
                        help="Result format preference (json or md, default: json) - Both formats will be generated")
    parse_group.add_argument("--json-output", help=f"Path to save the JSON output (default: {DEFAULT_DOWNLOAD_DIR}/filename.json)")
    parse_group.add_argument("--md-output", "-m", help=f"Path to save the markdown output (default: {DEFAULT_DOWNLOAD_DIR}/filename.md)")
    parse_group.add_argument("--extract-only", action="store_true", 
                        help="Only extract markdown from an existing JSON file (no download or parsing)")
    
    # API credentials arguments
    api_group.add_argument("--llama-api-key", help="API key for LlamaParse")
    api_group.add_argument("--vendor-model", help="Model to use for parsing (e.g., 'anthropic-sonnet-3.7')")
   
    
    args = parser.parse_args()
    
    # Process the document
    success, md_content = parse_to_document_link(
        document_link=args.document_link,
        download_path=args.download_path,
        json_output=args.json_output,
        md_output=args.md_output,
        parsing_instruction=args.instruction,
        format=args.format,
        extract_only=args.extract_only,
        llama_api_key=args.llama_api_key,
        vendor_model=args.vendor_model,
    )
    
    if success:
        print("Document processing completed successfully.")
        # Always print markdown content without requiring a flag
        if md_content:
            print("\nMarkdown Content:")
            print(md_content)
        exit(0)
    else:
        print("Document processing failed.")
        exit(1) 