# Workplace Training Platform Test Agent

A computer use agent that autonomously tests workplace training platforms by navigating through modules, watching videos, and completing assessments.

**Platform: macOS only** (uses `screencapture` and macOS-specific permissions)

## How It Works

This agent uses Anthropic's Claude with Computer Use capabilities to:

1. **Take screenshots** of your screen and analyze them with Claude's vision
2. **Control mouse/keyboard** via PyAutoGUI to click, type, scroll, and drag
3. **Navigate autonomously** through training content like a real user would
4. **Answer assessments** using Claude's reasoning to determine correct answers
5. **Track progress** in a persistent JSON file to resume between sessions
6. **Log confusion points** when the UI is unclear (useful for UX testing)

The agent handles Retina display scaling automatically - coordinates from the resized screenshot are scaled back to actual screen coordinates.

## Requirements

- macOS (tested on macOS 14+)
- Python 3.9+
- Anthropic API key
- Screen Recording permission for Terminal/Python
- Accessibility permission for Terminal/Python

## Setup

```bash
# Run the setup script
./setup.sh

# Add your API key
nano .env
# Set: ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Usage

1. Open your training platform in a browser and log in
2. Navigate to the main training dashboard
3. Run the agent:

```bash
./run.sh
```

The agent will:
- Take a screenshot to see the current state
- Find and start training modules
- Watch videos (waiting for completion)
- Answer assessment questions using reasoning
- Track which modules are completed
- Retry failed assessments

Press `Ctrl+C` to stop gracefully.

## Configuration

Edit `.env` to configure:

```
ANTHROPIC_API_KEY=sk-ant-...  # Required
RUN_DURATION_MINUTES=60       # How long to run (default: 60)
MAX_ASSESSMENT_RETRIES=3      # Retries per failed assessment
```

## Output Files

- `training_progress.json` - Tracks completed modules and assessment results
- `confusion_log.json` - Logs when the agent got confused (UX issues)
- `training_session_*.log` - Detailed session logs
- `agent.log` - General agent logs

## macOS Permissions

The agent needs these permissions (System Settings > Privacy & Security):

1. **Screen Recording** - Enable for Terminal (or your terminal app)
2. **Accessibility** - Enable for Terminal and Python

After enabling, restart your terminal.

## Architecture

```
training_agent/
├── agent.py       # Main agentic loop - Claude analyzes & decides
├── computer.py    # Mouse/keyboard execution with coordinate scaling
├── screenshot.py  # Screenshot capture, resize, and scale tracking
├── state.py       # Progress persistence (modules, assessments)
├── tools.py       # Anthropic API tool definitions
├── config.py      # Configuration from environment
└── permissions.py # macOS permission checks
```

## How Coordinate Scaling Works

1. Screenshot captured at full Retina resolution (e.g., 3024x1964)
2. Resized to fit API limits (~1330x864)
3. Claude sees resized image and returns coordinates in that space
4. Coordinates scaled back to screen space before clicking

This ensures clicks land exactly where Claude intended.
