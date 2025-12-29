"""State management for tracking training progress."""

import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Set, Optional, List
from dataclasses import dataclass, asdict, field
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
        elif module_name and not self.modules[module_id].module_name:
            self.modules[module_id].module_name = module_name
            self.save()
        return self.modules[module_id]

    def mark_video_watched(self, module_id: str):
        """Mark video as watched for a module."""
        module = self.get_or_create_module(module_id)
        module.video_watched = True
        self.save()
        logger.info(f"Video watched for module: {module_id}")

    def record_assessment_attempt(self, module_id: str, passed: bool,
                                   questions_total: int = 0, questions_correct: int = 0):
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

    def get_incomplete_modules(self) -> List[dict]:
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

    def get_failed_assessments(self) -> List[dict]:
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
        if total == 0:
            return "Training Progress Summary:\n  No modules tracked yet."

        videos_watched = sum(1 for m in self.modules.values() if m.video_watched)
        assessments_passed = sum(1 for m in self.modules.values() if m.assessment_passed)
        total_attempts = sum(m.assessment_attempts for m in self.modules.values())

        summary = (f"Training Progress Summary:\n"
                  f"  Modules tracked: {total}\n"
                  f"  Videos watched: {videos_watched}\n"
                  f"  Assessments passed: {assessments_passed}/{total}\n"
                  f"  Total assessment attempts: {total_attempts}\n"
                  f"  Session started: {self.session_start}")

        # Add details for each module
        if self.modules:
            summary += "\n\n  Module Details:"
            for module_id, progress in self.modules.items():
                status = "PASSED" if progress.assessment_passed else ("IN PROGRESS" if progress.video_watched else "NOT STARTED")
                summary += f"\n    - {progress.module_name}: {status}"
                if progress.assessment_attempts > 0:
                    summary += f" ({progress.questions_correct}/{progress.questions_answered} on attempt {progress.assessment_attempts})"

        return summary

    @staticmethod
    def hash_content(content: str) -> str:
        """Hash content for deduplication."""
        normalized = content.strip().lower()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]
