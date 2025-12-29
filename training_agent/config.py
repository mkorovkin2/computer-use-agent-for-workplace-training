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
            raise ValueError("Invalid ANTHROPIC_API_KEY format - should start with 'sk-ant-'")

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
            # Parse output for resolution
            output = result.stdout
            for line in output.split('\n'):
                if 'Resolution' in line:
                    # Try to extract resolution like "2560 x 1440"
                    parts = line.split(':')
                    if len(parts) > 1:
                        res_str = parts[1].strip()
                        # Handle formats like "2560 x 1440" or "2560x1440"
                        if ' x ' in res_str:
                            dims = res_str.split(' x ')
                        elif 'x' in res_str:
                            dims = res_str.split('x')
                        else:
                            continue
                        try:
                            width = int(dims[0].strip().split()[0])
                            height = int(dims[1].strip().split()[0])
                            self.screen_width = width
                            self.screen_height = height
                            logger.info(f"Detected screen size: {width}x{height}")
                            return
                        except (ValueError, IndexError):
                            continue
        except Exception as e:
            logger.debug(f"Screen detection failed, using defaults: {e}")
