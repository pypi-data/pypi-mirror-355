import os
import requests
import json
import time
import mimetypes
from typing import Optional, Tuple, Dict, Any, Union
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API keys from environment
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")  # For Anthropic or other model provider
VENDOR_MODEL = os.getenv("VENDOR_MODEL")

class LlamaParseClient:
    """Simple client for LlamaParse API to parse PDFs and images and get results"""
    
    def __init__(self, llama_api_key: Optional[str] = None,vendor_model: str = VENDOR_MODEL):
        """Initialize the LlamaParse client with API keys"""
        self.llama_api_key = llama_api_key or LLAMA_API_KEY
        self.vendor_model = vendor_model or VENDOR_MODEL
        
        if not self.llama_api_key:
            raise ValueError("LLAMA_API_KEY is required. Set it as an environment variable or pass it to the constructor.")
        
        
    def parse_document(self, file_path: str, parsing_instruction: Optional[str] = None, 
                  max_retries: int = 20, retry_delay: int = 5, 
                  result_format: str = "json") -> Tuple[bool, Optional[Union[str, Dict[str, Any]]]]:
        """
        Parse a PDF or image file using LlamaParse and return the result
        
        Args:
            file_path: Path to the PDF or image file
            parsing_instruction: Optional instructions for parsing
            max_retries: Maximum number of retries for result retrieval
            retry_delay: Delay in seconds between retries
            result_format: Format of the result ('json' or 'md')
            
        Returns:
            Tuple of (success status, result content or None)
        """
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            return False, None
            
        file_name = os.path.basename(file_path)
        print(f"Submitting '{file_name}' to LlamaParse...")
        
        # Submit parsing job
        job_id = self._submit_parsing_job(file_path, parsing_instruction)
        if not job_id:
            print(f"Failed to submit parsing job for {file_name}")
            return False, None
            
        print(f"Job submitted successfully. Job ID: {job_id}")
        print(f"Waiting for parsing results...")
        
        # Initial wait before first retrieval attempt
        time.sleep(10)  # Wait 10 seconds initially
        
        # Retrieve result
        for attempt in range(max_retries):
            print(f"Attempt {attempt + 1}/{max_retries} to retrieve {result_format} results...")
            
            if result_format == "json":
                result = self._get_json_result(job_id)
            else:
                result = self._get_markdown_result(job_id)
            
            if result is not None:
                print(f"Successfully retrieved {result_format} for {file_name}")
                return True, result
                
            if attempt < max_retries - 1:
                print(f"Waiting {retry_delay} seconds before next attempt...")
                time.sleep(retry_delay)  # Consistent 10-second wait
        
        print(f"Failed to retrieve {result_format} results after {max_retries} attempts")
        
        # As a fallback, try the other format
        fallback_format = "md" if result_format == "json" else "json"
        print(f"Trying fallback format: {fallback_format}")
        
        if fallback_format == "json":
            result = self._get_json_result(job_id)
        else:
            result = self._get_markdown_result(job_id)
            
        if result is not None:
            print(f"Successfully retrieved {fallback_format} for {file_name} (fallback)")
            return True, result
            
        return False, None
        
    def _submit_parsing_job(self, file_path: str, parsing_instruction: Optional[str] = None) -> Optional[str]:
        """Submit document parsing job and return job ID if successful"""
        upload_url = "https://api.cloud.llamaindex.ai/api/parsing/upload"
        headers = {
            "Authorization": f"Bearer {self.llama_api_key}",
            "accept": "application/json"
        }
        
        # Default parsing instruction if none provided
        if not parsing_instruction:
            parsing_instruction = """
Extract the text content from this document maintaining headers, paragraphs, and section structure. 

If it's a table, keep the layout intact. If it's an image, diagram, or picture, provide a detailed description.

Ensure everything about the document is included in the generated response:
* All text paragraphs, lists, etc.
* Tables (formatted as HTML) and Figure Descriptions appearing between two section headers are part of the *first* section's content.

Extract and describe content elements:
* Extract all textual content. Maintain paragraph structure.
* Represent tables using standard HTML tags (<table>, <thead>, <tbody>, <tr>, <th>, <td>). Include table content accurately.
* For figures, images, or diagrams: Describe based on visual analysis and context from surrounding text using the format "Figure Description: [Your detailed description here]".
  * Identify Type: Start by stating the type of visual (e.g., "Flowchart:", "Bar graph:", "Photograph:", "Technical drawing:", "Illustration:").
  * Describe Content Thoroughly: Detail the main subject, all visible text including labels, annotations, and data points, mention exact data, trends, or key comparisons shown, symbols and their meanings within the context, relationships depicted (e.g., connections in flowcharts, hierarchies in diagrams), significant colors if they convey meaning, and the overall composition or layout. For photos, describe the scene, objects, people (if depicted, describe neutrally and factually based on visual cues), and setting realistically and completely.
  * Be Specific & Accurate: Ensure all details present in the visual are described.
  * Transcribe text within the image exactly as it appears. Use quantifiable descriptions where appropriate (e.g., "shows a 3-stage process", "contains 5 columns labeled...").
* Crucially, do NOT treat figure captions or titles as section headers. They are part of the figure's descriptive context or textual content.
"""
        
        file_name = os.path.basename(file_path)
        
        try:
            multipart_data = {
                'parsing_instruction': parsing_instruction,
                'invalidate_cache': 'true',
                'use_vendor_multimodal_model': 'false',
                'vendor_multimodal_model_name': self.vendor_model,
                'output_tables_as_html': 'true',
                'parse_mode': 'parse_page_with_lvm'
            }
            
            # Determine file MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                # Default to PDF if can't determine
                if file_path.lower().endswith('.pdf'):
                    mime_type = 'application/pdf'
                elif file_path.lower().endswith(('.jpg', '.jpeg')):
                    mime_type = 'image/jpeg'
                elif file_path.lower().endswith('.png'):
                    mime_type = 'image/png'
                else:
                    mime_type = 'application/octet-stream'
            
            with open(file_path, 'rb') as f:
                files_payload = {
                    'file': (file_name, f, mime_type)
                }
                for key, value in multipart_data.items():
                    files_payload[key] = (None, value)
                
                print(f"Sending request to LlamaParse API for {mime_type} file...")
                response = requests.post(upload_url, headers=headers, files=files_payload)
                print(f"API response status code: {response.status_code}")
            
            if response.status_code == 200:
                response_json = response.json()
                job_id = response_json.get("id")
                if job_id:
                    return job_id
                else:
                    print(f"API response OK, but 'id' key not found: {response_json}")
            else:
                print(f"API submission failed: {response.status_code} - {response.text}")
            
        except Exception as e:
            print(f"Error submitting parsing job: {e}")
        
        return None
    
    def _get_markdown_result(self, job_id: str) -> Optional[str]:
        """Get markdown result from a completed parsing job"""
        result_url = f"https://api.cloud.llamaindex.ai/api/parsing/job/{job_id}/result/md"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.llama_api_key}"
        }
        
        try:
            print(f"Requesting markdown from: {result_url}")
            response = requests.get(result_url, headers=headers)
            print(f"Markdown response status: {response.status_code}")
            
            if response.status_code == 200:
                # The response should be the markdown text directly
                return response.text
            elif response.status_code == 404:
                print(f"Markdown result not found or job {job_id} not ready yet (404).")
            elif response.status_code == 401:
                print(f"Unauthorized (401) when retrieving markdown for job {job_id}.")
                return None
            else:
                print(f"Failed to retrieve markdown: {response.status_code}")
                print(f"Response text: {response.text[:200]}...")
                
        except Exception as e:
            print(f"Error retrieving markdown result: {e}")
            
        return None
        
    def _get_json_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get JSON result from a completed parsing job"""
        result_url = f"https://api.cloud.llamaindex.ai/api/parsing/job/{job_id}/result/json"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.llama_api_key}"
        }
        
        try:
            print(f"Requesting JSON from: {result_url}")
            response = requests.get(result_url, headers=headers)
            print(f"JSON response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    print("Received response is not valid JSON")
                    print(f"Raw response: {response.text[:200]}...")
                    return None
            elif response.status_code == 404:
                print(f"JSON result not found or job {job_id} not ready yet (404).")
            elif response.status_code == 401:
                print(f"Unauthorized (401) when retrieving JSON for job {job_id}.")
                return None
            else:
                print(f"Failed to retrieve JSON: {response.status_code}")
                print(f"Response text: {response.text[:200]}...")
                
        except Exception as e:
            print(f"Error retrieving JSON result: {e}")
            
        return None

# Alias for backward compatibility
parse_pdf = parse_document = lambda file_path, output_path=None, parsing_instruction=None, result_format="json", api_key=None, vendor_model=None: parse_document_file(file_path, output_path, parsing_instruction, result_format, api_key, vendor_model)

def parse_document_file(file_path: str, output_path: Optional[str] = None, 
             parsing_instruction: Optional[str] = None,
             result_format: str = "json",
             api_key: Optional[str] = None,
             vendor_model: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[Union[str, Dict[str, Any]]]]:
    """
    Parse a document (PDF or image) using LlamaParse and save the result
    
    Args:
        file_path: Path to the document file (PDF, JPEG, PNG, etc.)
        output_path: Optional path to save the result (if None, will use file name + extension)
        parsing_instruction: Optional custom parsing instruction
        result_format: Format of the result ('json' or 'md')
        api_key: Optional API key for LlamaParse
        vendor_model: Optional model to use for parsing
        
    Returns:
        Tuple of (success status, output path or None, result data or None)
    """
    # Get client
    client = LlamaParseClient(llama_api_key=api_key, vendor_model=vendor_model)
    
    # Parse document
    success, result = client.parse_document(file_path, parsing_instruction, result_format=result_format)
    
    if success and result:
        # Determine output path if not specified
        if not output_path:
            base_name = os.path.splitext(file_path)[0]
            ext = ".json" if result_format == "json" or isinstance(result, dict) else ".md"
            output_path = f"{base_name}{ext}"
        
        # Save result to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                if isinstance(result, dict):
                    json.dump(result, f, indent=2, ensure_ascii=False)
                else:
                    f.write(result)
            print(f"Result saved to: {output_path}")
            return True, output_path, result
        except Exception as e:
            print(f"Error saving result to file: {e}")
    
    return False, None, None

def extract_markdown_from_json(json_file_path: str, output_md_path: Optional[str] = None) -> Optional[str]:
    """
    Extract markdown content from a LlamaParse JSON result file
    
    Args:
        json_file_path: Path to the JSON file containing LlamaParse results
        output_md_path: Optional path to save the markdown output (if None, will not save to file)
        
    Returns:
        Extracted markdown content or None if extraction failed
    """
    try:
        # Read and parse the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract markdown content from each page
        if "pages" not in data:
            print(f"Error: JSON file {json_file_path} does not contain 'pages' key")
            return None
            
        # Combine markdown from all pages
        markdown_content = ""
        for i, page in enumerate(data["pages"]):
            if "md" in page:
                if i > 0:
                    markdown_content += "\n\n"  # Add separator between pages
                
                # Add centered page number before content
                page_number = page.get("page", i+1)  # Use page number from JSON or fallback to index+1
                page_separator = f"\n\n*************** Page {page_number} ***************\n\n"
                markdown_content += page_separator + page["md"]
            else:
                print(f"Warning: Page {i+1} does not contain markdown content")
        
        if not markdown_content:
            print(f"Error: No markdown content found in {json_file_path}")
            return None
            
        # Save to file if requested
        if output_md_path:
            try:
                with open(output_md_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                print(f"Markdown content extracted and saved to: {output_md_path}")
            except Exception as e:
                print(f"Error saving markdown to file {output_md_path}: {e}")
                
        return markdown_content
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file {json_file_path}: {e}")
    except FileNotFoundError:
        print(f"Error: File {json_file_path} not found")
    except Exception as e:
        print(f"Unexpected error processing {json_file_path}: {e}")
        
    return None

def parse_document_to_markdown(file_path: str, json_output_path: Optional[str] = None, 
                         md_output_path: Optional[str] = None,
                         parsing_instruction: Optional[str] = None,
                         api_key: Optional[str] = None,
                         vendor_model: Optional[str] = None) -> bool:
    """
    Process a document file (PDF or image) through LlamaParse and extract its content as both JSON and markdown
    
    Args:
        file_path: Path to the document file to process (PDF, JPEG, PNG, etc.)
        json_output_path: Optional path to save the JSON result
        md_output_path: Optional path to save the markdown result
        parsing_instruction: Optional custom parsing instruction
        api_key: Optional API key for LlamaParse
        vendor_model: Optional model to use for parsing
        
    Returns:
        True if successful, False otherwise
    """
    print(f"Processing document to extract both JSON and markdown: {file_path}")
    
    # Step 1: Parse document to JSON
    success, json_path, json_result = parse_document_file(
        file_path=file_path, 
        output_path=json_output_path,
        parsing_instruction=parsing_instruction,
        result_format="json",
        api_key=api_key,
        vendor_model=vendor_model
    )
    
    if not success or not json_path or not json_result:
        print(f"Failed to parse document to JSON: {file_path}")
        return False
        
    print(f"Successfully parsed document to JSON: {json_path}")
    
    # Step 2: Extract markdown from JSON result
    if isinstance(json_result, dict):
        # If we have the JSON result in memory, extract markdown from it directly
        if "pages" in json_result:
            markdown_content = ""
            for i, page in enumerate(json_result["pages"]):
                if "md" in page:
                    if i > 0:
                        markdown_content += "\n\n"  # Add separator between pages
                    
                    # Add centered page number before content
                    page_number = page.get("page", i+1)  # Use page number from JSON or fallback to index+1
                    page_separator = f"\n\n*************** Page {page_number} ***************\n\n"
                    markdown_content += page_separator + page["md"]
            
            # Determine markdown output path if not specified
            if not md_output_path:
                md_output_path = os.path.splitext(file_path)[0] + ".md"
                
            # Save markdown to file
            try:
                with open(md_output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                print(f"Markdown content extracted and saved to: {md_output_path}")
                return True
            except Exception as e:
                print(f"Error saving markdown to file {md_output_path}: {e}")
                return False
    
    # Fall back to extracting from the saved JSON file if needed
    markdown = extract_markdown_from_json(json_path, md_output_path)
    return markdown is not None

# For backward compatibility
parse_pdf_to_markdown = parse_document_to_markdown

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Parse documents (PDF, JPEG, PNG) using LlamaParse or extract markdown from JSON results")
    
    # Create argument groups
    parse_group = parser.add_argument_group("Document Parsing Options")
    extract_group = parser.add_argument_group("Markdown Extraction Options")
    api_group = parser.add_argument_group("API Credentials")
    
    # Document parsing arguments
    parse_group.add_argument("--file", help="Path to the document file to parse (PDF, JPEG, PNG)")
    parse_group.add_argument("--output", "-o", help="Path to save the output (default: same as input with appropriate extension)")
    parse_group.add_argument("--instruction", "-i", help="Custom parsing instruction")
    parse_group.add_argument("--format", "-f", choices=["json", "md"], default="json", 
                        help="Result format (json or md, default: json)")
    parse_group.add_argument("--to-md", help="Parse document and extract markdown in one step. Provide the document path.", metavar="FILE_PATH")
    parse_group.add_argument("--json-output", help="Path to save the JSON output when using --to-md (default: input name with .json extension)")
    parse_group.add_argument("--md-output", "-m", help="Path to save the markdown output (default: input name with .md extension)")
    
    # Markdown extraction arguments
    extract_group.add_argument("--extract-md", "-e", help="Extract markdown from an existing JSON result file")
    
    # API credentials arguments
    api_group.add_argument("--llama-api-key", help="API key for LlamaParse")
    api_group.add_argument("--vendor-model", help="Model to use for parsing (e.g., 'anthropic-sonnet-3.7')")
    
    # For backward compatibility
    parse_group.add_argument("--pdf", help="Path to the PDF file to parse (same as --file)")
    
    args = parser.parse_args()
    
    # Process file to both JSON and markdown in one step
    input_file = args.to_md or args.file or args.pdf
    
    if args.to_md:
        if not os.path.exists(args.to_md):
            print(f"Error: File not found at {args.to_md}")
            exit(1)
            
        # Use provided API key or fall back to environment variable
        api_key = args.llama_api_key or LLAMA_API_KEY
        vendor_model = args.vendor_model or VENDOR_MODEL
            
        if not api_key:
            print("ERROR: LLAMA_API_KEY is not provided and not set in environment.")
            print("Set it in your environment, in a .env file, or provide it with --llama-api-key.")
            exit(1)
       
        success = parse_document_to_markdown(
            file_path=args.to_md,
            json_output_path=args.json_output,
            md_output_path=args.md_output,
            parsing_instruction=args.instruction,
            api_key=api_key,
            vendor_model=vendor_model
        )
        
        if success:
            print("Document processed to both JSON and markdown successfully.")
            exit(0)
        else:
            print("Failed to process document to markdown.")
            exit(1)
    
    # Handle markdown extraction from JSON if requested
    elif args.extract_md:
        md_output = args.md_output
        if not md_output and args.extract_md.endswith('.json'):
            # Default output filename: replace .json with .md
            md_output = os.path.splitext(args.extract_md)[0] + '.md'
            
        markdown = extract_markdown_from_json(args.extract_md, md_output)
        if markdown:
            exit(0)
        else:
            exit(1)
    
    # Otherwise, parse a file to a single format
    elif input_file:
        # Use provided API key or fall back to environment variable
        api_key = args.llama_api_key or LLAMA_API_KEY
        vendor_model = args.vendor_model or VENDOR_MODEL
        
        if not api_key:
            print("ERROR: LLAMA_API_KEY is not provided and not set in environment.")
            print("Set it in your environment, in a .env file, or provide it with --llama-api-key.")
            exit(1)
        
        success, _, _ = parse_document_file(
            input_file, 
            args.output, 
            args.instruction, 
            args.format,
            api_key=api_key,
            vendor_model=vendor_model
        )
        
        if success:
            print("Document parsing completed successfully.")
            exit(0)
        else:
            print("Document parsing failed.")
            exit(1)
    
    else:
        parser.print_help()
        print("\nError: You must either specify a document file to parse with --file or --to-md, or a JSON file to extract markdown from with --extract-md")
        exit(1)