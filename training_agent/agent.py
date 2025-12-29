"""Core Training Agent with agentic loop."""

import time
import logging
from datetime import datetime, timedelta
from typing import Optional, List

import anthropic
import pyautogui

from .config import AgentConfig
from .state import TrainingState
from .tools import get_tools, BETA_FLAGS, DEFAULT_MODEL
from .computer import execute_computer_tool
from .permissions import check_permissions
from .screenshot import take_screenshot

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
        self.scroll_count = 0

        logger.info(f"Training Agent initialized. Will run until {self.end_time}")

    def _build_system_prompt(self) -> str:
        """Build the system prompt for Claude."""
        return f"""You are a computer use agent testing a workplace training platform. Your goal is to navigate through the platform as a real user would, completing training modules by watching videos and passing assessments.

## CLICK VERIFICATION - CRITICAL - YOU MUST DO THIS AFTER EVERY CLICK

After each click, the screenshot shows a RED CROSSHAIR MARKER labeled "CLICK: (x, y)" showing EXACTLY where your click landed.

**AFTER EVERY CLICK, YOU MUST:**
1. Look at the RED MARKER in the screenshot
2. Compare where the marker is vs where you INTENDED to click
3. If the marker missed the target element:
   - Calculate how far off you were (e.g., "marker is ~50 pixels to the left of the button")
   - Adjust your coordinates accordingly (e.g., "I need to add ~50 to my X coordinate")
   - IMMEDIATELY click again with the corrected coordinates
   - Repeat until the marker lands on the intended element

**EXAMPLE:**
- You try to click a "Play" button at (400, 300)
- Screenshot shows the RED MARKER landed on empty space to the LEFT of the button
- You reason: "The marker is about 30 pixels left of the Play button"
- You click again at (430, 300) to compensate
- Now the marker lands on the button - success!

**DO NOT** proceed to the next action until your click marker is visually ON the element you intended to click. Keep adjusting and re-clicking until you hit the target.

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

### Video and Audio Playback:
- **IMPORTANT**: Find and click ALL play buttons (triangle/arrow icons) on the page
- If you see a PAUSE button (two vertical bars), the media is already playing - DO NOT click it, let it play
- Wait for ALL media to finish playing before proceeding
- Look for progress bars - wait until they reach 100% or the end
- If multiple videos/audio clips exist, play them one at a time and wait for each to complete
- Take screenshots periodically to check if media is still playing or has finished
- Call `mark_video_watched` once ALL media on the page is complete

### "Complete the steps to continue" Button:
- If you see a button that says "Complete the steps to continue", this means there are REQUIRED steps you must finish
- DO NOT try to click this button - it won't work until you complete the required steps
- Look for incomplete steps on the page (unchecked items, unplayed videos, unanswered questions)
- Complete ALL required steps first, then the button will change to allow progression

### "Next" Button Navigation:
- ONLY click the "Next" button when it is HIGHLIGHTED/ENABLED (usually a solid color, not grayed out)
- If the "Next" button is grayed out or disabled, you have NOT completed all required steps
- Look for what's missing: unplayed videos, unanswered questions, unchecked checkboxes
- Complete the missing steps, then try "Next" again

### Assessment Answering:
- READ each question carefully before answering
- For multiple choice: analyze all options and select the most accurate answer based on the video content and your reasoning
- For free text: provide thoughtful, complete answers that address the question
- For drag-and-drop: match items logically based on the training content
- Look for "Submit", "Next Question", or "Finish" buttons
- After submitting, check for results - look for scores, pass/fail indicators
- Call `record_assessment_result` after seeing the final results

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
                # Take screenshot after click
                screenshot_b64 = take_screenshot()
                return f"Clicked cached location '{action_name}' at ({x}, {y}). Screenshot taken."
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

        # Take initial screenshot
        logger.info("Taking initial screenshot...")
        initial_screenshot = take_screenshot()
        if not initial_screenshot:
            logger.error("Failed to take initial screenshot!")
            return messages

        from .screenshot import get_screen_size
        w, h = get_screen_size()
        logger.info(f"Screen size: {w}x{h}")

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

        # Initial message with the screenshot we already took
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": "Here is the current state of the training platform. Please analyze it and begin navigating through the training."},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": initial_screenshot
                    }
                }
            ]
        })

        while iteration < max_iterations and datetime.now() < self.end_time:
            iteration += 1
            remaining = (self.end_time - datetime.now()).total_seconds() / 60

            logger.info(f"=== Iteration {iteration} | {remaining:.1f} min remaining | "
                       f"Modules: {len(self.state.modules)} | Scrolls: {self.scroll_count} ===")

            try:
                # Build API parameters
                # Get tools with current screenshot dimensions (updated after each screenshot)
                tools = get_tools()

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
                            scroll_counter = {'count': self.scroll_count}
                            result = execute_computer_tool(
                                block.input,
                                scroll_counter,
                                self.actions_cache
                            )
                            self.scroll_count = scroll_counter['count']
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
                    logger.info("No tool calls - Claude has finished or is waiting")
                    # Check if we should continue or if Claude thinks it's done
                    if response.stop_reason == "end_turn":
                        # Claude finished its response, let's prompt it to continue
                        messages.append({
                            "role": "user",
                            "content": "Please continue with the training. Take a screenshot to see the current state and proceed with the next task."
                        })
                    continue

                # Add tool results to messages
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # Truncate old images to manage context
                messages = self._truncate_old_images(messages, keep_recent=3)

            except anthropic.APIError as e:
                logger.error(f"API error: {e}")
                # Add error context for Claude
                messages.append({
                    "role": "user",
                    "content": f"API error occurred: {str(e)}. Please take a screenshot and try again."
                })
            except Exception as e:
                logger.error(f"Error in agent loop: {e}")
                import traceback
                logger.error(traceback.format_exc())
                messages.append({
                    "role": "user",
                    "content": f"Error occurred: {str(e)}. Please take a screenshot and try a different approach."
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
            logger.info(f"Partial progress: {len(self.state.modules)} modules tracked")
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

        # Clear click marker
        from .screenshot import clear_last_click, SCREENSHOT_PATH
        clear_last_click()

        # Delete temp screenshot file
        import os
        if os.path.exists(SCREENSHOT_PATH):
            os.remove(SCREENSHOT_PATH)
            logger.info(f"Deleted {SCREENSHOT_PATH}")

        # Save confusion log if any
        if self.confusion_log:
            import json
            with open('confusion_log.json', 'w') as f:
                json.dump(self.confusion_log, f, indent=2)
            logger.info(f"Saved {len(self.confusion_log)} confusion entries to confusion_log.json")

        logger.info("Agent shut down successfully")
