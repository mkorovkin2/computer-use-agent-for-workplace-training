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
