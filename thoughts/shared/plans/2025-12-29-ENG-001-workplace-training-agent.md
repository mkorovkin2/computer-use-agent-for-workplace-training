# Workplace Training Platform Computer Use Agent - Implementation Plan

## Overview

Create a Python-based computer use agent (modeled after the Twitter agent in `/Users/mkorovkin/Desktop/twitter-computer-use-agent`) that autonomously navigates and tests a workplace training platform. The agent will:

1. Watch training videos
2. Answer assessment questions (multiple choice, free text, drag-and-drop) using Claude's reasoning
3. Progress through training modules
4. Retry failed assessments until all pass
5. Report completion status

## Current State Analysis

### Reference Implementation (Twitter Agent)
The reference repository provides a complete, working computer use agent with:
- **Core architecture**: Agentic loop with Claude analyzing screenshots and deciding actions
- **Computer control**: PyAutoGUI for mouse/keyboard operations
- **Screenshot processing**: macOS screencapture + PIL resizing for API limits
- **State management**: JSON-based persistence for tracking progress
- **Error handling**: Errors fed back to Claude for adaptive recovery
- **Token management**: Old screenshots truncated to stay within context
- **Permission checking**: Validates macOS Screen Recording + Accessibility permissions

### Key Files to Model After:
- `twitter_agent/agent.py` - Core agentic loop orchestration
- `twitter_agent/computer.py` - Mouse/keyboard/screenshot execution
- `twitter_agent/screenshot.py` - Screenshot capture and processing
- `twitter_agent/state.py` - Progress state management
- `twitter_agent/tools.py` - Anthropic API tool definitions
- `twitter_agent/config.py` - Configuration management
- `twitter_agent/permissions.py` - macOS permission verification

### This Repository
Currently empty except for `.claude/` configuration framework. No application code exists yet.

## Desired End State

A fully functional Python script that:
1. Takes control of the screen where a workplace training platform is already open (user logged in)
2. Autonomously navigates through training modules
3. Watches videos (waits for completion or skips if allowed)
4. Answers all types of assessment questions using Claude's reasoning
5. Tracks which modules/assessments have been completed
6. Retries failed assessments
7. Reports final completion status
8. Handles confusion/unexpected states gracefully

### Verification:
- Agent successfully completes at least one training module end-to-end
- Agent correctly answers quiz questions using contextual reasoning
- Agent recovers from navigation errors
- Agent tracks and retries failed assessments
- State persists between runs

## What We're NOT Doing

- **NOT** building browser automation (Selenium/Playwright) - we use screenshot + mouse/keyboard like the reference
- **NOT** handling login/authentication - user will be logged in before starting
- **NOT** creating a web server or API - this is a standalone script
- **NOT** integrating with any external APIs besides Anthropic (no OpenAI like the Twitter agent)
- **NOT** adding real-time notifications or webhooks
- **NOT** supporting multiple simultaneous users/sessions

## Implementation Approach

We will create a modular Python package mirroring the Twitter agent structure but adapted for workplace training testing. The key difference is the system prompt and state tracking logic.

## Phase 1: Core Infrastructure Setup

### Overview
Set up the basic project structure, dependencies, and reusable components copied from the reference implementation.

### Changes Required:

#### 1. Create Package Structure
**Directory**: `training_agent/`

Create the following files:
```
training_agent/
├── __init__.py
├── agent.py          # Core agentic loop
├── computer.py       # Mouse/keyboard control (copy from reference)
├── screenshot.py     # Screenshot capture (copy from reference)
├── state.py          # Training progress state
├── tools.py          # Anthropic tool definitions
├── config.py         # Configuration management
└── permissions.py    # macOS permissions (copy from reference)
```

#### 2. requirements.txt
**File**: `requirements.txt`

```
anthropic>=0.40.0
python-dotenv>=1.0.0
Pillow>=10.0.0
pyautogui>=0.9.54
```

#### 3. Main Entry Point
**File**: `main.py`

```python
#!/usr/bin/env python3
"""
Workplace Training Platform Test Agent

A computer use agent that autonomously navigates and tests
a workplace training platform by watching videos, answering
assessments, and verifying user flow completion.
"""

from training_agent import TrainingAgent


def main():
    agent = TrainingAgent()
    agent.run()


if __name__ == "__main__":
    main()
```

#### 4. Package Init
**File**: `training_agent/__init__.py`

```python
"""Training Agent Package - Computer Use Agent for Workplace Training Testing"""

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent.log')
    ]
)

from .agent import TrainingAgent

__all__ = ['TrainingAgent']
```

#### 5. Screenshot Module (Copy from Reference)
**File**: `training_agent/screenshot.py`

Copy directly from `/Users/mkorovkin/Desktop/twitter-computer-use-agent/twitter_agent/screenshot.py`

No modifications needed - screenshot logic is platform-agnostic.

#### 6. Computer Module (Copy from Reference)
**File**: `training_agent/computer.py`

Copy directly from `/Users/mkorovkin/Desktop/twitter-computer-use-agent/twitter_agent/computer.py`

No modifications needed - mouse/keyboard control is platform-agnostic.

#### 7. Permissions Module (Copy from Reference)
**File**: `training_agent/permissions.py`

Copy directly from `/Users/mkorovkin/Desktop/twitter-computer-use-agent/twitter_agent/permissions.py`

No modifications needed - permission checking is platform-agnostic.

### Success Criteria:

#### Automated Verification:
- [ ] All files created in correct locations: `ls -la training_agent/`
- [ ] No Python syntax errors: `python -m py_compile training_agent/*.py`
- [ ] Package imports successfully: `python -c "from training_agent import TrainingAgent"`

#### Manual Verification:
- [ ] Directory structure matches plan
- [ ] Copied files are identical to reference

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation before proceeding to Phase 2.

---

## Phase 2: Configuration and State Management

### Overview
Create the configuration system and training-specific state management for tracking module/assessment progress.

### Changes Required:

#### 1. Configuration Module
**File**: `training_agent/config.py`

```python
"""Configuration management for the Training Agent."""

import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class AgentConfig:
    """Configuration for the Training Agent."""

    def __init__(self):
        load_dotenv()

        # API Configuration
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        if not self.anthropic_api_key.startswith('sk-ant-'):
            raise ValueError("Invalid ANTHROPIC_API_KEY format")

        # Run Configuration
        self.run_duration_minutes = int(os.getenv('RUN_DURATION_MINUTES', '60'))
        if not 1 <= self.run_duration_minutes <= 480:
            raise ValueError("RUN_DURATION_MINUTES must be between 1 and 480")

        # Retry Configuration
        self.max_assessment_retries = int(os.getenv('MAX_ASSESSMENT_RETRIES', '3'))

        # Screen Configuration (for API tool definition)
        self.screen_width = 1920
        self.screen_height = 1080
        self._detect_screen_size()

        logger.info(f"Configuration loaded: {self.run_duration_minutes}min duration, "
                   f"{self.screen_width}x{self.screen_height} screen")

    def _detect_screen_size(self):
        """Attempt to detect actual screen size."""
        try:
            import subprocess
            result = subprocess.run(
                ['system_profiler', 'SPDisplaysDataType'],
                capture_output=True, text=True
            )
            # Parse output for resolution if needed
            # For now, use defaults
        except Exception as e:
            logger.debug(f"Screen detection failed, using defaults: {e}")
```

#### 2. State Management Module
**File**: `training_agent/state.py`

```python
"""State management for tracking training progress."""

import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Set, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

STATE_FILE = 'training_progress.json'


@dataclass
class ModuleProgress:
    """Progress for a single training module."""
    module_id: str
    module_name: str
    video_watched: bool = False
    assessment_attempts: int = 0
    assessment_passed: bool = False
    questions_answered: int = 0
    questions_correct: int = 0
    last_attempt: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'ModuleProgress':
        return cls(**data)


class TrainingState:
    """Manages training progress state with persistence."""

    def __init__(self):
        self.modules: Dict[str, ModuleProgress] = {}
        self.current_module: Optional[str] = None
        self.session_start: str = datetime.now().isoformat()
        self._load()

    def _load(self):
        """Load state from disk."""
        try:
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
                self.modules = {
                    k: ModuleProgress.from_dict(v)
                    for k, v in data.get('modules', {}).items()
                }
                logger.info(f"Loaded progress for {len(self.modules)} modules")
        except FileNotFoundError:
            logger.info("No previous progress found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading state: {e}")

    def save(self):
        """Save state to disk."""
        try:
            data = {
                'modules': {k: v.to_dict() for k, v in self.modules.items()},
                'last_saved': datetime.now().isoformat()
            }
            with open(STATE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("State saved")
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def get_or_create_module(self, module_id: str, module_name: str = "") -> ModuleProgress:
        """Get existing module progress or create new entry."""
        if module_id not in self.modules:
            self.modules[module_id] = ModuleProgress(
                module_id=module_id,
                module_name=module_name or module_id
            )
            self.save()
        return self.modules[module_id]

    def mark_video_watched(self, module_id: str):
        """Mark video as watched for a module."""
        module = self.get_or_create_module(module_id)
        module.video_watched = True
        self.save()
        logger.info(f"Video watched for module: {module_id}")

    def record_assessment_attempt(self, module_id: str, passed: bool,
                                   questions_total: int, questions_correct: int):
        """Record an assessment attempt."""
        module = self.get_or_create_module(module_id)
        module.assessment_attempts += 1
        module.assessment_passed = passed
        module.questions_answered = questions_total
        module.questions_correct = questions_correct
        module.last_attempt = datetime.now().isoformat()
        self.save()
        logger.info(f"Assessment attempt for {module_id}: "
                   f"{'PASSED' if passed else 'FAILED'} "
                   f"({questions_correct}/{questions_total})")

    def get_incomplete_modules(self) -> list:
        """Get list of modules that haven't been fully completed."""
        incomplete = []
        for module_id, progress in self.modules.items():
            if not progress.assessment_passed:
                incomplete.append({
                    'id': module_id,
                    'name': progress.module_name,
                    'video_watched': progress.video_watched,
                    'attempts': progress.assessment_attempts
                })
        return incomplete

    def get_failed_assessments(self) -> list:
        """Get list of failed assessments that need retry."""
        failed = []
        for module_id, progress in self.modules.items():
            if progress.video_watched and not progress.assessment_passed:
                failed.append({
                    'id': module_id,
                    'name': progress.module_name,
                    'attempts': progress.assessment_attempts
                })
        return failed

    def get_summary(self) -> str:
        """Get summary of training progress."""
        total = len(self.modules)
        videos_watched = sum(1 for m in self.modules.values() if m.video_watched)
        assessments_passed = sum(1 for m in self.modules.values() if m.assessment_passed)
        total_attempts = sum(m.assessment_attempts for m in self.modules.values())

        return (f"Training Progress Summary:\n"
                f"  Modules tracked: {total}\n"
                f"  Videos watched: {videos_watched}\n"
                f"  Assessments passed: {assessments_passed}/{total}\n"
                f"  Total assessment attempts: {total_attempts}\n"
                f"  Session started: {self.session_start}")

    @staticmethod
    def hash_content(content: str) -> str:
        """Hash content for deduplication."""
        normalized = content.strip().lower()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]
```

#### 3. Environment Template
**File**: `.env.example`

```
# Anthropic API Key (required)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Run duration in minutes (default: 60)
RUN_DURATION_MINUTES=60

# Maximum retries for failed assessments (default: 3)
MAX_ASSESSMENT_RETRIES=3
```

### Success Criteria:

#### Automated Verification:
- [ ] Config loads without error: `python -c "from training_agent.config import AgentConfig; c = AgentConfig()" 2>&1 | grep -v "ANTHROPIC_API_KEY"` (will fail without key, but syntax should be valid)
- [ ] State module works: `python -c "from training_agent.state import TrainingState; s = TrainingState(); print(s.get_summary())"`
- [ ] No Python syntax errors: `python -m py_compile training_agent/config.py training_agent/state.py`

#### Manual Verification:
- [ ] `.env.example` created with proper template
- [ ] State file `training_progress.json` created on first run

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation before proceeding to Phase 3.

---

## Phase 3: Tool Definitions

### Overview
Define the Anthropic API tools for computer control and training-specific operations.

### Changes Required:

#### 1. Tools Module
**File**: `training_agent/tools.py`

```python
"""Anthropic API tool definitions for the Training Agent."""

BETA_FLAGS = ["computer-use-2025-01-24", "prompt-caching-2024-07-31"]
DEFAULT_MODEL = "claude-sonnet-4-20250514"


def get_tools(screen_width: int = 1920, screen_height: int = 1080) -> list:
    """Get tool definitions for the Anthropic API."""
    return [
        # Computer control tool (Anthropic's built-in)
        {
            "type": "computer_20250124",
            "name": "computer",
            "display_width_px": screen_width,
            "display_height_px": screen_height,
            "display_number": 1
        },

        # Mark video as watched
        {
            "name": "mark_video_watched",
            "description": (
                "Mark the current training video as watched. Call this when you have "
                "confirmed the video has finished playing or you have watched enough "
                "to understand the content for the assessment."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "module_id": {
                        "type": "string",
                        "description": "Unique identifier for the module (e.g., module title or number)"
                    },
                    "module_name": {
                        "type": "string",
                        "description": "Human-readable name of the module"
                    }
                },
                "required": ["module_id"]
            }
        },

        # Record assessment result
        {
            "name": "record_assessment_result",
            "description": (
                "Record the result of a completed assessment. Call this after "
                "submitting an assessment and seeing the results screen."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "module_id": {
                        "type": "string",
                        "description": "Module identifier for this assessment"
                    },
                    "passed": {
                        "type": "boolean",
                        "description": "Whether the assessment was passed"
                    },
                    "questions_total": {
                        "type": "integer",
                        "description": "Total number of questions in the assessment"
                    },
                    "questions_correct": {
                        "type": "integer",
                        "description": "Number of questions answered correctly"
                    }
                },
                "required": ["module_id", "passed"]
            }
        },

        # Get training progress
        {
            "name": "get_progress",
            "description": (
                "Get a summary of training progress including modules completed, "
                "videos watched, assessments passed, and any failed assessments "
                "that need to be retried."
            ),
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },

        # Get failed assessments for retry
        {
            "name": "get_failed_assessments",
            "description": (
                "Get a list of assessments that were failed and need to be retried. "
                "Use this to determine which modules to revisit."
            ),
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },

        # Cache UI element location
        {
            "name": "cache_action",
            "description": (
                "Cache the coordinates of a UI element for later reuse. Useful for "
                "elements like 'Next' buttons, navigation menu items, or other "
                "frequently clicked elements."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "action_name": {
                        "type": "string",
                        "description": "Descriptive name for this cached location (e.g., 'next_button', 'menu_courses')"
                    },
                    "x": {
                        "type": "integer",
                        "description": "X coordinate of the element"
                    },
                    "y": {
                        "type": "integer",
                        "description": "Y coordinate of the element"
                    }
                },
                "required": ["action_name", "x", "y"]
            }
        },

        # Use cached location
        {
            "name": "use_cached_action",
            "description": (
                "Click on a previously cached UI element location. Use this for "
                "elements you've found before that appear in consistent positions."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "action_name": {
                        "type": "string",
                        "description": "Name of the cached action to use"
                    }
                },
                "required": ["action_name"]
            }
        },

        # List cached actions
        {
            "name": "list_cached_actions",
            "description": "List all cached UI element locations.",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },

        # Note confusion or problem
        {
            "name": "note_confusion",
            "description": (
                "Log that you encountered something confusing or unexpected. "
                "This helps track usability issues with the training platform. "
                "Use this when the UI is unclear, instructions are ambiguous, "
                "or you're not sure how to proceed."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of what was confusing"
                    },
                    "location": {
                        "type": "string",
                        "description": "Where in the training platform this occurred"
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["minor", "moderate", "blocking"],
                        "description": "How severe the confusion is"
                    }
                },
                "required": ["description"]
            }
        }
    ]
```

### Success Criteria:

#### Automated Verification:
- [ ] Tools module imports: `python -c "from training_agent.tools import get_tools, BETA_FLAGS, DEFAULT_MODEL; print(len(get_tools()))"`
- [ ] Tools return correct structure: `python -c "from training_agent.tools import get_tools; tools = get_tools(); assert tools[0]['type'] == 'computer_20250124'"`
- [ ] No syntax errors: `python -m py_compile training_agent/tools.py`

#### Manual Verification:
- [ ] All 8 tools defined (computer + 7 custom)
- [ ] Tool descriptions are clear and actionable

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation before proceeding to Phase 4.

---

## Phase 4: Core Agent Logic

### Overview
Implement the main agent class with the agentic loop, system prompt, and tool execution.

### Changes Required:

#### 1. Agent Module
**File**: `training_agent/agent.py`

```python
"""Core Training Agent with agentic loop."""

import time
import logging
from datetime import datetime, timedelta
from typing import Optional

import anthropic
import pyautogui

from .config import AgentConfig
from .state import TrainingState
from .tools import get_tools, BETA_FLAGS, DEFAULT_MODEL
from .computer import execute_computer_tool
from .permissions import check_permissions

logger = logging.getLogger(__name__)


class TrainingAgent:
    """
    Computer Use Agent for testing workplace training platforms.

    This agent autonomously navigates training modules, watches videos,
    answers assessment questions, and tracks progress through the platform.
    """

    def __init__(self):
        self.config = AgentConfig()
        self.client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
        self.state = TrainingState()

        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=self.config.run_duration_minutes)

        self.actions_cache = {}
        self.confusion_log = []

        logger.info(f"Training Agent initialized. Will run until {self.end_time}")

    def _build_system_prompt(self) -> str:
        """Build the system prompt for Claude."""
        return f"""You are a computer use agent testing a workplace training platform. Your goal is to navigate through the platform as a real user would, completing training modules by watching videos and passing assessments.

## Your Primary Objectives:
1. Find and start available training modules
2. Watch training videos (wait for them to complete or find skip/continue buttons)
3. Complete assessments by answering questions thoughtfully
4. Track your progress and retry failed assessments
5. Report any confusing or unclear parts of the platform

## Navigation Guidelines:

### Finding Content:
- Look for navigation menus, "Courses", "My Learning", "Training" sections
- Look for "Start", "Continue", "Resume" buttons on modules
- Training modules typically show as cards or list items with titles and progress indicators

### Video Watching:
- Videos may auto-play or require clicking a play button
- Wait for videos to complete - look for progress bars reaching 100%
- Some platforms have "Skip" or "Continue" buttons that appear after watching
- If a video seems stuck, try clicking on the video player or looking for controls
- After video completion, look for "Next", "Continue to Assessment", or similar buttons

### Assessment Answering:
- READ each question carefully before answering
- For multiple choice: analyze all options and select the most accurate answer based on the video content and your reasoning
- For free text: provide thoughtful, complete answers that address the question
- For drag-and-drop: match items logically based on the training content
- Look for "Submit", "Next Question", or "Finish" buttons
- After submitting, check for results - look for scores, pass/fail indicators

### Answer Strategy:
- Use your reasoning to determine the best answer
- Consider what a well-informed employee would answer after watching the training
- For safety/compliance questions, err on the side of caution
- For procedural questions, follow the exact steps mentioned in training
- If genuinely unsure, make your best educated guess

## Error Recovery:

### If you get confused:
1. Take a screenshot to assess current state
2. Use the `note_confusion` tool to log the issue
3. Try clicking obvious navigation elements (home, back, menu)
4. If completely stuck after 3 attempts, try refreshing or navigating to a known location

### If you accidentally navigate away:
1. Look for breadcrumbs, back buttons, or navigation menus
2. Try to return to the training list/dashboard
3. Find and resume the module you were working on

### If an action doesn't work:
1. Wait 1-2 seconds and try again
2. Try clicking slightly different coordinates
3. Look for alternative buttons or links that accomplish the same goal

## Tool Usage:

- Use `mark_video_watched` after confirming a video has completed
- Use `record_assessment_result` after seeing assessment results
- Use `get_progress` periodically to check your status
- Use `get_failed_assessments` to find modules that need retry
- Use `cache_action` for frequently-used buttons (Next, Continue, etc.)
- Use `note_confusion` whenever something is unclear or unexpected

## Important Reminders:

- ALWAYS take a screenshot before making decisions about what to click
- ALWAYS verify actions succeeded by checking the resulting screenshot
- Be patient with video loading and playback
- Don't rush through assessments - read questions carefully
- If you fail an assessment, note what went wrong and try to learn from it
- Track all modules you discover, even if you don't complete them immediately

## Session Info:
- Session started: {self.start_time.isoformat()}
- Session ends: {self.end_time.isoformat()}
- Max assessment retries: {self.config.max_assessment_retries}

Begin by taking a screenshot to see the current state of the training platform.
"""

    def _truncate_old_images(self, messages: list, keep_recent: int = 3) -> list:
        """Truncate old images from messages to manage token usage."""
        image_count = 0

        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "tool_result":
                            result_content = item.get("content", [])
                            if isinstance(result_content, list):
                                for result_item in result_content:
                                    if result_item.get("type") == "image":
                                        image_count += 1
                                        if image_count > keep_recent:
                                            result_item["type"] = "text"
                                            result_item["text"] = "[Previous screenshot removed to save context]"
                                            if "source" in result_item:
                                                del result_item["source"]

        return messages

    def _execute_custom_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a custom (non-computer) tool."""

        if tool_name == "mark_video_watched":
            module_id = tool_input.get("module_id", "unknown")
            module_name = tool_input.get("module_name", module_id)
            self.state.get_or_create_module(module_id, module_name)
            self.state.mark_video_watched(module_id)
            return f"Video marked as watched for module: {module_name}"

        elif tool_name == "record_assessment_result":
            module_id = tool_input.get("module_id", "unknown")
            passed = tool_input.get("passed", False)
            questions_total = tool_input.get("questions_total", 0)
            questions_correct = tool_input.get("questions_correct", 0)
            self.state.record_assessment_attempt(
                module_id, passed, questions_total, questions_correct
            )
            status = "PASSED" if passed else "FAILED"
            return f"Assessment result recorded: {status} ({questions_correct}/{questions_total})"

        elif tool_name == "get_progress":
            return self.state.get_summary()

        elif tool_name == "get_failed_assessments":
            failed = self.state.get_failed_assessments()
            if not failed:
                return "No failed assessments. All completed assessments have passed!"
            result = "Failed assessments that need retry:\n"
            for item in failed:
                result += f"  - {item['name']} (ID: {item['id']}, attempts: {item['attempts']})\n"
            return result

        elif tool_name == "cache_action":
            action_name = tool_input.get("action_name", "")
            x = tool_input.get("x", 0)
            y = tool_input.get("y", 0)
            if action_name:
                self.actions_cache[action_name] = (x, y)
                return f"Cached location '{action_name}' at ({x}, {y})"
            return "Error: action_name is required"

        elif tool_name == "use_cached_action":
            action_name = tool_input.get("action_name", "")
            if action_name in self.actions_cache:
                x, y = self.actions_cache[action_name]
                pyautogui.click(x, y)
                time.sleep(0.5)
                return f"Clicked cached location '{action_name}' at ({x}, {y})"
            return f"Error: No cached action named '{action_name}'. Available: {list(self.actions_cache.keys())}"

        elif tool_name == "list_cached_actions":
            if not self.actions_cache:
                return "No cached actions yet."
            result = "Cached UI locations:\n"
            for name, (x, y) in self.actions_cache.items():
                result += f"  - {name}: ({x}, {y})\n"
            return result

        elif tool_name == "note_confusion":
            description = tool_input.get("description", "Unknown issue")
            location = tool_input.get("location", "Unknown location")
            severity = tool_input.get("severity", "moderate")

            confusion_entry = {
                "timestamp": datetime.now().isoformat(),
                "description": description,
                "location": location,
                "severity": severity
            }
            self.confusion_log.append(confusion_entry)
            logger.warning(f"CONFUSION LOGGED [{severity}]: {description} at {location}")
            return f"Confusion noted: {description}"

        return f"Unknown tool: {tool_name}"

    def agentic_loop(self, initial_task: str, max_iterations: int = 200) -> list:
        """Main agentic loop - Claude analyzes screenshots and decides actions."""

        messages = []
        iteration = 0

        # Build system message with cache control
        system = [{
            "type": "text",
            "text": initial_task + """

IMPORTANT INSTRUCTIONS:
After each action, carefully evaluate the screenshot to verify the action succeeded.
Explicitly state your evaluation: "I see that [describe what you see]... The action [succeeded/failed] because [reason]..."

If an action didn't work, analyze what went wrong and try a different approach.
Only proceed to the next step when you confirm the current step succeeded.

Work systematically through the training platform. Take your time with assessments.
""",
            "cache_control": {"type": "ephemeral"}
        }]

        # Initial message to start the loop
        messages.append({
            "role": "user",
            "content": "Please begin by taking a screenshot to see the current state of the training platform."
        })

        while iteration < max_iterations and datetime.now() < self.end_time:
            iteration += 1
            remaining = (self.end_time - datetime.now()).total_seconds() / 60

            logger.info(f"=== Iteration {iteration} | {remaining:.1f} min remaining | "
                       f"Modules: {len(self.state.modules)} ===")

            try:
                # Build API parameters
                tools = get_tools(self.config.screen_width, self.config.screen_height)

                api_params = {
                    "model": DEFAULT_MODEL,
                    "max_tokens": 4096,
                    "system": system,
                    "tools": tools,
                    "messages": messages,
                    "betas": BETA_FLAGS
                }

                # Enable extended thinking
                api_params["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": 2048
                }

                # Call Claude API
                response = self.client.beta.messages.create(**api_params)

                # Log response blocks
                for block in response.content:
                    if hasattr(block, 'type'):
                        if block.type == "thinking":
                            logger.debug(f"Thinking: {block.thinking[:200]}...")
                        elif block.type == "text":
                            logger.info(f"Claude: {block.text[:300]}...")
                        elif block.type == "tool_use":
                            logger.info(f"Tool: {block.name} with {block.input}")

                # Add response to messages
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Process tool calls
                tool_results = []
                has_tool_use = False

                for block in response.content:
                    if hasattr(block, 'type') and block.type == "tool_use":
                        has_tool_use = True

                        if block.name == "computer":
                            # Execute computer control
                            scroll_counter = {'count': 0}
                            result = execute_computer_tool(
                                block.input,
                                scroll_counter,
                                self.actions_cache
                            )
                        else:
                            # Execute custom tool
                            result_text = self._execute_custom_tool(block.name, block.input)
                            result = [{"type": "text", "text": result_text}]

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })

                # If no tool calls, Claude is done
                if not has_tool_use:
                    logger.info("No tool calls - Claude has finished")
                    return messages

                # Add tool results to messages
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # Truncate old images to manage context
                messages = self._truncate_old_images(messages, keep_recent=3)

            except Exception as e:
                logger.error(f"Error in agent loop: {e}")
                messages.append({
                    "role": "user",
                    "content": f"Error occurred: {str(e)}. Please try a different approach."
                })

        logger.info("Agent loop completed (time limit or max iterations reached)")
        return messages

    def run(self):
        """Main entry point to run the agent."""
        logger.info("=" * 60)
        logger.info("WORKPLACE TRAINING TEST AGENT")
        logger.info("=" * 60)

        # Check permissions
        if not check_permissions():
            logger.error("Required permissions not granted. Please enable them and try again.")
            return

        # Warn user to have training platform open
        logger.info("\n*** IMPORTANT ***")
        logger.info("Make sure the training platform is open and visible on screen.")
        logger.info("You should be logged in and on the main training page.")
        logger.info("Starting in 5 seconds...")
        time.sleep(5)

        try:
            # Build task and run
            task = self._build_system_prompt()
            messages = self.agentic_loop(task, max_iterations=200)

            # Log final summary
            logger.info("\n" + "=" * 60)
            logger.info("SESSION COMPLETE")
            logger.info("=" * 60)
            logger.info(self.state.get_summary())

            if self.confusion_log:
                logger.info("\nConfusion/Issues Logged:")
                for entry in self.confusion_log:
                    logger.info(f"  [{entry['severity']}] {entry['description']} at {entry['location']}")

        except KeyboardInterrupt:
            logger.info("\nAgent stopped by user (Ctrl+C)")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources and save state."""
        logger.info("Cleaning up...")
        self.state.save()

        # Save confusion log if any
        if self.confusion_log:
            import json
            with open('confusion_log.json', 'w') as f:
                json.dump(self.confusion_log, f, indent=2)
            logger.info(f"Saved {len(self.confusion_log)} confusion entries to confusion_log.json")

        logger.info("Agent shut down successfully")
```

### Success Criteria:

#### Automated Verification:
- [ ] Agent module imports: `python -c "from training_agent.agent import TrainingAgent"`
- [ ] No syntax errors: `python -m py_compile training_agent/agent.py`
- [ ] Full package imports: `python -c "from training_agent import TrainingAgent; print('Import successful')"`

#### Manual Verification:
- [ ] Agent initializes with valid API key in `.env`
- [ ] Agent requests permissions correctly
- [ ] Agent takes initial screenshot and begins analysis

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation before proceeding to Phase 5.

---

## Phase 5: Integration Testing & Refinement

### Overview
Test the complete agent with a real training platform session and refine based on observations.

### Changes Required:

#### 1. Create Run Script with Better Logging
**File**: `run_agent.py`

```python
#!/usr/bin/env python3
"""
Run the Training Agent with enhanced logging.
"""

import sys
import logging
from datetime import datetime

# Set up detailed logging
log_filename = f"training_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_filename)
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info(f"Session log: {log_filename}")

    from training_agent import TrainingAgent

    agent = TrainingAgent()
    agent.run()

    logger.info(f"\nFull session log saved to: {log_filename}")

if __name__ == "__main__":
    main()
```

#### 2. Create .env file (user must fill in)
**File**: `.env`

```
# Get your API key from https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-your-key-here

# How long to run (in minutes)
RUN_DURATION_MINUTES=60

# Max retries for failed assessments
MAX_ASSESSMENT_RETRIES=3
```

### Success Criteria:

#### Automated Verification:
- [ ] Run script syntax valid: `python -m py_compile run_agent.py`
- [ ] All modules compile: `python -m py_compile training_agent/*.py`
- [ ] Package structure complete: `python -c "import training_agent; print(dir(training_agent))"`

#### Manual Verification:
- [ ] Agent successfully takes screenshot of training platform
- [ ] Agent navigates to a training module
- [ ] Agent watches a video (or waits appropriately)
- [ ] Agent attempts to answer assessment questions
- [ ] Agent records results correctly
- [ ] State persists between runs
- [ ] Confusion logging works when agent is confused

**Implementation Note**: This is the final phase. After automated verification passes, conduct a full manual test session with the training platform.

---

## Testing Strategy

### Unit Tests:
- Test state management (create, update, persist, load)
- Test configuration validation
- Test tool definitions structure

### Integration Tests:
- Test screenshot capture and resizing
- Test mouse click execution
- Test keyboard input

### Manual Testing Steps:
1. Start the training platform in a browser
2. Log in to the platform
3. Navigate to the training dashboard
4. Run `python run_agent.py`
5. Observe agent taking screenshots and making decisions
6. Verify agent finds and clicks on training modules
7. Verify agent handles video playback (waiting or skipping)
8. Verify agent answers assessment questions
9. Check `training_progress.json` for correct state
10. Check log files for any errors or confusion entries
11. Test Ctrl+C graceful shutdown
12. Restart agent and verify it resumes with saved state

## Performance Considerations

- Screenshot resizing ensures API size limits are met
- Old screenshots are truncated to manage context window
- State is saved after each significant action
- Extended thinking budget is limited to 2048 tokens

## Migration Notes

N/A - This is a new project with no existing data to migrate.

## References

- Reference implementation: `/Users/mkorovkin/Desktop/twitter-computer-use-agent/`
- Anthropic Computer Use API: https://docs.anthropic.com/en/docs/build-with-claude/computer-use
- Claude Sonnet model: `claude-sonnet-4-20250514`
