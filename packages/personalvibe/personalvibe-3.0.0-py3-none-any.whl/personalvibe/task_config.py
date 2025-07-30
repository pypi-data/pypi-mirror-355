# Copyright © 2025 by Nick Jenkins. All rights reserved
"""Task configuration loading and management."""

from __future__ import annotations

import logging
from typing import Dict

import yaml
from jinja2 import BaseLoader, Environment
from pydantic import BaseModel

from personalvibe import vibe_utils

log = logging.getLogger(__name__)


class TaskConfig(BaseModel):
    """Configuration for a specific task type."""

    task_name: str
    task_summary: str
    semver: str  # major, minor, or patch
    task_instructions: str


class TaskManager:
    """Manages loading and rendering of task configurations."""

    def __init__(self: TaskManager) -> None:
        self._task_cache: Dict[str, TaskConfig] = {}

    def load_task_config(self: TaskManager, task_name: str) -> TaskConfig:
        """Load task configuration from bundled data."""
        if task_name in self._task_cache:
            return self._task_cache[task_name]

        try:
            # Load from package data
            task_file = f"tasks/{task_name}.yaml"
            task_yaml = vibe_utils._load_template(task_file)

            # Parse YAML
            task_data = yaml.safe_load(task_yaml)

            # Create and cache config
            config = TaskConfig(**task_data)
            self._task_cache[task_name] = config

            log.info("Loaded task config: %s", task_name)
            return config

        except Exception as e:
            log.error("Failed to load task config '%s': %s", task_name, e)
            raise ValueError(f"Unknown task: {task_name}") from e

    def render_task_instructions(self: TaskManager, task_config: TaskConfig, context: dict) -> str:
        """Render task instructions with Jinja2 templating."""
        env = Environment(loader=BaseLoader())
        template = env.from_string(task_config.task_instructions)
        return template.render(**context)

    def get_semver_type(self: TaskManager, task_name: str) -> str:
        """Get the semver increment type for a task."""
        config = self.load_task_config(task_name)
        return config.semver


# Global instance
task_manager = TaskManager()
