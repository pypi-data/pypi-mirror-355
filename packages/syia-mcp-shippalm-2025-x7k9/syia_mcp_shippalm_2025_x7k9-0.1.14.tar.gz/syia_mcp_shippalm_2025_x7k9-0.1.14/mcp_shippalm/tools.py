# tools.py

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from .utils import  upload_screenshot_to_s3, get_artifact, html_table_to_markdown
from asyncio import sleep
import time
from playwright.async_api import Download
from playwright.async_api import TimeoutError as PwTimeout
from .mcp_instance import mcp
from .tool_schema import tool_definitions
import mcp.types as types
import json
from pymongo import MongoClient, errors
from typing import List, Dict, Any



# ── MCP instance & logger ─────────────────────────────────────────────
logger = logging.getLogger("mcp_shippalm")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[tools] %(message)s"))
    logger.addHandler(handler)

# ── Credentials ───────────────────────────────────────────────────────────
load_dotenv()
EMAIL = os.getenv("SHIPPALM_EMAIL", "")
PASSWORD = os.getenv("SHIPPALM_PASSWORD", "")


server_tools = tool_definitions


#------ Tool Registration ------------------------------------------------------------


def register_tools():
    @mcp.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return server_tools

    @mcp.call_tool()
    async def handle_call_tool(name: str, arguments: dict):
        
        if name == "urgent_requisition_from_shippalm":
            return await urgent_requisition_from_shippalm(**arguments)
        elif name == "expired_certificate_from_shippalm":
            return await expired_certificate_from_shippalm(**arguments)
        elif name == "critical_spares_inventory_from_shippalm":
            return await critical_spares_inventory_from_shippalm(**arguments)
        elif name == "position_book_report_from_shippalm":
            return await position_book_report_from_shippalm(**arguments)
        elif name == "purchase_order_data_from_shippalm":
            return await purchase_order_data_from_shippalm(**arguments)
        elif name == "purchase_requisition_order_data_from_shippalm":
            return await purchase_requisition_order_data_from_shippalm(**arguments)
  
      
        else:
            raise ValueError(f"Unknown tool: {name}")



# DOC LIST
norden_doc_list =['SDK', 'NSSM']
synergy_group_doc_list = ['SMGGH']
# synergy_marine_group_doc_list = ['SMGGH']

# ─────────────────────────────────────────────────────────────────────────────
# Urgent Requisition
# ─────────────────────────────────────────────────────────────────────────────


async def _urgent_requisition_automation(vessel_name: str, shippalmDoc: str) -> dict:
    # Determine base URL based on doc
    if shippalmDoc in norden_doc_list:
        base_url = f"https://shippalmv3.norden-synergy.com/?company={shippalmDoc}"
    elif shippalmDoc in synergy_group_doc_list:
        base_url = f"https://shippalmv3.synergygroup.sg/?company={shippalmDoc}"
    else:
        base_url = f"https://shippalmv3.synergymarinegroup.com/?company={shippalmDoc}"
        
    # Microsoft SSO login URL remains the same
    login_url = (
        "https://login.microsoftonline.com/common/wsfed?"
        "wa=wsignin1.0&wtrealm=https%3a%2f%2fshippalmv3.synergymarinegroup.com"
        "&wreply=https%3a%2f%2fshippalmv3.synergymarinegroup.com%2fSignIn%3fReturnUrl%3d%252f"
        "&sso_reload=true"
    )

    # Initialize result dictionary
    result = {
        "content": [],
        "s3_url": None
    }

    async with async_playwright() as p:
        logger.info("launch browser (headless)")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width":1380, "height":900})
        page = await context.new_page()

        try:
            # 1. Login via Microsoft SSO
            logger.info("goto login URL")
            await page.goto(login_url, timeout=60000)

            # Optional account tile
            tile = page.locator(f'div[data-test-id="accountTile"] >> text="{EMAIL}"')
            if await tile.count():
                await tile.first.click()

            # Email input
            await page.fill('input[type="email"], input[name="loginfmt"]', EMAIL)
            await page.click('button[type="submit"], input[type="submit"][value="Next"]')
            # Password input
            await page.fill('input[type="password"]', PASSWORD)
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_load_state("networkidle", timeout=60000)

            # After successful login, navigate to the specific company URL
            logger.info(f"Navigating to base URL: {base_url}")
            await page.goto(base_url, timeout=60000)
            await page.wait_for_load_state("networkidle", timeout=60000)

            # 2. Enter main iframe
            iframe = page.frame_locator('iframe[title="Main Content"]')

            # 3. Apply Vessel filter
            logger.info("apply Vessel filter: %s", vessel_name)
            # open Requisition > ALL and toggle filter pane
            await iframe.get_by_role("menuitem", name="Requisition").click()
            await iframe.get_by_role("menuitem", name="ALL", exact=True).click()
            await page.wait_for_load_state("networkidle", timeout=60000)
            await iframe.get_by_role("menuitemcheckbox", name="Toggle filter").click()
            await sleep(2)
           
            
            
            # add a filter field and choose Vessel
            await iframe.get_by_role("button", name="Add a new filter on a field").click()
            await iframe.get_by_role("option", name="Vessel Name", exact=True).click()
            # fill the Vessel combobox to narrow results
            combo_v = iframe.get_by_role("combobox", name="Vessel Name")
            await combo_v.fill(vessel_name.upper())
            logger.info(f"Vessel filter applied in combobox {vessel_name}")
            
            # Wait for dropdown to populate
            logger.info("Waiting for dropdown to populate...")
            await sleep(2)
            
            try:
                # Wait for dropdown to be visible
                dropdown_v = iframe.locator('div.spa-view.spa-lookup')
                await dropdown_v.wait_for(state="visible", timeout=30000)
                logger.info("Dropdown is visible")
                await sleep(2)
            except Exception as e:
                logger.error(f"Error waiting for dropdown: {str(e)}")
                raise

            # Try to find and click the vessel by name
            try:
                vessel_option = dropdown_v.locator(f'tr:has-text("{vessel_name}")').first
                if await vessel_option.count() > 0:
                    logger.info(f"Found vessel by name")
                    await vessel_option.click()
                else:
                    logger.error("Could not find vessel in dropdown")
                    raise Exception(f"Vessel element not found in dropdown")
                
                logger.info(f"Successfully selected vessel {vessel_name}")
                await sleep(2)  # Wait for selection to take effect
            
            except Exception as e:
                logger.error(f"Error selecting vessel: {str(e)}")
                raise

            # 4. Apply Order Priority filter
            logger.info("apply Order Priority filter: URGENT")
            await iframe.get_by_role("button", name="Add a new filter on a field").click()
            await iframe.get_by_role("option", name="Order Priority", exact=True).click()
            combo_p = iframe.get_by_role("combobox", name="Order Priority")
            await combo_p.click()
            await sleep(1)

            try:
                urgent_row = iframe.locator('tr:has-text("URGENT"):has-text("Urgent/ Immediate")').first
                await urgent_row.wait_for(state="visible", timeout=30000)
                await urgent_row.click()
                logger.info("Selected URGENT priority")
                
                # Wait for 2 seconds after selecting URGENT
                logger.info("Waiting 3 seconds for data to load after URGENT selection")
                await sleep(3)
               
                
                # Click factBoxToggle button
                logger.info("Clicking factBoxToggle button")
                try:
                    factbox_toggle = iframe.locator('#b4h_factBoxToggle')
                    await factbox_toggle.wait_for(state="visible", timeout=30000)
                    await factbox_toggle.click()
                    logger.info("Successfully clicked factBoxToggle")
                    # Wait for any animations or data loading
                    await sleep(2)
                except Exception as e:
                    logger.warning(f"Could not click factBoxToggle: {str(e)}")
                
            except Exception as e:
                logger.error(f"Failed to select URGENT option: {str(e)}")
                raise

            # Take screenshot and upload directly to S3 (before getting table data)
            logger.info("Taking screenshot and uploading directly to S3")
            try:
                # Capture screenshot as bytes
                screenshot_bytes = await page.screenshot(full_page=True)
                logger.info(f"Screenshot captured as bytes: {len(screenshot_bytes)} bytes")

                # Upload directly to S3
                s3_url = upload_screenshot_to_s3(screenshot_bytes, vessel_name, "urgent")
                logger.info(f"Screenshot uploaded to S3: {s3_url}")

                # Add S3 URL as text content
                result["content"].append({
                    "type": "text",
                    "text": f"Screenshot uploaded to S3: {s3_url}"
                })

                # Store S3 URL in result for artifact creation
                result["s3_url"] = s3_url
                
            except Exception as e:
                logger.error(f"Error capturing/uploading screenshot: {str(e)}")
                result["content"].append({
                    "type": "text",
                    "text": f"Error capturing/uploading screenshot: {str(e)}"
                })

            # Get table data
            logger.info("Getting table data")
            try:
                # Get content from the table
                logger.info("Getting table content")
                # table = iframe.locator('#b6t')
                table = iframe.locator('xpath=/html/body/div[1]/div[3]/form/div/div[2]/main/div[2]/div[2]/div[2]/div/div[2]/div')
                # table = iframe.locator('table').nth(1)
                
                
                
                # Wait for the table to be visible
                await table.wait_for(state="visible", timeout=30000)
                logger.info("Table is visible")
                
                # Get both text and HTML content
                table_html = await table.inner_html()
                table_text = await table.inner_text()
                
                # Convert HTML table to markdown
                table_markdown = html_table_to_markdown(table_html)
                
                logger.info("Successfully got table content and converted to markdown")
                
                # Add table data to result with markdown format
                result["content"].append({
                    "type": "text",
                    "text": json.dumps({
                        # "text_content": table_text,
                        # "html_content": table_html,
                        "markdown_content": table_markdown
                    })
                })

            except Exception as e:
                logger.error(f"Error getting table data: {str(e)}")
                result["content"].append({
                    "type": "text",
                    "text": f"Error getting table data: {str(e)}"
                })

        except Exception as e:
            logger.error(f"Error in automation: {str(e)}")
            result["content"].append({
                "type": "text",
                "text": f"Error in automation: {str(e)}"
            })
        finally:
            await context.close()
            await browser.close()

    return result




async def urgent_requisition_from_shippalm(vessel_name: str, shippalmDoc: str) -> list[dict]:
    """
    Return markdown table data and S3 screenshot path for URGENT requisitions of a vessel.
    
    Args:
        vessel_name (str): Name of the vessel
        shippalmDoc (str): Document type for determining login URL
        
    Returns:
        list[dict]: List containing markdown content with S3 path and artifact data
    """
    result = await _urgent_requisition_automation(vessel_name, shippalmDoc)
    
    # Extract markdown content from result
    markdown_content = "No data could be retrieved from ShipPalm"
    s3_url_text = ""
    
    if result.get("content"):
        for content_block in result["content"]:
            if content_block.get("type") == "text":
                try:
                    # Try to parse JSON content to get markdown
                    content_data = json.loads(content_block["text"])
                    if "markdown_content" in content_data:
                        markdown_content = content_data["markdown_content"]
                except (json.JSONDecodeError, KeyError):
                    # If it's the S3 URL text
                    if "Screenshot uploaded to S3:" in content_block["text"]:
                        s3_url_text = content_block["text"]
    
    # Get S3 URL from result if available
    if result.get("s3_url") and not s3_url_text:
        s3_url_text = f"Screenshot uploaded to S3: {result['s3_url']}"
    
    # Create your content with markdown and S3 path
    your_content = {
        "type": "text",
        "text": f"{markdown_content}\n\n{s3_url_text}"
    }
    
    # Start with your content
    response_list = [your_content]
    
    # Add artifact if S3 URL is available
    if result.get("s3_url"):
        artifact_data = get_artifact("urgent_requisition_from_shippalm", result["s3_url"])
        
        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Urgent requisition from ShipPalm",
            format="json"
        )
        
        response_list.append(artifact)
    
    return response_list



# ─────────────────────────────────────────────────────────────────────────────
# Certificate & Survey/Service
# ─────────────────────────────────────────────────────────────────────────────

async def _certificate_automation(vessel_name: str, shippalmDoc: str) -> dict:
    # Determine base URL based on doc
    shippalmDoc ="SMPL"
    if shippalmDoc in norden_doc_list:
        base_url = f"https://shippalmv3.norden-synergy.com/?company={shippalmDoc}"
    elif shippalmDoc in synergy_group_doc_list:
        base_url = f"https://shippalmv3.synergygroup.sg/?company={shippalmDoc}"
    else:
        base_url = f"https://shippalmv3.synergymarinegroup.com/?company={shippalmDoc}"
        
    # Microsoft SSO login URL remains the same
    login_url = (
        "https://login.microsoftonline.com/common/wsfed?"
        "wa=wsignin1.0&wtrealm=https%3a%2f%2fshippalmv3.synergymarinegroup.com"
        "&wreply=https%3a%2f%2fshippalmv3.synergymarinegroup.com%2fSignIn%3fReturnUrl%3d%252f"
        "&sso_reload=true"
    )

    # Initialize result dictionary
    result = {
        "content": [],
        "s3_url": None
    }

    async with async_playwright() as p:
        logger.info("launch browser (non-headless)")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width":1380, "height":900})
        page = await context.new_page()

        try:
            # 1. Login (reusing same login logic)
            logger.info("goto login URL")
            await page.goto(login_url, timeout=60000)

            # Optional account tile
            tile = page.locator(f'div[data-test-id="accountTile"] >> text="{EMAIL}"')
            if await tile.count():
                await tile.first.click()

            # Email input
            await page.fill('input[type="email"], input[name="loginfmt"]', EMAIL)
            await page.click('button[type="submit"], input[type="submit"][value="Next"]')
            # Password input
            await page.fill('input[type="password"]', PASSWORD)
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_load_state("networkidle", timeout=60000)

            # After successful login, navigate to the specific company URL
            logger.info(f"Navigating to base URL: {base_url}")
            await page.goto(base_url)
            await page.wait_for_load_state("networkidle", timeout=60000)

            # 2. Enter main iframe
            iframe = page.frame_locator('iframe[title="Main Content"]')

            # 3. Navigate to Certificate & Survey/Service
            logger.info("navigating to Certificate & Survey/Service")
            await iframe.get_by_role("menuitem", name="Certificate & Survey/Service").click()
            await sleep(1)
            
            # Click on Vessel Certificates
            await iframe.get_by_role("menuitem", name="Vessel Certificates").click()
            # await page.wait_for_load_state("networkidle", timeout=60000)
            await page.wait_for_load_state("networkidle", timeout=60000) 
            
            
            # 4. Apply filters
            logger.info(f"applying filters - Vessel: {vessel_name}, Due Status: Expired")
            
            # Toggle filter pane
            await iframe.get_by_role("menuitemcheckbox", name="Toggle filter").click()
            await sleep(1)
            logger.info(f"Opened filter pane")

            # Add Vessel Name filter
            await iframe.get_by_role("button", name="Add a new filter on a field").click()
            await sleep(1)
            logger.info(f"Added Vessel Name filter")

            await iframe.get_by_role("option", name="Vessel Name", exact=True).click()
            logger.info(f"Vessel Name filter applied")
            
            # fill the Vessel combobox to narrow results
            combo_v = iframe.get_by_role("combobox", name="Vessel Name")
            await combo_v.fill(vessel_name.lower())
            logger.info(f"Vessel Name filter applied in combobox {vessel_name}")
            
            # Wait for dropdown and click
            dropdown_v = iframe.locator('div.spa-view.spa-lookup')
            await dropdown_v.wait_for(state="visible", timeout=30000)
            
            # Try to find and click the vessel by name
            try:
                vessel_option = dropdown_v.locator(f'tr:has-text("{vessel_name}")').first
                if await vessel_option.count() > 0:
                    logger.info(f"Found vessel by name")
                    await vessel_option.click()
                else:
                    logger.error("Could not find vessel in dropdown")
                    raise Exception(f"Vessel element not found in dropdown")
                
                logger.info(f"Successfully selected vessel {vessel_name}")
                await sleep(2)  # Wait for selection to take effect
            
            except Exception as e:
                logger.error(f"Error selecting vessel: {str(e)}")
                raise
            await sleep(1)
            logger.info(f"Vessel Name filter Clicked in dropdown {vessel_name}")
            
            # Add Due Status filter
            await iframe.get_by_role("button", name="Add a new filter on a field").click()
            
            # Select Due Status from dropdown
            await iframe.get_by_role("option", name="Due Status", exact=True).click()
            
            # Click the Due Status dropdown to open it
            due_status_dropdown = iframe.get_by_role("combobox", name="Due Status")
            await due_status_dropdown.click()
            await sleep(2)  # Wait longer for dropdown to open

            # Select Expired using content frame
            try:
                # Get the content frame and click Expired
                content_frame = page.locator("iframe[title=\"Main Content\"]").content_frame
                expired_option = content_frame.get_by_text("Expired")
                await expired_option.wait_for(state="visible", timeout=30000)
                await expired_option.click()
                logger.info("Selected Expired option")
                await sleep(2)  # Wait for selection to take effect
            except Exception as e:
                logger.error(f"Failed to select Expired option: {str(e)}")
                raise

            logger.info("Due Status filter applied")
            
            # Click FactBox toggle button
            logger.info("clicking FactBox toggle button")
            try:
                factbox_button = iframe.locator('div.command-bar-button-container--ZGRV7lJx0lJlu5ERRVHh6.factbox-toggle-control--yR-dCtUkau8iVWjN-e1FE')
                # b4h_factBoxToggle
                await factbox_button.wait_for(state="visible", timeout=30000)
                await factbox_button.click()
                await sleep(1)
            except Exception as e:
                logger.error(f"Failed to click FactBox toggle: {str(e)}")
                raise

            # Take screenshot and upload directly to S3 (before getting table data)
            logger.info("Taking screenshot and uploading directly to S3")
            try:
                # Capture screenshot as bytes
                screenshot_bytes = await page.screenshot(full_page=True)
                logger.info(f"Screenshot captured as bytes: {len(screenshot_bytes)} bytes")

                # Upload directly to S3
                s3_url = upload_screenshot_to_s3(screenshot_bytes, vessel_name, "certificates")
                logger.info(f"Screenshot uploaded to S3: {s3_url}")

                # Add S3 URL as text content
                result["content"].append({
                    "type": "text",
                    "text": f"Screenshot uploaded to S3: {s3_url}"
                })

                # Store S3 URL in result for artifact creation
                result["s3_url"] = s3_url
                
            except Exception as e:
                logger.error(f"Error capturing/uploading screenshot: {str(e)}")
                result["content"].append({
                    "type": "text",
                    "text": f"Error capturing/uploading screenshot: {str(e)}"
                })

            # Get table data
            logger.info("Getting table data")
            try:
                # Get content from the table
                logger.info("Getting table content")
                # table = iframe.locator('#b6h')
                table = iframe.locator('xpath=/html/body/div[1]/div[3]/form/div/div[2]/main/div[2]/div[2]/div[2]/div/div[2]/div')

                # table = iframe.locator('table[class*="ms-nav-grid-container"]').nth(1)
                # table = iframe.locator('table').nth(1)
                
                # Wait for the table to be visible
                await table.wait_for(state="visible", timeout=30000)
                logger.info("Table is visible")
                
                # Get both text and HTML content
                table_html = await table.inner_html()
                table_text = await table.inner_text()
                
                # Convert HTML table to markdown
                table_markdown = html_table_to_markdown(table_html)
                
                logger.info("Successfully got table content and converted to markdown")
                
                # Add table data to result with markdown format
                result["content"].append({
                    "type": "text",
                    "text": json.dumps({
                        "markdown_content": table_markdown
                    })
                })

            except Exception as e:
                logger.error(f"Error getting table data: {str(e)}")
                result["content"].append({
                    "type": "text",
                    "text": f"Error getting table data: {str(e)}"
                })

        except Exception as e:
            logger.error(f"Error in automation: {str(e)}")
            result["content"].append({
                "type": "text",
                "text": f"Error in automation: {str(e)}"
            })
        finally:
            await context.close()
            await browser.close()

    return result

async def expired_certificate_from_shippalm(vessel_name: str, shippalmDoc: str) -> list[dict]:
    """
    Return markdown table data and S3 screenshot path for expired certificates of a vessel.
    
    Args:
        vessel_name (str): Name of the vessel
        shippalmDoc (str): Document type for determining login URL
        
    Returns:
        list[dict]: List containing markdown content with S3 path and artifact data
    """
    result = await _certificate_automation(vessel_name, shippalmDoc)
    
    # Extract markdown content from result
    markdown_content = "No data could be retrieved from ShipPalm"
    s3_url_text = ""
    
    if result.get("content"):
        for content_block in result["content"]:
            if content_block.get("type") == "text":
                try:
                    # Try to parse JSON content to get markdown
                    content_data = json.loads(content_block["text"])
                    if "markdown_content" in content_data:
                        markdown_content = content_data["markdown_content"]
                except (json.JSONDecodeError, KeyError):
                    # If it's the S3 URL text
                    if "Screenshot uploaded to S3:" in content_block["text"]:
                        s3_url_text = content_block["text"]
    
    # Get S3 URL from result if available
    if result.get("s3_url") and not s3_url_text:
        s3_url_text = f"Screenshot uploaded to S3: {result['s3_url']}"
    
    # Create your content with markdown and S3 path
    your_content = {
        "type": "text",
        "text": f"{markdown_content}\n\n{s3_url_text}"
    }
    
    # Start with your content
    response_list = [your_content]
    
    # Add artifact if S3 URL is available
    if result.get("s3_url"):
        artifact_data = get_artifact("expired_certificate_from_shippalm", result["s3_url"])
        
        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Expired certificates from ShipPalm",
            format="json"
        )
        
        response_list.append(artifact)
    
    return response_list





# ─────────────────────────────────────────────────────────────────────────────
# Critical Spares Inventory
# ─────────────────────────────────────────────────────────────────────────────
async def _critical_spares_automation(vessel_name: str, shippalmDoc: str) -> dict:
    # Determine base URL based on doc
    if shippalmDoc in norden_doc_list:
        base_url = f"https://shippalmv3.norden-synergy.com/?company={shippalmDoc}"
    elif shippalmDoc in synergy_group_doc_list:
        base_url = f"https://shippalmv3.synergygroup.sg/?company={shippalmDoc}"
    else:
        base_url = f"https://shippalmv3.synergymarinegroup.com/?company={shippalmDoc}"
        
    # Microsoft SSO login URL remains the same
    login_url = (
        "https://login.microsoftonline.com/common/wsfed?"
        "wa=wsignin1.0&wtrealm=https%3a%2f%2fshippalmv3.synergymarinegroup.com"
        "&wreply=https%3a%2f%2fshippalmv3.synergymarinegroup.com%2fSignIn%3fReturnUrl%3d%252f"
        "&sso_reload=true"
    )

    # Initialize result dictionary
    result = {
        "content": [],
        "s3_url": None
    }

    async with async_playwright() as p:
        logger.info("launch browser (non-headless)")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width":1380, "height":900})
        page = await context.new_page()

        try:
            # 1. Login (reusing same login logic)
            logger.info("goto login URL")
            await page.goto(login_url, timeout=60000)
            await page.wait_for_load_state("networkidle", timeout=60000)

            # Optional account tile
            tile = page.locator(f'div[data-test-id="accountTile"] >> text="{EMAIL}"')
            if await tile.count():
                await tile.first.click()

            # Email input
            await page.fill('input[type="email"], input[name="loginfmt"]', EMAIL)
            await page.click('button[type="submit"], input[type="submit"][value="Next"]')
            
            # Password input
            await page.fill('input[type="password"]', PASSWORD)
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_load_state("networkidle", timeout=60000)

            # After successful login, navigate to the specific company URL
            logger.info(f"Navigating to base URL: {base_url}")
            logger.info(f"DOC NAME: {shippalmDoc}")
            await page.goto(base_url)
            await page.wait_for_load_state("networkidle", timeout=60000)

            # 2. Enter main iframe and wait for it
            logger.info("Waiting for main iframe")
            await page.wait_for_selector('iframe[title="Main Content"]', timeout=60000)
            iframe = page.frame_locator('iframe[title="Main Content"]')

            # 3. Navigate to Inventory
            logger.info("navigating to Inventory")
            await iframe.get_by_role("menuitem", name="Inventory").click()
            await sleep(2)  # Wait for menu to expand
            
            # Click on All Items and wait for page load
            await iframe.get_by_role("menuitem", name="All Items").click()
            await sleep(2)  # Wait for page to load
            await page.wait_for_load_state("networkidle", timeout=60000)  # Wait for page to load
            
           
            
            # Toggle filter pane
            await iframe.get_by_role("menuitemcheckbox", name="Toggle filter").click()
            await sleep(1)
            logger.info(f"Opened filter pane")
            
            # Toggle FactBox
            await iframe.get_by_role("menuitemcheckbox", name="Toggle FactBox").click()
            await sleep(1)
            logger.info(f"Clicked FactBox")
            
            # 4. Click on Critical Spares
            logger.info("clicking on Critical Spares")
            await page.locator("iframe[title=\"Main Content\"]").content_frame.get_by_role("button", name="Critical Spares").click()
            
            # Wait for navigation after clicking Critical Spares
            await sleep(2)  # Additional wait for any dynamic content
            
            # 5. Apply filters
            logger.info(f"applying filters - Vessel: {vessel_name}")
            
            # Add Vessel Name filter
            await iframe.get_by_role("button", name="Add a new filter on a field").click()
            await sleep(1)
            
            await iframe.get_by_role("option", name="Vessel", exact=True).click()
            logger.info(f"Vessel Name filter selected")
            
            # Fill the Vessel combobox to narrow results
            combo_v = iframe.get_by_role("combobox", name="Vessel")
            await combo_v.fill(vessel_name)
            logger.info(f"Vessel filter applied in combobox {vessel_name}")
            
            # Wait for dropdown and click
            dropdown_v = iframe.locator('div.spa-view.spa-lookup')
            await dropdown_v.wait_for(state="visible", timeout=30000)
            await sleep(2)  # Give more time for dropdown to populate
            
            # Try to select the vessel from dropdown
            try:
                vessel_option = dropdown_v.locator(f'tr:has-text("{vessel_name}")').first
                if await vessel_option.count() > 0:
                    logger.info(f"Found vessel by name")
                    await vessel_option.click()
                else:
                    # Try with exact text
                    vessel_option = dropdown_v.locator(f'text="{vessel_name}"').first
                    await vessel_option.click()
                
                logger.info(f"Successfully selected vessel {vessel_name}")
                await sleep(2)  # Wait for selection to take effect
            
            except Exception as e:
                logger.error(f"Error selecting vessel: {str(e)}")
                raise

            # Wait for table to load after vessel selection
            await sleep(2)  # Additional wait for any dynamic content

            # Take screenshot and upload directly to S3 (before getting table data)
            logger.info("Taking screenshot and uploading directly to S3")
            try:
                # Capture screenshot as bytes
                screenshot_bytes = await page.screenshot(full_page=True)
                logger.info(f"Screenshot captured as bytes: {len(screenshot_bytes)} bytes")

                # Upload directly to S3
                s3_url = upload_screenshot_to_s3(screenshot_bytes, vessel_name, "critical_spares")
                logger.info(f"Screenshot uploaded to S3: {s3_url}")

                # Add S3 URL as text content
                result["content"].append({
                    "type": "text",
                    "text": f"Screenshot uploaded to S3: {s3_url}"
                })

                # Store S3 URL in result for artifact creation
                result["s3_url"] = s3_url
                
            except Exception as e:
                logger.error(f"Error capturing/uploading screenshot: {str(e)}")
                result["content"].append({
                    "type": "text",
                    "text": f"Error capturing/uploading screenshot: {str(e)}"
                })
            await sleep(2)    

            # 6. Extract table data
            logger.info("Getting table data")
            try:
                # Get content from the table
                logger.info("Getting table content")
                # logger.info(iframe.locator('table[class*="ms-nav-grid-container"]'))
                # table = iframe.locator('#b16c')
                table = iframe.locator('xpath=/html/body/div[1]/div[3]/form/div/div[2]/main/div[2]/div[2]/div[2]/div/div[2]/div')
                # table = iframe.locator('#b1vx')
                # table = iframe.locator('table').nth(1)
                
                # Wait for the table to be visible
                await table.wait_for(state="visible", timeout=60000)
                logger.info("Table is visible")
                
                # Get both text and HTML content
                table_html = await table.evaluate('el => el.outerHTML')
                table_text = await table.inner_text()
                
                # Convert HTML table to markdown
                table_markdown = html_table_to_markdown(table_html)
                
                logger.info("Successfully got table content and converted to markdown")
                
                # Add table data to result with markdown format
                result["content"].append({
                    "type": "text",
                    "text": json.dumps({
                        "markdown_content": table_markdown
                    }, ensure_ascii=False)
                })

            except Exception as e:
                logger.error(f"Error getting table data: {str(e)}")
                result["content"].append({
                    "type": "text",
                    "text": f"Error getting table data: {str(e)}"
                })

            return result

        except Exception as e:
            logger.error(f"Error during critical spares automation: {str(e)}")
            # Take error state screenshot
            await page.screenshot(path="debug_critical_spares_error.png")
            result["content"].append({
                "type": "text",
                "text": f"Error during automation: {str(e)}"
            })
            return result
        finally:
            await context.close()
            await browser.close()


async def critical_spares_inventory_from_shippalm(vessel_name: str, shippalmDoc: str) -> list[dict]:
    """
    Return markdown table data and S3 screenshot path for critical spares inventory.
    
    Args:
        vessel_name (str): Name of the vessel
        shippalmDoc (str): Document type for determining login URL
        
    Returns:
        list[dict]: List containing markdown content with S3 path and artifact data
    """
    result = await _critical_spares_automation(vessel_name, shippalmDoc)
    
    # Extract markdown content from result
    markdown_content = "No data could be retrieved from ShipPalm"
    s3_url_text = ""
    
    if result.get("content"):
        for content_block in result["content"]:
            if content_block.get("type") == "text":
                try:
                    # Try to parse JSON content to get markdown
                    content_data = json.loads(content_block["text"])
                    if "markdown_content" in content_data:
                        markdown_content = content_data["markdown_content"]
                except (json.JSONDecodeError, KeyError):
                    # If it's the S3 URL text
                    if "Screenshot uploaded to S3:" in content_block["text"]:
                        s3_url_text = content_block["text"]
    
    # Get S3 URL from result if available
    if result.get("s3_url") and not s3_url_text:
        s3_url_text = f"Screenshot uploaded to S3: {result['s3_url']}"
    
    # Create your content with markdown and S3 path
    your_content = {
        "type": "text",
        "text": f"{markdown_content}\n\n{s3_url_text}"
    }
    
    # Start with your content
    response_list = [your_content]
    
    # Add artifact if S3 URL is available
    if result.get("s3_url"):
        artifact_data = get_artifact("critical_spares_inventory_from_shippalm", result["s3_url"])
        
        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Critical spares inventory from ShipPalm",
            format="json"
        )
        
        response_list.append(artifact)
    
    return response_list





# ─────────────────────────────────────────────────────────────────────────────
# Position Book Report
# ─────────────────────────────────────────────────────────────────────────────
 
async def _position_book_automation(vessel_name: str, shippalmDoc: str) -> dict:
    # Determine base URL based on doc
    if shippalmDoc in norden_doc_list:
        base_url = f"https://shippalmv3.norden-synergy.com/?company={shippalmDoc}"
    elif shippalmDoc in synergy_group_doc_list:
        base_url = f"https://shippalmv3.synergygroup.sg/?company={shippalmDoc}"
    else:
        base_url = f"https://shippalmv3.synergymarinegroup.com/?company={shippalmDoc}"
        
    # Microsoft SSO login URL remains the same
    login_url = (
        "https://login.microsoftonline.com/common/wsfed?"
        "wa=wsignin1.0&wtrealm=https%3a%2f%2fshippalmv3.synergymarinegroup.com"
        "&wreply=https%3a%2f%2fshippalmv3.synergymarinegroup.com%2fSignIn%3fReturnUrl%3d%252f"
        "&sso_reload=true"
    )

    # Initialize result dictionary
    result = {
        "content": [],
        "s3_url": None
    }

    async with async_playwright() as p:
        logger.info("launch browser (headless)")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width":1380, "height":900})
        page = await context.new_page()

        try:
            # 1. Login via Microsoft SSO
            logger.info("goto login URL")
            await page.goto(login_url, timeout=60000)

            # Optional account tile
            tile = page.locator(f'div[data-test-id="accountTile"] >> text="{EMAIL}"')
            if await tile.count():
                await tile.first.click()

            # Email input
            await page.fill('input[type="email"], input[name="loginfmt"]', EMAIL)
            await page.click('button[type="submit"], input[type="submit"][value="Next"]')
            # Password input
            await page.fill('input[type="password"]', PASSWORD)
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_load_state("networkidle", timeout=60000)

            # After successful login, navigate to the specific company URL
            logger.info(f"Navigating to base URL: {base_url}")
            await page.goto(base_url, timeout=60000)
            await page.wait_for_load_state("networkidle", timeout=60000)

            # 2. Enter main iframe
            iframe = page.frame_locator('iframe[title="Main Content"]')

            # 3. Navigate to Voyage
            logger.info("navigating to Voyage")
            await iframe.get_by_role("menuitem", name="Voyage").click()
            await iframe.get_by_role("menuitem", name="Position Book Report").click()
            logger.info("Position Book Report Clicked")
            await page.wait_for_load_state("networkidle", timeout=60000)  # Wait for page to load

         
            # 4. Apply Vessel filter
            logger.info("apply Vessel filter: %s", vessel_name)
            # Toggle filter pane
            await iframe.get_by_role("menuitemcheckbox", name="Toggle filter").click()
            # add a filter field and choose Vessel
            await iframe.get_by_role("button", name="Add a new filter on a field").click()
            await iframe.get_by_role("option", name="Vessel Name", exact=True).click()
            # fill the Vessel combobox to narrow results
            combo_v = iframe.get_by_role("combobox", name="Vessel Name")
            await combo_v.fill(vessel_name.upper())
            logger.info(f"Vessel filter applied in combobox {vessel_name}")
            
            # Wait for dropdown to populate
            logger.info("Waiting for dropdown to populate...")
            await sleep(2)
            
            try:
                # Wait for dropdown to be visible
                dropdown_v = iframe.locator('div.spa-view.spa-lookup')
                await dropdown_v.wait_for(state="visible", timeout=30000)
                logger.info("Dropdown is visible")
                await sleep(2)
            except Exception as e:
                logger.error(f"Error waiting for dropdown: {str(e)}")
                raise

            # Try to find and click the vessel by name
            try:
                vessel_option = dropdown_v.locator(f'tr:has-text("{vessel_name}")').first
                if await vessel_option.count() > 0:
                    logger.info(f"Found vessel by name")
                    await vessel_option.click()
                else:
                    logger.error("Could not find vessel in dropdown")
                    raise Exception(f"Vessel element not found in dropdown")
                
                logger.info(f"Successfully selected vessel {vessel_name}")
                await sleep(2)  # Wait for selection to take effect
            
            except Exception as e:
                logger.error(f"Error selecting vessel: {str(e)}")
                raise
            await sleep(2)


            # 5. Click factBoxToggle button
            logger.info("Clicking factBoxToggle button")
            try:
                factbox_toggle = iframe.locator('#b4h_factBoxToggle')
                await factbox_toggle.wait_for(state="visible", timeout=30000)
                await factbox_toggle.click()
                logger.info("Successfully clicked factBoxToggle")
                # Wait for any animations or data loading
                await sleep(2)
            except Exception as e:
                logger.warning(f"Could not click factBoxToggle: {str(e)}")

            # Take screenshot and upload directly to S3 (before getting table data)
            logger.info("Taking screenshot and uploading directly to S3")
            try:
                # Capture screenshot as bytes
                screenshot_bytes = await page.screenshot(full_page=True)
                logger.info(f"Screenshot captured as bytes: {len(screenshot_bytes)} bytes")

                # Upload directly to S3
                s3_url = upload_screenshot_to_s3(screenshot_bytes, vessel_name, "position_book")
                logger.info(f"Screenshot uploaded to S3: {s3_url}")

                # Add S3 URL as text content
                result["content"].append({
                    "type": "text",
                    "text": f"Screenshot uploaded to S3: {s3_url}"
                })

                # Store S3 URL in result for artifact creation
                result["s3_url"] = s3_url
                
            except Exception as e:
                logger.error(f"Error capturing/uploading screenshot: {str(e)}")
                result["content"].append({
                    "type": "text",
                    "text": f"Error capturing/uploading screenshot: {str(e)}"
                })

            # Get table data
            logger.info("Getting table data")
            try:
                # Get content from the table
                logger.info("Getting table content")
                # table = iframe.locator('#b66')
                table = iframe.locator('xpath=/html/body/div[1]/div[3]/form/div/div[2]/main/div[2]/div[2]/div[2]/div/div[2]/div')

                # table = iframe.locator('table[class*="ms-nav-grid-data-table"]')
                # frame.locator('table[class*="ms-nav-grid-data-table"]').nth(1)
                
                # Wait for the table to be visible
                await table.wait_for(state="visible", timeout=60000)  # 2 minutes
                logger.info("Table is visible")
                
                # Get both text and HTML content
                table_html = await table.inner_html()
                table_text = await table.inner_text()
                
                # Convert HTML table to markdown
                table_markdown = html_table_to_markdown(table_html)
                
                logger.info("Successfully got table content and converted to markdown")
                
                # Add table data to result with markdown format
                result["content"].append({
                    "type": "text",
                    "text": json.dumps({
                        "markdown_content": table_markdown
                    })
                })

            except Exception as e:
                logger.error(f"Error getting table data: {str(e)}")
                result["content"].append({
                    "type": "text",
                    "text": f"Error getting table data: {str(e)}"
                })

        except Exception as e:
            logger.error(f"Error in automation: {str(e)}")
            result["content"].append({
                "type": "text",
                "text": f"Error in automation: {str(e)}"
            })
        finally:
            await context.close()
            await browser.close()

    return result


async def position_book_report_from_shippalm(vessel_name: str, shippalmDoc: str) -> list[dict]:
    """
    Return markdown table data and S3 screenshot path for Position Book Report.
    
    Args:
        vessel_name (str): The name of the vessel to filter by
        shippalmDoc (str): Document type for determining login URL
        
    Returns:
        list[dict]: List containing markdown content with S3 path and artifact data
    """
    result = await _position_book_automation(vessel_name, shippalmDoc)
    
    # Extract markdown content from result
    markdown_content = "No data could be retrieved from ShipPalm"
    s3_url_text = ""
    
    if result.get("content"):
        for content_block in result["content"]:
            if content_block.get("type") == "text":
                try:
                    # Try to parse JSON content to get markdown
                    content_data = json.loads(content_block["text"])
                    if "markdown_content" in content_data:
                        markdown_content = content_data["markdown_content"]
                except (json.JSONDecodeError, KeyError):
                    # If it's the S3 URL text
                    if "Screenshot uploaded to S3:" in content_block["text"]:
                        s3_url_text = content_block["text"]
    
    # Get S3 URL from result if available
    if result.get("s3_url") and not s3_url_text:
        s3_url_text = f"Screenshot uploaded to S3: {result['s3_url']}"
    
    # Create your content with markdown and S3 path
    your_content = {
        "type": "text",
        "text": f"{markdown_content}\n\n{s3_url_text}"
    }
    
    # Start with your content
    response_list = [your_content]
    
    # Add artifact if S3 URL is available
    if result.get("s3_url"):
        artifact_data = get_artifact("position_book_report_from_shippalm", result["s3_url"])
        
        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Position book report from ShipPalm",
            format="json"
        )
        
        response_list.append(artifact)
    
    return response_list







# ─────────────────────────────────────────────────────────────────────────────
# Purchase Order number data
# ─────────────────────────────────────────────────────────────────────────────

async def _purchase_order_data_automation(order_number: str, shippalmDoc: str) -> dict:
    # Determine base URL based on doc
    if shippalmDoc in norden_doc_list:
        base_url = f"https://shippalmv3.norden-synergy.com/?company={shippalmDoc}"
    elif shippalmDoc in synergy_group_doc_list:
        base_url = f"https://shippalmv3.synergygroup.sg/?company={shippalmDoc}"
    else:
        base_url = f"https://shippalmv3.synergymarinegroup.com/?company={shippalmDoc}"

    # Microsoft SSO login URL remains the same
    login_url = (
        "https://login.microsoftonline.com/common/wsfed?"
        "wa=wsignin1.0&wtrealm=https%3a%2f%2fshippalmv3.synergymarinegroup.com"
        "&wreply=https%3a%2f%2fshippalmv3.synergymarinegroup.com%2fSignIn%3fReturnUrl%3d%252f"
        "&sso_reload=true"
    )

    # Initialize result dictionary
    result = {
        "content": [],
        "s3_url": None
    }

    async with async_playwright() as p:
        logger.info("launch browser (headless)")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width":1380, "height":900})
        page = await context.new_page()

        try:
            # 1. Login (reusing same login logic)
            logger.info("goto login URL")
            await page.goto(login_url, timeout=60000)

            # Optional account tile
            tile = page.locator(f'div[data-test-id="accountTile"] >> text="{EMAIL}"')
            if await tile.count():
                await tile.first.click()

            # Email input
            await page.fill('input[type="email"], input[name="loginfmt"]', EMAIL)
            await page.click('button[type="submit"], input[type="submit"][value="Next"]')
            # Password input
            await page.fill('input[type="password"]', PASSWORD)
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_load_state("networkidle", timeout=60000)

            # After successful login, navigate to the specific company URL
            logger.info(f"Navigating to base URL: {base_url}")
            logger.info(f"DOC NAME: {shippalmDoc}")
            await page.goto(base_url)
            await page.wait_for_load_state("networkidle", timeout=60000)

            # 2. Navigate to Orders
            logger.info("navigating to Orders")
            await page.wait_for_selector('iframe[title="Main Content"]', timeout=60000)
            frame = page.frame_locator('iframe[title="Main Content"]')
            
            # Click Orders menu
            await frame.get_by_role("menuitem", name="Orders", exact=True).click()
            await page.wait_for_load_state("networkidle", timeout=60000)  # Wait for menu to load
            
            # Click ALL
            await frame.get_by_role("menuitem", name="ALL", exact=True).click()
            await page.wait_for_load_state("networkidle", timeout=60000)  # Wait for page to load
            
         

            # Toggle filter pane
            await frame.get_by_role("menuitemcheckbox", name="Toggle filter").click()
            await sleep(1)

            # Add No. filter
            await frame.get_by_role("button", name="Add a new filter on a field").click()
            await frame.get_by_role("option", name="No.", exact=True).click()
            
            # Enter order number
            logger.info(f"Attempting to enter order number: {order_number}")
            
            # Enter order number
            filter_input = frame.get_by_role("textbox", name="No.", exact=True).first
            logger.info(f"Filling order number: {order_number}")
            await filter_input.fill(order_number)
            logger.info("Pressing Enter key")
            await filter_input.press("Enter")
            logger.info("Waiting after pressing Enter key")
            await sleep(2)
            
            # Click factBoxToggle button
            logger.info("Clicking factBoxToggle button")
            try:
                factbox_toggle = frame.locator('#b4h_factBoxToggle')
                await factbox_toggle.click()
                logger.info("Successfully clicked factBoxToggle")
                await sleep(2)  # Wait for any animations
            except Exception as e:
                logger.warning(f"Could not click factBoxToggle: {str(e)}")

            # Take screenshot and upload directly to S3 (before getting table data)
            logger.info("Taking screenshot and uploading directly to S3")
            try:
                # Capture screenshot as bytes
                screenshot_bytes = await page.screenshot(full_page=True)
                logger.info(f"Screenshot captured as bytes: {len(screenshot_bytes)} bytes")

                # Upload directly to S3
                s3_url = upload_screenshot_to_s3(screenshot_bytes, order_number, "purchase_order")
                logger.info(f"Screenshot uploaded to S3: {s3_url}")

                # Add S3 URL as text content
                result["content"].append({
                    "type": "text",
                    "text": f"Screenshot uploaded to S3: {s3_url}"
                })

                # Store S3 URL in result for artifact creation
                result["s3_url"] = s3_url
                
            except Exception as e:
                logger.error(f"Error capturing/uploading screenshot: {str(e)}")
                result["content"].append({
                    "type": "text",
                    "text": f"Error capturing/uploading screenshot: {str(e)}"
                })

            # Get all table data
            logger.info("Getting table data")
            try:
                # Wait for and get the second data grid (index 1)
                # main_grid = frame.locator('table[class*="ms-nav-grid-data-table"]').nth(1)
                main_grid = frame.locator('xpath=/html/body/div[1]/div[3]/form/div/div[2]/main/div[2]/div[2]/div[2]/div/div[2]/div')

                # table = iframe.locator('xpath=/html/body/div[1]/div[3]/form/div/div[2]/main/div[2]/div[2]/div[2]/div/div[2]/div')

                await main_grid.wait_for(state="visible", timeout=30000)
                
                # Get the data
                grid_html = await main_grid.evaluate('el => el.outerHTML')
                grid_text = await main_grid.inner_text()
                
                # Convert HTML table to markdown
                table_markdown = html_table_to_markdown(grid_html)
                
                logger.info("Successfully got grid content and converted to markdown")
                
                # Add table data to result with markdown format
                result["content"].append({
                    "type": "text",
                    "text": json.dumps({
                        "markdown_content": table_markdown
                    })
                })

            except Exception as e:
                logger.error(f"Error getting table data: {str(e)}")
                result["content"].append({
                    "type": "text",
                    "text": f"Error getting table data: {str(e)}"
                })

        except Exception as e:
            logger.error(f"Failed to retrieve order {order_number}: {str(e)}")
            result["content"].append({
                "type": "text",
                "text": f"Error in automation: {str(e)}"
            })
        finally:
            await context.close()
            await browser.close()
            
    return result


async def purchase_order_data_from_shippalm(order_number: str, shippalmDoc: str) -> list[dict]:
    """
    Return markdown table data and S3 screenshot path for a specific Purchase Order.
    
    Args:
        order_number (str): The order number to filter by
        shippalmDoc (str): Document type for determining login URL
        
    Returns:
        list[dict]: List containing markdown content with S3 path and artifact data
    """
    result = await _purchase_order_data_automation(order_number, shippalmDoc)
    
    # Extract markdown content from result
    markdown_content = "No data could be retrieved from ShipPalm"
    s3_url_text = ""
    
    if result.get("content"):
        for content_block in result["content"]:
            if content_block.get("type") == "text":
                try:
                    # Try to parse JSON content to get markdown
                    content_data = json.loads(content_block["text"])
                    if "markdown_content" in content_data:
                        markdown_content = content_data["markdown_content"]
                except (json.JSONDecodeError, KeyError):
                    # If it's the S3 URL text
                    if "Screenshot uploaded to S3:" in content_block["text"]:
                        s3_url_text = content_block["text"]
    
    # Get S3 URL from result if available
    if result.get("s3_url") and not s3_url_text:
        s3_url_text = f"Screenshot uploaded to S3: {result['s3_url']}"
    
    # Create your content with markdown and S3 path
    your_content = {
        "type": "text",
        "text": f"{markdown_content}\n\n{s3_url_text}"
    }
    
    # Start with your content
    response_list = [your_content]
    
    # Add artifact if S3 URL is available
    if result.get("s3_url"):
        artifact_data = get_artifact("purchase_order_data_from_shippalm", result["s3_url"])
        
        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Purchase order data from ShipPalm",
            format="json"
        )
        
        response_list.append(artifact)
    
    return response_list







# ─────────────────────────────────────────────────────────────────────────────
# Requisition Order number data
# ─────────────────────────────────────────────────────────────────────────────

async def _purchase_requisition_order_data_automation(requisition_number: str, shippalmDoc: str) -> dict:
    # Determine base URL based on doc
    if shippalmDoc in norden_doc_list:
        base_url = f"https://shippalmv3.norden-synergy.com/?company={shippalmDoc}"
    elif shippalmDoc in synergy_group_doc_list:
        base_url = f"https://shippalmv3.synergygroup.sg/?company={shippalmDoc}"
    else:
        base_url = f"https://shippalmv3.synergymarinegroup.com/?company={shippalmDoc}"

    # Microsoft SSO login URL remains the same
    login_url = (
        "https://login.microsoftonline.com/common/wsfed?"
        "wa=wsignin1.0&wtrealm=https%3a%2f%2fshippalmv3.synergymarinegroup.com"
        "&wreply=https%3a%2f%2fshippalmv3.synergymarinegroup.com%2fSignIn%3fReturnUrl%3d%252f"
        "&sso_reload=true"
    )

    # Initialize result dictionary
    result = {
        "content": [],
        "s3_url": None
    }

    async with async_playwright() as p:
        logger.info("launch browser (headless)")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width":1380, "height":900})
        page = await context.new_page()

        try:
            # 1. Login
            logger.info("goto login URL")
            await page.goto(login_url, timeout=60000)

            # Optional account tile
            tile = page.locator(f'div[data-test-id="accountTile"] >> text="{EMAIL}"')
            if await tile.count():
                await tile.first.click()

            # Email input
            await page.fill('input[type="email"], input[name="loginfmt"]', EMAIL)
            await page.click('button[type="submit"], input[type="submit"][value="Next"]')
            # Password input
            await page.fill('input[type="password"]', PASSWORD)
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_load_state("networkidle", timeout=60000)

            # After successful login, navigate to the specific company URL
            logger.info(f"Navigating to base URL: {base_url}")
            logger.info(f"DOC NAME: {shippalmDoc}")
            await page.goto(base_url, timeout=60000)
            await page.wait_for_load_state("networkidle", timeout=60000)

            # 2. Navigate to Requisition
            logger.info("navigating to Requisition")
            await page.wait_for_selector('iframe[title="Main Content"]', timeout=60000)
            frame = page.frame_locator('iframe[title="Main Content"]')
            
            # Click Requisition menu
            await frame.get_by_role("menuitem", name="Requisition", exact=True).click()
            await page.wait_for_load_state("networkidle", timeout=60000)  # Wait for menu to load
            
            # Click ALL
            await frame.get_by_role("menuitem", name="ALL", exact=True).click()
            await page.wait_for_load_state("networkidle", timeout=60000)  # Wait for page to load
            
          

            # Toggle filter pane
            await frame.get_by_role("menuitemcheckbox", name="Toggle filter").click()
            await sleep(1)

            # Add No. filter
            await frame.get_by_role("button", name="Add a new filter on a field").click()
            await frame.get_by_role("option", name="No.", exact=True).click()
            
            # Enter requisition number
            logger.info(f"Attempting to enter requisition number: {requisition_number}")
            
            # Enter requisition number
            filter_input = frame.get_by_role("textbox", name="No.", exact=True).first
            logger.info(f"Filling requisition number: {requisition_number}")
            await filter_input.fill(requisition_number)
            logger.info("Pressing Enter key")
            await filter_input.press("Enter")
            logger.info("Waiting after pressing Enter key")
            await sleep(2)
            
            # Click factBoxToggle button
            logger.info("Clicking factBoxToggle button")
            try:
                factbox_toggle = frame.locator('#b4h_factBoxToggle')
                await factbox_toggle.click()
                logger.info("Successfully clicked factBoxToggle")
                await sleep(2)  # Wait for any animations
            except Exception as e:
                logger.warning(f"Could not click factBoxToggle: {str(e)}")

            # Take screenshot and upload directly to S3 (before getting table data)
            logger.info("Taking screenshot and uploading directly to S3")
            try:
                # Capture screenshot as bytes
                screenshot_bytes = await page.screenshot(full_page=True)
                logger.info(f"Screenshot captured as bytes: {len(screenshot_bytes)} bytes")

                # Upload directly to S3
                s3_url = upload_screenshot_to_s3(screenshot_bytes, requisition_number, "purchase_requisition")
                logger.info(f"Screenshot uploaded to S3: {s3_url}")

                # Add S3 URL as text content
                result["content"].append({
                    "type": "text",
                    "text": f"Screenshot uploaded to S3: {s3_url}"
                })

                # Store S3 URL in result for artifact creation
                result["s3_url"] = s3_url
                
            except Exception as e:
                logger.error(f"Error capturing/uploading screenshot: {str(e)}")
                result["content"].append({
                    "type": "text",
                    "text": f"Error capturing/uploading screenshot: {str(e)}"
                })

            # Get all table data
            logger.info("Getting table data")
            try:
                # Wait for and get the second data grid (index 1)
                # main_grid = frame.locator('table[class*="ms-nav-grid-data-table"]').nth(1)
                main_grid = frame.locator('xpath=/html/body/div[1]/div[3]/form/div/div[2]/main/div[2]/div[2]/div[2]/div/div[2]/div')
                await main_grid.wait_for(state="visible", timeout=30000)
                
                # Get the data
                grid_html = await main_grid.evaluate('el => el.outerHTML')
                grid_text = await main_grid.inner_text()
                
                # Convert HTML table to markdown
                table_markdown = html_table_to_markdown(grid_html)
                
                logger.info("Successfully got grid content and converted to markdown")
                
                # Add table data to result with markdown format
                result["content"].append({
                    "type": "text",
                    "text": json.dumps({
                        "markdown_content": table_markdown
                    })
                })

            except Exception as e:
                logger.error(f"Error getting table data: {str(e)}")
                result["content"].append({
                    "type": "text",
                    "text": f"Error getting table data: {str(e)}"
                })

        except Exception as e:
            logger.error(f"Failed to retrieve requisition {requisition_number}: {str(e)}")
            result["content"].append({
                "type": "text",
                "text": f"Error in automation: {str(e)}"
            })
        finally:
            await context.close()
            await browser.close()
            
    return result


async def purchase_requisition_order_data_from_shippalm(requisition_number: str, shippalmDoc: str) -> list[dict]:
    """
    Return markdown table data and S3 screenshot path for a specific Purchase Requisition.
    
    Args:
        requisition_number (str): The requisition number to filter by
        shippalmDoc (str): Document type for determining login URL
        
    Returns:
        list[dict]: List containing markdown content with S3 path and artifact data
    """
    result = await _purchase_requisition_order_data_automation(requisition_number, shippalmDoc)
    
    # Extract markdown content from result
    markdown_content = "No data could be retrieved from ShipPalm"
    s3_url_text = ""
    
    if result.get("content"):
        for content_block in result["content"]:
            if content_block.get("type") == "text":
                try:
                    # Try to parse JSON content to get markdown
                    content_data = json.loads(content_block["text"])
                    if "markdown_content" in content_data:
                        markdown_content = content_data["markdown_content"]
                except (json.JSONDecodeError, KeyError):
                    # If it's the S3 URL text
                    if "Screenshot uploaded to S3:" in content_block["text"]:
                        s3_url_text = content_block["text"]
    
    # Get S3 URL from result if available
    if result.get("s3_url") and not s3_url_text:
        s3_url_text = f"Screenshot uploaded to S3: {result['s3_url']}"
    
    # Create your content with markdown and S3 path
    your_content = {
        "type": "text",
        "text": f"{markdown_content}\n\n{s3_url_text}"
    }
    
    # Start with your content
    response_list = [your_content]
    
    # Add artifact if S3 URL is available
    if result.get("s3_url"):
        artifact_data = get_artifact("purchase_requisition_order_data_from_shippalm", result["s3_url"])
        
        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Purchase requisition order data from ShipPalm",
            format="json"
        )
        
        response_list.append(artifact)
    
    return response_list






