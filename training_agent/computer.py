"""Computer control - mouse and keyboard operations."""

import logging
import time
import pyautogui

from .screenshot import take_screenshot, hash_screenshot, set_last_click

logger = logging.getLogger(__name__)

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.1


def execute_computer_tool(tool_input: dict, scroll_counter: dict, actions_cache: dict = None) -> list:
    """Execute computer use tool action. Coordinates are used DIRECTLY - no scaling."""
    if actions_cache is None:
        actions_cache = {}

    action = tool_input.get("action")

    if action == "screenshot":
        screenshot = take_screenshot(show_click_marker=True)
        if screenshot:
            return [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot}}]
        return [{"type": "text", "text": "Screenshot failed"}]

    elif action == "mouse_move":
        x, y = tool_input.get("coordinate", [0, 0])
        pyautogui.moveTo(x, y)
        return [{"type": "text", "text": f"Moved to ({x}, {y})"}]

    elif action == "left_click":
        x, y = tool_input.get("coordinate", [0, 0])
        logger.info(f"CLICK at ({x}, {y})")
        set_last_click(x, y)  # Record for overlay
        pyautogui.click(x, y)
        time.sleep(0.5)
        screenshot = take_screenshot(show_click_marker=True)
        return [
            {"type": "text", "text": f"Clicked ({x}, {y}) - RED MARKER shows where click landed"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot}}
        ]

    elif action == "right_click":
        x, y = tool_input.get("coordinate", [0, 0])
        set_last_click(x, y)
        pyautogui.rightClick(x, y)
        time.sleep(0.5)
        screenshot = take_screenshot(show_click_marker=True)
        return [
            {"type": "text", "text": f"Right clicked ({x}, {y}) - RED MARKER shows where click landed"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot}}
        ]

    elif action == "double_click":
        x, y = tool_input.get("coordinate", [0, 0])
        set_last_click(x, y)
        pyautogui.doubleClick(x, y)
        time.sleep(0.5)
        screenshot = take_screenshot(show_click_marker=True)
        return [
            {"type": "text", "text": f"Double clicked ({x}, {y}) - RED MARKER shows where click landed"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot}}
        ]

    elif action == "left_click_drag":
        start = tool_input.get("start_coordinate", [0, 0])
        end = tool_input.get("coordinate", [0, 0])
        set_last_click(end[0], end[1])  # Mark end position
        pyautogui.moveTo(start[0], start[1])
        time.sleep(0.1)
        pyautogui.mouseDown()
        pyautogui.moveTo(end[0], end[1], duration=0.5)
        pyautogui.mouseUp()
        time.sleep(0.5)
        screenshot = take_screenshot(show_click_marker=True)
        return [
            {"type": "text", "text": f"Dragged from ({start[0]}, {start[1]}) to ({end[0]}, {end[1]}) - RED MARKER shows end position"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot}}
        ]

    elif action == "type":
        text = tool_input.get("text", "")
        logger.info(f"TYPE: {text[:50]}...")
        time.sleep(0.3)
        pyautogui.write(text, interval=0.02)
        time.sleep(0.5)
        screenshot = take_screenshot()
        return [
            {"type": "text", "text": f"Typed: {text[:100]}"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot}}
        ]

    elif action == "key":
        key = tool_input.get("text", "")
        if '+' in key:
            pyautogui.hotkey(*key.split('+'))
        else:
            pyautogui.press(key)
        time.sleep(0.5)
        screenshot = take_screenshot()
        return [
            {"type": "text", "text": f"Pressed: {key}"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot}}
        ]

    elif action == "scroll":
        coord = tool_input.get("coordinate", [756, 491])
        direction = tool_input.get("scroll_direction", "down")
        amount = tool_input.get("scroll_amount", 3)

        pyautogui.moveTo(coord[0], coord[1])

        before = take_screenshot()
        before_hash = hash_screenshot(before) if before else None

        if direction == "down":
            pyautogui.scroll(-amount * 100)
        elif direction == "up":
            pyautogui.scroll(amount * 100)
        elif direction == "left":
            pyautogui.hscroll(-amount * 100)
        elif direction == "right":
            pyautogui.hscroll(amount * 100)

        time.sleep(1.0)
        scroll_counter['count'] += 1

        after = take_screenshot()
        after_hash = hash_screenshot(after) if after else None
        changed = before_hash != after_hash

        msg = f"Scrolled {direction} by {amount}."
        if not changed:
            msg += " Content unchanged - may be at end."

        return [
            {"type": "text", "text": msg},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": after}}
        ]

    elif action == "wait":
        duration = tool_input.get("duration", 1)
        time.sleep(duration)
        screenshot = take_screenshot()
        return [
            {"type": "text", "text": f"Waited {duration}s"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot}}
        ]

    return [{"type": "text", "text": f"Unknown action: {action}"}]
