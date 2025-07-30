#!/usr/bin/env python3
"""Auto-update checker for mcp-google-workspace"""

import asyncio
import subprocess
import sys
from packaging import version
import aiohttp
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json

logger = logging.getLogger(__name__)

PYPI_API_URL = "https://pypi.org/pypi/mcp-google-workspace/json"
UPDATE_CHECK_FILE = Path.home() / ".config" / "mcp-google" / ".last_update_check.json"
UPDATE_CHECK_INTERVAL = timedelta(hours=24)  # Check once per day

async def get_latest_version():
    """Fetch the latest version from PyPI"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PYPI_API_URL, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["info"]["version"]
    except Exception as e:
        logger.debug(f"Failed to check for updates: {e}")
    return None

def get_current_version():
    """Get the currently installed version"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "mcp-google-workspace"],
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.split('\n'):
            if line.startswith('Version:'):
                return line.split(':', 1)[1].strip()
    except Exception:
        return None

def should_check_for_update():
    """Check if we should check for updates based on last check time"""
    UPDATE_CHECK_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    if UPDATE_CHECK_FILE.exists():
        try:
            with open(UPDATE_CHECK_FILE, 'r') as f:
                data = json.load(f)
                last_check = datetime.fromisoformat(data.get('last_check', ''))
                if datetime.now() - last_check < UPDATE_CHECK_INTERVAL:
                    return False
        except Exception:
            pass
    
    return True

def save_last_check():
    """Save the last update check time"""
    UPDATE_CHECK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(UPDATE_CHECK_FILE, 'w') as f:
        json.dump({'last_check': datetime.now().isoformat()}, f)

async def check_for_updates():
    """Check if a newer version is available"""
    if not should_check_for_update():
        return None
    
    current = get_current_version()
    if not current:
        return None
    
    latest = await get_latest_version()
    if not latest:
        return None
    
    save_last_check()
    
    try:
        if version.parse(latest) > version.parse(current):
            return {
                'current': current,
                'latest': latest,
                'update_available': True
            }
    except Exception:
        pass
    
    return None

def notify_update(update_info):
    """Notify user about available update"""
    if update_info and update_info.get('update_available'):
        logger.info(
            f"\n🔄 Update available for mcp-google-workspace: "
            f"{update_info['current']} → {update_info['latest']}\n"
            f"Run 'claude mcp update mcp-google-workspace' to update.\n"
        )