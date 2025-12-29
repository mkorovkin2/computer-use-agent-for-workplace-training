"""Screenshot capture - resized to match pyautogui coordinates exactly."""

import base64
import hashlib
import logging
import subprocess
from typing import Optional, Tuple
from PIL import Image, ImageDraw
import pyautogui

logger = logging.getLogger(__name__)

SCREENSHOT_PATH = '/tmp/training_agent_screenshot.png'

# Screen size in pyautogui points - coordinates will match this exactly
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
logger.info(f"Screen size: {SCREEN_WIDTH}x{SCREEN_HEIGHT} points")

# Track last click position for overlay
_last_click = None


def get_screen_size() -> Tuple[int, int]:
    """Get screen size in pyautogui points."""
    return SCREEN_WIDTH, SCREEN_HEIGHT


def set_last_click(x: int, y: int):
    """Record where the last click happened."""
    global _last_click
    _last_click = (x, y)
    logger.info(f"Recorded click at ({x}, {y})")


def clear_last_click():
    """Clear the click marker."""
    global _last_click
    _last_click = None


def take_screenshot(show_click_marker: bool = True) -> Optional[str]:
    """Take screenshot resized to pyautogui coordinate space, with click marker overlay."""
    global _last_click

    try:
        subprocess.run(['screencapture', '-x', SCREENSHOT_PATH], check=True)

        img = Image.open(SCREENSHOT_PATH)
        img = img.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.Resampling.LANCZOS)

        # Draw click marker if we have a recent click
        if show_click_marker and _last_click is not None:
            x, y = _last_click
            draw = ImageDraw.Draw(img)

            # Draw a bright red crosshair + circle at click location
            marker_size = 20

            # Outer circle (red)
            draw.ellipse([x - marker_size, y - marker_size, x + marker_size, y + marker_size],
                        outline='red', width=3)
            # Inner circle (yellow)
            draw.ellipse([x - 8, y - 8, x + 8, y + 8],
                        outline='yellow', width=2)
            # Crosshair
            draw.line([x - marker_size - 5, y, x + marker_size + 5, y], fill='red', width=2)
            draw.line([x, y - marker_size - 5, x, y + marker_size + 5], fill='red', width=2)

            # Label with coordinates
            draw.text((x + marker_size + 5, y - 10), f"CLICK: ({x}, {y})", fill='red')

            logger.info(f"Drew click marker at ({x}, {y})")

        img.save(SCREENSHOT_PATH, 'PNG', optimize=True)

        with open(SCREENSHOT_PATH, 'rb') as f:
            data = f.read()

        return base64.b64encode(data).decode('utf-8')

    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        return None


def hash_screenshot(screenshot_b64: str) -> str:
    """Hash for detecting content changes."""
    return hashlib.md5(screenshot_b64.encode()).hexdigest()[:16]
