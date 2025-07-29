from pathlib import Path
from datetime import datetime
import boto3
import logging
from dotenv import load_dotenv
import os
import time
import re
from bs4 import BeautifulSoup
from io import BytesIO
import urllib.parse
import tempfile

load_dotenv()



# AWS S3 Configuration
AWS_REGION_AWS = os.getenv("AWS_REGION")
ACCESS_KEY_S3 = os.getenv("S3_ACCESS_KEY")
SECRET_KEY_S3 = os.getenv("S3_SECRET_KEY")
BUCKET_ETL_PROD_S3 = os.getenv("S3_BUCKET_ETL_PROD")

print(AWS_REGION_AWS, ACCESS_KEY_S3, SECRET_KEY_S3, BUCKET_ETL_PROD_S3)

# Initialize S3 client
s3_client = boto3.client(
    's3',
    region_name=AWS_REGION_AWS,
    aws_access_key_id=ACCESS_KEY_S3,
    aws_secret_access_key=SECRET_KEY_S3
)

print(s3_client)

logger = logging.getLogger(__name__)

# S3 configuration matching the working code
bucket_name = BUCKET_ETL_PROD_S3
base_url = f'https://s3.{AWS_REGION_AWS}.amazonaws.com/{bucket_name}'

def timestamped_filename(prefix: str, ext: str = ".png") -> Path:
    """
    Returns Path("<cwd>/screenshots/{prefix}_{UTC_ISO}.png"),
    creating the directory if needed.
    """
    base = Path.cwd() / "screenshots_shippalm"
    base.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return base / f"{prefix}_{ts}{ext}"

def upload_screenshot_to_s3(screenshot_bytes: bytes, vessel_name: str, screenshot_type: str = "urgent") -> str:
    """
    Upload screenshot bytes directly to S3 and return the S3 URL using the working approach.
    """
    try:
        logger.info(f"Starting direct S3 upload for screenshot")
        logger.info(f"S3 Bucket: {bucket_name}")
        logger.info(f"Screenshot size: {len(screenshot_bytes)} bytes")
        
        # Generate timestamp for unique filename
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        
        # Use path structure you have permissions for (syia_documents instead of chat_screenshot)
        document_title = f"{vessel_name}_{screenshot_type}_{ts}"
        object_name = f"chat_screenshot/shippalm_screenshots/{document_title}.png"
        
        logger.info(f"S3 object name: {object_name}")
        
        # Use your working URL encoding approach
        encoded_object_name = urllib.parse.quote(object_name, safe='/')
        s3_url = f"{base_url}/{encoded_object_name}"
        
        # Create temporary file to use with upload_file (matching your working approach)
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_file.write(screenshot_bytes)
            temp_file_path = temp_file.name
        
        try:
            # Upload using the same method as your working code
            logger.info("Uploading screenshot to S3...")
            s3_client.upload_file(
                Filename=temp_file_path,
                Bucket=bucket_name,
                Key=object_name,
                ExtraArgs={'ContentType': 'image/png'}
            )
            
            logger.info(f"✅ Successfully uploaded to {s3_url}")
            return s3_url
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"❌ Failed to upload screenshot to S3: {str(e)}")
        return f"Error uploading to S3: {str(e)}"

def html_table_to_markdown(html_content: str) -> str:
    """
    Convert HTML table content to markdown format.
    
    Args:
        html_content (str): HTML content containing table(s)
        
    Returns:
        str: Markdown formatted table content
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        markdown_content = []
        
        # Find all tables in the HTML
        tables = soup.find_all('table')
        
        if not tables:
            logger.warning("No tables found in HTML content")
            return "No table data found"
        
        for table_idx, table in enumerate(tables):
            if table_idx > 0:
                markdown_content.append("\n---\n")  # Separator between tables
            
            rows = table.find_all('tr')
            if not rows:
                continue
                
            # Process header row (first row)
            header_row = rows[0]
            headers = []
            for cell in header_row.find_all(['th', 'td']):
                cell_text = cell.get_text(strip=True)
                headers.append(cell_text if cell_text else "")
            
            if headers:
                # Create markdown header
                markdown_content.append("| " + " | ".join(headers) + " |")
                markdown_content.append("| " + " | ".join(["---"] * len(headers)) + " |")
            
            # Process data rows
            for row in rows[1:] if len(rows) > 1 else rows:
                cells = []
                for cell in row.find_all(['td', 'th']):
                    cell_text = cell.get_text(strip=True)
                    # Clean up cell text and escape pipe characters
                    cell_text = cell_text.replace('|', '\\|').replace('\n', ' ').replace('\r', '')
                    cells.append(cell_text if cell_text else "")
                
                if cells:
                    # Ensure we have the same number of cells as headers
                    while len(cells) < len(headers):
                        cells.append("")
                    markdown_content.append("| " + " | ".join(cells[:len(headers)]) + " |")
        
        result = "\n".join(markdown_content)
        logger.info("Successfully converted HTML table to markdown")
        return result
        
    except Exception as e:
        logger.error(f"Error converting HTML to markdown: {str(e)}")
        return f"Error converting table to markdown: {str(e)}"

def get_artifact(function_name: str, url: str):
    """
    Handle get artifact tool using updated artifact format
    """
    artifact = {
        "id": "msg_browser_ghi7894",
        "parentTaskId": "task_japan_itinerary_7d8f9g",
        "timestamp": int(time.time()),
        "agent": {
            "id": "agent_siya_browser",
            "name": "SIYA",
            "type": "qna"
        },
        "messageType": "action",
        "action": {
            "tool": "browser",
            "operation": "browsing",
            "params": {
                "url": url,
                "pageTitle": f"Tool response for {function_name}",
                "visual": {
                    "icon": "browser",
                    "color": "#2D8CFF"
                },
                "stream": {
                    "type": "vnc",
                    "streamId": "stream_browser_1",
                    "target": "browser"
                }
            }
        },
        "content": f"Viewed page: {function_name}",
        "artifacts": [
            {
                "id": "artifact_webpage_1746018877304_994",
                "type": "browser_view",
                "content": {
                    "url": url,
                    "title": function_name,
                    "screenshot": "",
                    "textContent": f"Observed output of cmd `{function_name}` executed:",
                    "extractedInfo": {}
                },
                "metadata": {
                    "domainName": "example.com",
                    "visitTimestamp": int(time.time() * 1000),
                    "category": "web_page"
                }
            }
        ],
        "status": "completed"
    }
    return artifact




