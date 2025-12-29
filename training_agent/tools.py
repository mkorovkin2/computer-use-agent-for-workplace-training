"""Anthropic API tool definitions."""

from .screenshot import get_screen_size

BETA_FLAGS = ["computer-use-2025-01-24", "prompt-caching-2024-07-31"]
DEFAULT_MODEL = "claude-sonnet-4-20250514"


def get_tools() -> list:
    """Get tool definitions. Screen size matches screenshot exactly."""
    w, h = get_screen_size()

    return [
        {
            "type": "computer_20250124",
            "name": "computer",
            "display_width_px": w,
            "display_height_px": h,
            "display_number": 1
        },
        {
            "name": "mark_video_watched",
            "description": "Mark training video as watched after it finishes playing.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "module_id": {"type": "string", "description": "Module identifier"},
                    "module_name": {"type": "string", "description": "Module name"}
                },
                "required": ["module_id"]
            }
        },
        {
            "name": "record_assessment_result",
            "description": "Record assessment result after seeing the results screen.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "module_id": {"type": "string", "description": "Module identifier"},
                    "passed": {"type": "boolean", "description": "Whether passed"},
                    "questions_total": {"type": "integer", "description": "Total questions"},
                    "questions_correct": {"type": "integer", "description": "Correct answers"}
                },
                "required": ["module_id", "passed"]
            }
        },
        {
            "name": "get_progress",
            "description": "Get training progress summary.",
            "input_schema": {"type": "object", "properties": {}, "required": []}
        },
        {
            "name": "get_failed_assessments",
            "description": "Get list of failed assessments to retry.",
            "input_schema": {"type": "object", "properties": {}, "required": []}
        },
        {
            "name": "cache_action",
            "description": "Cache UI element coordinates for reuse.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action_name": {"type": "string", "description": "Name for cached location"},
                    "x": {"type": "integer", "description": "X coordinate"},
                    "y": {"type": "integer", "description": "Y coordinate"}
                },
                "required": ["action_name", "x", "y"]
            }
        },
        {
            "name": "use_cached_action",
            "description": "Click a previously cached location.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action_name": {"type": "string", "description": "Cached action name"}
                },
                "required": ["action_name"]
            }
        },
        {
            "name": "list_cached_actions",
            "description": "List all cached UI locations.",
            "input_schema": {"type": "object", "properties": {}, "required": []}
        },
        {
            "name": "note_confusion",
            "description": "Log confusing UI or unclear instructions.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "What was confusing"},
                    "location": {"type": "string", "description": "Where it occurred"},
                    "severity": {"type": "string", "enum": ["minor", "moderate", "blocking"]}
                },
                "required": ["description"]
            }
        }
    ]
