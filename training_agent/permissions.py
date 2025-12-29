"""macOS permission checking for the Training Agent."""

import logging
import os
import subprocess
import time
import pyautogui

logger = logging.getLogger(__name__)


def check_permissions() -> bool:
    """
    Check if necessary macOS permissions are granted.

    Returns:
        True if all permissions are granted, False otherwise
    """
    logger.info("\nChecking macOS permissions...")

    # Test screen recording
    if not _check_screen_recording():
        return False

    # Test pyautogui mouse control
    if not _check_accessibility():
        return False

    return True


def _check_screen_recording() -> bool:
    """Check if screen recording permission is granted."""
    try:
        subprocess.run(
            ['screencapture', '-x', '/tmp/permission_test.png'],
            check=True,
            capture_output=True
        )
        os.remove('/tmp/permission_test.png')
        logger.info("Screen Recording: Enabled")
        return True
    except Exception as e:
        logger.error("Screen Recording: DISABLED")
        logger.error("\nPERMISSION REQUIRED:")
        logger.error("   System Preferences -> Security & Privacy -> Privacy")
        logger.error("   -> Screen Recording -> Enable for Terminal\n")
        return False


def _check_accessibility() -> bool:
    """Check if accessibility permission is granted for mouse/keyboard control."""
    logger.info("Testing mouse/keyboard control...")
    try:
        # Get current position
        current_pos = pyautogui.position()
        logger.info(f"Current mouse position: {current_pos}")

        # Try to move mouse slightly
        pyautogui.moveRel(1, 1)
        time.sleep(0.1)
        new_pos = pyautogui.position()

        if current_pos == new_pos:
            logger.error("Mouse/Keyboard Control: DISABLED")
            logger.error("\nPERMISSION REQUIRED:")
            logger.error("   System Preferences -> Security & Privacy -> Privacy")
            logger.error("   -> Accessibility -> Enable for Terminal")
            logger.error("   -> Accessibility -> Enable for Python")
            logger.error("\n   After enabling, RESTART TERMINAL!\n")
            return False
        else:
            logger.info("Mouse/Keyboard Control: Working")
            # Move back
            pyautogui.moveRel(-1, -1)
            return True
    except Exception as e:
        logger.error(f"Mouse/Keyboard test failed: {e}")
        logger.error(
            "   Grant Accessibility permission to Terminal/Python and restart Terminal"
        )
        return False
