#!/usr/bin/env -S uv run -s
# this_file: src/vexylicon/utils/theme_loader.py
# ruff: noqa
"""Theme loading and validation utilities.

This module handles loading theme definitions from JSON files
and provides validation to ensure themes are properly structured.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal
from dataclasses import dataclass


@dataclass
class GradientStop:
    """Represents a color stop in a gradient."""

    offset: float
    color: str
    opacity: float

    def __post_init__(self) -> None:  # noqa: D401 – simple validation method
        if not 0 <= self.offset <= 1:
            raise ValueError(
                "Gradient stop 'offset' must be within 0–1 range.",
            )
        if not 0 <= self.opacity <= 1:
            raise ValueError(
                "Gradient stop 'opacity' must be within 0–1 range.",
            )


@dataclass
class LinearGradient:
    """Linear gradient definition."""

    type: Literal["linear"]
    x1: float
    y1: float
    x2: float
    y2: float
    stops: list[GradientStop]

    def __post_init__(self) -> None:  # noqa: D401
        if self.type != "linear":
            raise ValueError(
                "LinearGradient type must be 'linear'.",
            )


@dataclass
class RadialGradient:
    """Radial gradient definition."""

    type: Literal["radial"]
    cx: float
    cy: float
    r: float
    stops: list[GradientStop]

    def __post_init__(self) -> None:  # noqa: D401
        if self.type != "radial":
            raise ValueError(
                "RadialGradient type must be 'radial'.",
            )


@dataclass
class ThemeColors:
    """Theme color definitions."""

    canvas: str
    border: str


@dataclass
class ThemeEffects:
    """Theme effect settings."""

    blendMode: str = "screen"
    strokeOpacity: float = 0.5
    strokeWidth: float = 0.25

    def __post_init__(self) -> None:  # noqa: D401
        if not 0 <= self.strokeOpacity <= 1:
            raise ValueError(
                "ThemeEffects strokeOpacity must be within 0–1.",
            )
        if self.strokeWidth <= 0:
            raise ValueError("ThemeEffects strokeWidth must be > 0.")


@dataclass
class Theme:
    """Complete theme definition."""

    name: str
    version: str
    gradients: dict[str, dict[str, Any]]
    colors: ThemeColors
    effects: ThemeEffects

    # ---------------------------------------------------------------------
    # Construction helpers
    # ---------------------------------------------------------------------
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Theme:  # noqa: D401 – factory method
        """Create a :class:`Theme` from a raw ``dict`` (e.g. loaded from JSON)."""
        colors = data.get("colors", {})
        effects = data.get("effects", {})

        # Convert nested structures to dataclasses if necessary
        if not isinstance(colors, ThemeColors):
            colors = ThemeColors(**colors)
        if not isinstance(effects, ThemeEffects):
            effects = ThemeEffects(**effects)

        gradients: dict[str, dict[str, Any]] = data.get("gradients", {})
        name = data.get("name", "unnamed")
        version = data.get("version", "0.0.0")
        theme = cls(
            name=name,
            version=version,
            gradients=gradients,
            colors=colors,
            effects=effects,
        )
        # Validate after creation
        theme._validate_gradients()
        return theme

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:  # noqa: D401
        """Post-initialisation validation and coercion."""
        # Ensure nested dictionaries become dataclass instances when Theme is
        # constructed directly via ``Theme(**kwargs)``.
        if isinstance(self.colors, dict):
            self.colors = ThemeColors(**self.colors)  # type: ignore[assignment]
        if isinstance(self.effects, dict):
            self.effects = ThemeEffects(**self.effects)  # type: ignore[assignment]
        self._validate_gradients()

    # private ----------------------------------------------------------------
    def _validate_gradients(self) -> None:
        """Validate gradient structures ensuring supported types and ranges."""
        for name, grad in self.gradients.items():
            grad_type = grad.get("type")
            if grad_type == "linear":
                required_keys = {"x1", "y1", "x2", "y2", "stops"}
            elif grad_type == "radial":
                required_keys = {"cx", "cy", "r", "stops"}
            else:
                raise ValueError(
                    (f"Unknown gradient type '{grad_type}' in gradient '{name}'."),
                )

            missing = required_keys - set(grad.keys())
            if missing:
                missing_keys = ", ".join(sorted(missing))
                raise ValueError(
                    (f"Gradient '{name}' missing keys: {missing_keys}"),
                )

            # Validate stops
            for stop in grad.get("stops", []):
                try:
                    GradientStop(**stop)  # type: ignore[arg-type]
                except TypeError as exc:
                    raise ValueError(
                        (f"Invalid gradient stop in '{name}': {exc}"),
                    ) from exc


class ThemeLoader:
    """Handles loading and management of theme definitions."""

    def __init__(self, theme_dir: Path | None = None):
        """Initialize theme loader.

        Args:
            theme_dir: Directory containing theme JSON files.
                      If None, uses package assets directory.
        """
        if theme_dir is None:
            # Use package assets
            import importlib.resources

            self.theme_dir = importlib.resources.files("vexylicon.assets.themes")
        else:
            self.theme_dir = Path(theme_dir)

    def load_theme(self, theme_name: str) -> Theme:
        """Load and validate a theme by name.

        Args:
            theme_name: Name of the theme (without .json extension)

        Returns:
            Validated Theme object

        Raises:
            FileNotFoundError: If theme file doesn't exist
            ValidationError: If theme JSON is invalid
        """
        theme_path = self.theme_dir / f"{theme_name}.json"

        if hasattr(self.theme_dir, "joinpath"):
            # Handle importlib.resources path
            theme_content = (self.theme_dir / f"{theme_name}.json").read_text()
            theme_data = json.loads(theme_content)
        else:
            # Handle regular Path
            if not theme_path.exists():
                msg = f"Theme not found: {theme_name}"
                raise FileNotFoundError(msg)

            with open(theme_path) as f:
                theme_data = json.load(f)

        return Theme.from_dict(theme_data)

    def list_themes(self) -> list[str]:
        """List available theme names.

        Returns:
            List of theme names (without .json extension)
        """
        if hasattr(self.theme_dir, "iterdir"):
            # Handle importlib.resources path
            return [f.name[:-5] for f in self.theme_dir.iterdir() if f.name.endswith(".json")]
        # Handle regular Path
        return [f.stem for f in self.theme_dir.glob("*.json")]

    def create_dark_variant(self, theme: Theme) -> Theme:
        """Create a dark variant of a theme.

        This creates a modified version of the theme suitable for
        dark backgrounds by adjusting opacity values.

        Args:
            theme: Base theme to modify

        Returns:
            Dark variant of the theme
        """
        import copy

        dark_theme = copy.deepcopy(theme)
        dark_theme.name = f"{theme.name}-dark"

        # Increase opacity slightly for dark backgrounds
        for gradient in dark_theme.gradients.values():
            for stop in gradient.get("stops", []):
                if "opacity" in stop:
                    # Increase opacity by 20% for dark mode
                    stop["opacity"] = min(1.0, stop["opacity"] * 1.2)

        return dark_theme
