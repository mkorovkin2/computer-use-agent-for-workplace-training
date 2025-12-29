#!/usr/bin/env python3
"""
Run the Training Agent with enhanced logging.

Usage:
    python run_agent.py

Make sure to:
1. Copy .env.example to .env and add your ANTHROPIC_API_KEY
2. Have your training platform open in a browser
3. Be logged in and on the main training page
"""

import sys
import logging
from datetime import datetime

# Set up detailed logging with timestamped file
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
    logger.info(f"Session log will be saved to: {log_filename}")
    logger.info("-" * 60)

    try:
        from training_agent import TrainingAgent

        agent = TrainingAgent()
        agent.run()

    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure you have installed dependencies: pip install -r requirements.txt")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Make sure you have set up your .env file with ANTHROPIC_API_KEY")
        sys.exit(1)

    logger.info("-" * 60)
    logger.info(f"Full session log saved to: {log_filename}")


if __name__ == "__main__":
    main()
