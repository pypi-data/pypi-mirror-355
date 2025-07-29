import re
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from asyncio import sleep
import asyncio
import time
from urllib.parse import parse_qs, urlparse
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any, Optional ,Sequence, Union
from .mcp_instance import mcp
from .tool_schema import tool_definitions
import mcp.types as types
import json
from pymongo import MongoClient, errors
import pandas as pd
import aiohttp
from dotenv import load_dotenv

import nest_asyncio

load_dotenv()

# ── MCP instance & logger ─────────────────────────────────────────────
logger = logging.getLogger("SyiaDataTools")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[tools] %(message)s"))
    logger.addHandler(handler)

# ── Credentials ───────────────────────────────────────────────────────────
load_dotenv()
EMAIL = os.getenv("LOGIN_EMAIL", "")
PASSWORD = os.getenv("LOGIN_PASSWORD", "")

server_tools = tool_definitions

#------ Tool Registration ------------------------------------------------------------

def register_tools():
    @mcp.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return server_tools

    @mcp.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
        try:
            if name == "cdi_data_main":
                return await cdi_data_main(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]


# ────────────────────── Helper functions ─────────────────────────

def _build_login_url(doc_name: str) -> str:
 
    user = os.getenv(f'CDI_{doc_name}_USERNAME')
    pwd = os.getenv(f'CDI_{doc_name}_PASSWORD')
    if not user or not pwd:
        raise ValueError(f'Missing credentials: set CDI_{doc_name}_USERNAME and CDI_{doc_name}_PASSWORD')
    return (
        'https://www.cdim.org/psp/cdim.wp_postlogin?p_session_id=&p_mode=1'
        '&p_user=%7Enot+used%7E&p_URL=https%3A%2F%2Fwww.cdim.org%2Fpsp%2Fcdim.wp_home'
        f'&p_userid={user}&p_password={pwd}'
    )


def _get_session_id(html: str) -> str:
    patterns = [
        r'p_session_id=([^&"\']+)',
        r'session_id\s*=\s*["\']([^"\']+)["\']',
        r'name="p_session_id"\s+value="([^"]+)"'
    ]
    for pat in patterns:
        m = re.search(pat, html)
        if m:
            return m.group(1)
    raise RuntimeError('Session ID not found in login response')


def _parse_vessel_table(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', class_='cell_table')
    if not table:
        return pd.DataFrame()
    rows = []
    for tr in table.find_all('tr'):
        cells = [td.get_text(strip=True) for td in tr.find_all(['th','td'])]
        if len(cells) > 5:
            rows.append(cells)
    if len(rows) < 2:
        return pd.DataFrame()
    header = rows[0]
    data = [r[:len(header)] for r in rows[1:]]
    return pd.DataFrame(data, columns=header)

# ───────────────── Vessel list scraper ─────────────────────────────────

async def _fetch_vessel_list(session: aiohttp.ClientSession, session_id: str, max_pages: int) -> pd.DataFrame:
    pages: List[pd.DataFrame] = []
    for page in range(1, max_pages + 1):
        url = f'https://www.cdim.org/psp/cdim.wp_all_ships?p_session_id={session_id}&p_page_no={page}'
        logger.info('Fetching vessel list page %d', page)
        async with session.get(url) as resp:
            resp.raise_for_status()
            text = await resp.text()
            df = _parse_vessel_table(text)
            if df.empty:
                logger.info('No data on vessel list page %d, stopping', page)
                break
            pages.append(df)
    return pd.concat(pages, ignore_index=True) if pages else pd.DataFrame()

# ──────────── Inspection & PDF fetch with corrected PDF link ─────────────────

async def _fetch_inspections(session: aiohttp.ClientSession, session_id: str, vessels: pd.DataFrame, download_dir: Path) -> List[Dict[str,Any]]:
    inspections: List[Dict[str,Any]] = []
    seen = set()
    download_dir.mkdir(parents=True, exist_ok=True)

    for _, v in vessels.iterrows():
        imo = v.get('IMO')
        vessel_name = v.get('Ship Name') or v.get('Vessel Name') or ''
        detail_url = f'https://www.cdim.org/psp/cdim.wp_view_ship?p_session_id={session_id}&p_lrn_number={imo}'
        logger.debug('Fetching details for IMO %s', imo)
        async with session.get(detail_url) as resp:
            resp.raise_for_status()
            text = await resp.text()
            soup = BeautifulSoup(text, 'html.parser')
            table = soup.find('table', class_='cell_table')
            if not table:
                continue
            headers = [th.get_text(strip=True) for th in table.find_all('th')]

            for tr in table.find_all('tr')[1:]:
                cols = [td.get_text(strip=True) for td in tr.find_all('td')]
                if not any(cols):
                    continue
                cols = cols[:len(headers)]
                info = dict(zip(headers, cols))
                key = (imo, info.get('Insp. Date'), info.get(headers[0]))
                if key in seen:
                    continue
                seen.add(key)
                info['IMO'] = imo
                info['Vessel_Name'] = vessel_name

                # Correct summary link for PDF retrieval
                link_tag = tr.find('a', href=True, string=lambda t: t and 'view' in t.lower())
                if link_tag:
                    logger.info('Found PDF link for IMO %s: %s', imo, link_tag['href'])
                    q = parse_qs(urlparse(link_tag['href']).query)
                    pdf_page = (
                        'https://www.cdim.org/pls/apex/cdim.wp_summary?'
                        f'p_session_id={q.get("p_session_id",[""])[0]}&'
                        f'p_inspection_number={q.get("p_inspection_number",[""])[0]}&'
                        f'p_lrn_number={q.get("p_lrn_number",[""])[0]}&'
                        f'p_qset={q.get("p_qset",[""])[0]}&'
                        f'p_report_number={q.get("p_report_number",[""])[0]}&'
                        'p_language=10&p_print_type=pre_pdf&p_is_loading=0'
                    )
                    logger.info('Fetching PDF page for IMO %s: %s', imo, pdf_page)
                    async with session.get(pdf_page) as pdf_resp:
                        if pdf_resp.ok:
                            text = await pdf_resp.text()
                            psoup = BeautifulSoup(text, 'html.parser')
                            pdf_tag = psoup.find('a', href=True, string='View PDF file')
                            if pdf_tag:
                                pdf_url = pdf_tag['href']
                                if not pdf_url.startswith('http'):
                                    pdf_url = 'https://www.cdim.org' + pdf_url
                                logger.info('Found PDF URL for IMO %s: %s', imo, pdf_url)
                                try:
                                    async with session.get(pdf_url) as file_resp:
                                        file_resp.raise_for_status()
                                        content = await file_resp.read()
                                        date_str = info.get('Insp. Date','')
                                        if date_str:
                                            try:
                                                dt = datetime.strptime(date_str, '%d-%m-%Y').strftime('%Y-%m-%d')
                                            except ValueError:
                                                # If date parsing fails, use current date
                                                dt = datetime.now().strftime('%Y-%m-%d')
                                                logger.warning('Date parsing failed for %s, using current date', date_str)
                                        else:
                                            dt = datetime.now().strftime('%Y-%m-%d')
                                        
                                        # Clean vessel name for filename
                                        clean_vessel_name = vessel_name.replace('/', '-').replace('\\', '-').replace(':', '-')
                                        fname = f'{clean_vessel_name}_{imo}_{dt}.pdf'
                                        fpath = download_dir / fname
                                        
                                        # Ensure directory exists
                                        fpath.parent.mkdir(parents=True, exist_ok=True)
                                        
                                        with open(fpath,'wb') as f:
                                            f.write(content)
                                        
                                        info['pdf_path'] = str(fpath.resolve())
                                        info['pdf_link'] = pdf_url
                                        logger.info('Successfully downloaded PDF: %s (size: %d bytes)', fpath, len(content))
                                        
                                        # Verify file was actually written
                                        if fpath.exists() and fpath.stat().st_size > 0:
                                            logger.info('PDF file verified on disk: %s', fpath)
                                        else:
                                            logger.error('PDF file not found on disk or empty: %s', fpath)
                                            info['pdf_path'] = None
                                            
                                except Exception as e:
                                    logger.error('PDF download failed for IMO %s: %s', imo, e)
                                    info['pdf_path'], info['pdf_link'] = None, pdf_url
                            else:
                                logger.warning('PDF tag not found for IMO %s', imo)
                                info['pdf_path'], info['pdf_link'] = None, None
                        else:
                            logger.warning('PDF page request failed for IMO %s: %s', imo, pdf_resp.status)
                            info['pdf_path'], info['pdf_link'] = None, None
                else:
                    logger.debug('No PDF link found for IMO %s', imo)
                    info['pdf_path'], info['pdf_link'] = None, None

                inspections.append(info)
    return inspections

# ───────────────────────── Public API ───────────────────────────────────

async def cdi_data(doc_name: str, download_dir: str = 'downloads', max_pages: int = 5) -> Dict[str,Any]:
    """Return vessel table, inspection list, and PDFs."""
    logger.info("Starting scrape for %s", doc_name)

    async with aiohttp.ClientSession() as session:
        async with session.get(_build_login_url(doc_name)) as login_resp:
            login_resp.raise_for_status()
            text = await login_resp.text()
            session_id = _get_session_id(text)
            logger.info('Logged in, session=%s', session_id)

        vessels = await _fetch_vessel_list(session, session_id, max_pages)
        inspections = await _fetch_inspections(session, session_id, vessels, Path(download_dir))
        pdfs = [i.get('pdf_path') for i in inspections if i.get('pdf_path')]

        logger.info('Completed: %d vessels, %d inspections, %d PDFs', len(vessels), len(inspections), len(pdfs))
        
        # Log PDF paths for debugging
        if pdfs:
            logger.info('PDF paths found:')
            for pdf_path in pdfs:
                logger.info('  - %s', pdf_path)
        else:
            logger.warning('No PDF paths found in inspections')
            
        # Log inspection data for debugging
        pdf_count_in_inspections = sum(1 for i in inspections if i.get('pdf_path'))
        logger.info('Inspections with PDF paths: %d out of %d', pdf_count_in_inspections, len(inspections))

        return {'vessel_table': vessels, 'inspection_reports': inspections, 'pdf_paths': pdfs}





def get_scrape_results(doc_name: str) -> Dict[str, Any]:
    """
    Synchronous wrapper function to get scraping results.
    Returns a dictionary containing vessel table, inspection reports, and PDF paths.
    """
    import asyncio
    return asyncio.run(cdi_data(doc_name))


async def cdi_data_main(arguments: dict) -> Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
    """
    Main function to fetch and combine all scraping results.
    Returns a sequence of content objects with all vessel,
    inspection, and PDF data formatted as JSON.
    """
    # Extract doc_name from arguments
    logger.info("Arguments: %s", arguments)
    doc_name = arguments.get('doc_name', '')
    if not doc_name:
        return [types.TextContent(
            type="text",
            text="Error: doc_name parameter is required"
        )]
    
    try:
        # Fetch and combine data
        results = await cdi_data(doc_name)
        logger.info("Results: %s", results)
        combined_results = []
        
        # Convert vessel table to list of dictionaries
        vessel_data = results['vessel_table'].to_dict('records')
        
        # Log PDF information
        pdf_paths = results.get('pdf_paths', [])
        logger.info("PDF paths in results: %d", len(pdf_paths))
        for pdf_path in pdf_paths:
            logger.info("PDF path: %s", pdf_path)
        
        # Process each inspection report and combine with vessel data
        for inspection in results['inspection_reports']:
            vessel_info = next((v for v in vessel_data if v.get('IMO') == inspection.get('IMO')), {})
            combined_result = {
                **vessel_info,
                **inspection,
                'pdf_path': inspection.get('pdf_path'),
                'pdf_link': inspection.get('pdf_link')
            }
            combined_results.append(combined_result)
            
            # Log if this inspection has a PDF
            if inspection.get('pdf_path'):
                logger.info("Inspection for IMO %s has PDF: %s", inspection.get('IMO'), inspection.get('pdf_path'))
        
        # Log summary
        inspections_with_pdfs = sum(1 for r in combined_results if r.get('pdf_path'))
        logger.info("Combined results: %d total, %d with PDFs", len(combined_results), inspections_with_pdfs)
        
        # Format the response as TextContent
        if combined_results:
            return [types.TextContent(
                type="text",
                text=json.dumps(combined_results, indent=2)
            )]
        else:
            return [types.TextContent(
                type="text",
                text="No data could be retrieved from scraping."
            )]
            
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error during scraping: {str(e)}"
        )]

