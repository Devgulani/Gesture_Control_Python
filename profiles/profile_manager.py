"""User profile management for GestureOS.

Profiles store custom gesture mappings, sensitivity settings,
and AI/rule-based preferences independently from the core
controller architecture.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


PROFILES_DIR = Path(__file__).resolve().parent / "profiles"
DEFAULT_PROFILE_NAME = "default"


@dataclass
class Profile:
    """User profile storing preferences and gesture customisation."""

    profile_name: str = DEFAULT_PROFILE_NAME
    preferred_mode: str = "rule"

    sensitivity: Dict[str, float] = field(default_factory=lambda: {
        "cursor_smoothing": 0.45,
        "pinch_threshold": 0.055,
        "scroll_sensitivity": 1.0,
        "click_cooldown": 0.45,
    })

    ai_preferences: Dict[str, Any] = field(default_factory=lambda: {
        "confidence_threshold": 0.7,
        "hybrid_strategy": "rule_priority",
    })

    analytics_enabled: bool = False
    created_at: str = ""
    updated_at: str = ""


class ProfileManager:
    """Load, save, and switch user profiles."""

    def __init__(self, profiles_dir: Optional[Path] = None) -> None:
        """Initialise the manager with a profiles directory.

        Creates the directory and default profile if they do not exist.
        """
        self._profiles_dir = profiles_dir or PROFILES_DIR
        self._profiles_dir.mkdir(parents=True, exist_ok=True)
        self._active: Optional[Profile] = None
        self._ensure_default()
        logging.info("ProfileManager initialised (dir: %s)", self._profiles_dir)

    @property
    def active(self) -> Profile:
        """Return the currently loaded profile (loads default if needed)."""
        if self._active is None:
            self._active = self.load(DEFAULT_PROFILE_NAME)
        return self._active

    def _ensure_default(self) -> None:
        """Create a default profile file if none exists."""
        default_path = self._profiles_dir / f"{DEFAULT_PROFILE_NAME}.json"
        if not default_path.exists():
            self._write_profile(Profile(profile_name=DEFAULT_PROFILE_NAME))
            logging.info("Created default profile: %s", default_path)

    def load(self, name: str = DEFAULT_PROFILE_NAME) -> Profile:
        """Load a profile from disk.

        Args:
            name: Profile name (without .json extension).

        Returns:
            The deserialised Profile, or a default if loading fails.
        """
        path = self._profiles_dir / f"{name}.json"
        if not path.exists():
            logging.warning("Profile '%s' not found, using defaults", name)
            return Profile(profile_name=name)

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            profile = Profile(**data)
            self._active = profile
            logging.info("Loaded profile: %s", name)
            return profile
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            logging.error("Failed to load profile '%s': %s", name, exc)
            return Profile(profile_name=name)

    def save(self, profile: Optional[Profile] = None) -> None:
        """Save a profile to disk.

        Args:
            profile: The profile to save.  Defaults to the active profile.
        """
        target = profile or self._active
        if target is None:
            return
        self._write_profile(target)
        self._active = target
        logging.info("Saved profile: %s", target.profile_name)

    def _write_profile(self, profile: Profile) -> None:
        """Serialise and write a profile to its JSON file."""
        path = self._profiles_dir / f"{profile.profile_name}.json"
        data = asdict(profile)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
