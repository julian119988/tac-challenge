"""State management for ADW workflows."""

import json
import os
import sys
from typing import Optional, Any, Dict
from datetime import datetime
from pathlib import Path
import logging

from .data_types import ADWStateData, ModelSet, IssueClassSlashCommand


class ADWState:
    """Persistent state container for ADW workflows.

    State is stored in agents/{adw_id}/adw_state.json and can be loaded/saved
    across different workflow phases.
    """

    def __init__(self, adw_id: str, **kwargs):
        """Initialize ADW state.

        Args:
            adw_id: Unique ADW identifier
            **kwargs: Additional state fields matching ADWStateData
        """
        self.adw_id = adw_id
        self.issue_number: Optional[int] = kwargs.get("issue_number")
        self.branch_name: Optional[str] = kwargs.get("branch_name")
        self.plan_file: Optional[str] = kwargs.get("plan_file")
        self.issue_class: Optional[IssueClassSlashCommand] = kwargs.get("issue_class")
        self.worktree_path: Optional[str] = kwargs.get("worktree_path")
        self.backend_port: Optional[int] = kwargs.get("backend_port")
        self.frontend_port: Optional[int] = kwargs.get("frontend_port")
        self.model_set: ModelSet = kwargs.get("model_set", "base")
        self.all_adws: list = kwargs.get("all_adws", [])
        self.created_at: Optional[str] = kwargs.get("created_at")
        self.updated_at: Optional[str] = kwargs.get("updated_at")

        # Set created_at if not provided
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    @classmethod
    def load(cls, adw_id: str, logger: Optional[logging.Logger] = None) -> "ADWState":
        """Load state from file or create new if doesn't exist.

        Args:
            adw_id: ADW identifier
            logger: Optional logger for messages

        Returns:
            ADWState instance
        """
        state_file = cls._get_state_file_path(adw_id)

        if os.path.exists(state_file):
            try:
                with open(state_file, "r") as f:
                    data = json.load(f)

                if logger:
                    logger.info(f"Loaded state from {state_file}")

                return cls.from_dict(data)
            except Exception as e:
                if logger:
                    logger.warning(f"Failed to load state from {state_file}: {e}")
                if logger:
                    logger.info("Creating new state")

        # Create new state
        if logger:
            logger.info(f"Creating new state for ADW ID: {adw_id}")

        return cls(adw_id=adw_id)

    @classmethod
    def load_from_stdin(cls) -> Optional["ADWState"]:
        """Load state from stdin for piping between scripts.

        Returns:
            ADWState instance or None if stdin is empty
        """
        if not sys.stdin.isatty():
            try:
                data = json.load(sys.stdin)
                return cls.from_dict(data)
            except:
                pass
        return None

    def save(self, workflow_name: str) -> str:
        """Persist state to file.

        Args:
            workflow_name: Name of workflow saving the state

        Returns:
            Path to saved state file
        """
        self.updated_at = datetime.now().isoformat()

        # Add workflow to all_adws if not present
        if workflow_name and workflow_name not in self.all_adws:
            self.all_adws.append(workflow_name)

        state_file = self._get_state_file_path(self.adw_id)

        # Ensure directory exists
        os.makedirs(os.path.dirname(state_file), exist_ok=True)

        # Write state
        with open(state_file, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

        return state_file

    def save_to_stdout(self):
        """Output state to stdout for piping to next script."""
        print(json.dumps(self.to_dict(), indent=2))

    def update(self, **kwargs) -> "ADWState":
        """Update state fields.

        Args:
            **kwargs: Fields to update

        Returns:
            Self for chaining
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        return self

    def validate(self) -> tuple[bool, str]:
        """Validate core fields.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.adw_id:
            return False, "adw_id is required"

        # Validate using Pydantic model
        try:
            ADWStateData(**self.to_dict())
            return True, ""
        except Exception as e:
            return False, str(e)

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "adw_id": self.adw_id,
            "issue_number": self.issue_number,
            "branch_name": self.branch_name,
            "plan_file": self.plan_file,
            "issue_class": self.issue_class,
            "worktree_path": self.worktree_path,
            "backend_port": self.backend_port,
            "frontend_port": self.frontend_port,
            "model_set": self.model_set,
            "all_adws": self.all_adws,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ADWState":
        """Create state from dictionary.

        Args:
            data: Dictionary with state fields

        Returns:
            ADWState instance
        """
        adw_id = data.pop("adw_id")
        return cls(adw_id=adw_id, **data)

    @staticmethod
    def _get_state_file_path(adw_id: str) -> str:
        """Get path to state file.

        Args:
            adw_id: ADW identifier

        Returns:
            Path to adw_state.json
        """
        # Get project root (3 levels up from this file)
        project_root = Path(__file__).parent.parent.parent
        return str(project_root / "agents" / adw_id / "adw_state.json")
