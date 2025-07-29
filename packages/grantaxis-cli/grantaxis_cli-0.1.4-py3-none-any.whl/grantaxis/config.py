from __future__ import annotations
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Pattern, Sequence, Tuple, Union

import yaml

"""
GrantAxis – config.py
====================
Load **grantaxis.yml** once with support for presets and compile all regex filters.
Expose helper functions to trim the `added`/`removed`/`changed` collections 
produced by `diff.py`.

Supported configuration structure:
```yaml
# Built-in presets (can be overridden)
preset: "production"  # or "development", "security-audit", or custom preset name

# Custom presets
presets:
  my-custom:
    ignore_objects:
      - "^RAW\\.EVENT_.*$"
    ignore_grantees:
      - "^ROLE_ETL_TMP_.*$"
    # ... other filters

# Direct filters (legacy support, merged with preset)
ignore_objects:
  - "^TEMP\\..*$"
ignore_grantees:
  - "^USER_TEMP_.*$"
ignore_privileges:
  - "^USAGE$"
critical_privileges:
  - "OWNERSHIP"

# Noise reduction settings
noise_reduction:
  group_similar: true
  max_similar_items: 5
  ignore_grant_option_for: ["USAGE", "MONITOR"]
```

If **grantaxis.yml** is missing, defaults to "allow all" (no filters).
"""

# Configure module logger
logger = logging.getLogger(__name__)

# Type aliases for better readability
DriftRecord = Dict[str, str]
ChangedRecord = Tuple[DriftRecord, DriftRecord]
TransferRecord = Tuple[DriftRecord, DriftRecord]
FilterResult = Tuple[
    List[DriftRecord], List[DriftRecord], List[ChangedRecord], List[TransferRecord]
]


class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""

    pass


class ValidationError(ConfigError):
    """Raised when configuration validation fails."""

    pass


@dataclass(slots=True, frozen=True)
class NoiseReductionSettings:
    """Settings for reducing noise in drift reports."""

    group_similar: bool = False
    max_similar_items: int = 10
    ignore_grant_option_for: List[str] = None

    def __post_init__(self):
        if self.ignore_grant_option_for is None:
            object.__setattr__(self, "ignore_grant_option_for", [])


@dataclass(slots=True, frozen=True)
class Config:
    """Configuration holder with compiled regex patterns for filtering grant drift."""

    ignore_objects: List[Pattern[str]]
    ignore_grantees: List[Pattern[str]]
    ignore_privileges: List[Pattern[str]]
    critical_privileges: List[Pattern[str]]
    noise_reduction: NoiseReductionSettings
    active_preset: Optional[str] = None

    # Built-in presets
    BUILTIN_PRESETS = {
        "production": {
            "ignore_objects": [
                r".*_TMP$",
                r".*_TEMP$",
                r".*_BACKUP$",
                r".*_ARCHIVE$",
                r"^TEMP\..*",
                r".*\..*_PERSONAL\..*",
                r".*\..*_SANDBOX\..*",
            ],
            "ignore_grantees": [
                r"^ROLE_.*_TMP$",
                r"^ROLE_.*_TEMP$",
                r"^USER_.*_TEMP$",
                r"^.*_SERVICE_ACCOUNT$",
                r"^DBT_.*",
                r"^FIVETRAN_.*",
            ],
            "ignore_privileges": [r"^MONITOR$"],
            "critical_privileges": [
                r"^OWNERSHIP$",
                r"^ACCOUNTADMIN$",
                r"^SECURITYADMIN$",
                r"^CREATE USER$",
                r"^CREATE ROLE$",
            ],
        },
        "development": {
            "ignore_objects": [
                r".*_PERSONAL\..*",
                r".*_TEMP$",
                r".*_TMP$",
                r"^SCRATCH\..*",
            ],
            "ignore_grantees": [r"^ROLE_DEV_.*_TMP$", r"^USER_.*_TEMP$"],
            "ignore_privileges": [r"^MONITOR$", r"^USAGE$"],
            "critical_privileges": [r"^SELECT$", r"^INSERT$", r"^UPDATE$", r"^DELETE$"],
        },
        "security-audit": {
            "ignore_objects": [],
            "ignore_grantees": [],
            "ignore_privileges": [],
            "critical_privileges": [
                r"^OWNERSHIP$",
                r"^ACCOUNTADMIN$",
                r"^SECURITYADMIN$",
                r"^USERADMIN$",
                r"^CREATE USER$",
                r"^CREATE ROLE$",
                r"^MANAGE GRANTS$",
            ],
        },
    }

    @classmethod
    def load(
        cls,
        path: Union[str, Path, None] = "grantaxis.yml",
        preset_override: Optional[str] = None,
    ) -> Config:
        """
        Load configuration from YAML file with preset support.

        Args:
            path: Path to configuration file. Defaults to 'grantaxis.yml'
            preset_override: Override preset from command line

        Returns:
            Config instance with compiled patterns

        Raises:
            ConfigError: If file cannot be read or parsed
            ValidationError: If configuration structure is invalid
        """
        config_path = Path(path) if path else Path("grantaxis.yml")

        try:
            if config_path.exists():
                logger.info(f"Loading configuration from {config_path}")
                with config_path.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
            else:
                logger.info(
                    f"Configuration file {config_path} not found, using defaults"
                )
                data = {}

        except yaml.YAMLError as exc:
            raise ConfigError(f"Failed to parse YAML in {config_path}: {exc}") from exc
        except (OSError, IOError) as exc:
            raise ConfigError(
                f"Failed to read config file {config_path}: {exc}"
            ) from exc

        # Validate configuration structure
        cls._validate_config(data, config_path)

        # Determine active preset
        active_preset = preset_override or data.get("preset")

        # Merge preset with direct configuration
        merged_config = cls._merge_preset_config(data, active_preset)

        # Extract noise reduction settings
        noise_settings = cls._load_noise_reduction(merged_config)

        return cls(
            ignore_objects=cls._compile_patterns("ignore_objects", merged_config),
            ignore_grantees=cls._compile_patterns("ignore_grantees", merged_config),
            ignore_privileges=cls._compile_patterns("ignore_privileges", merged_config),
            critical_privileges=cls._compile_patterns(
                "critical_privileges", merged_config
            ),
            noise_reduction=noise_settings,
            active_preset=active_preset,
        )

    @classmethod
    def _merge_preset_config(cls, data: Dict, preset_name: Optional[str]) -> Dict:
        """Merge preset configuration with direct configuration."""
        merged = {}

        # Start with preset if specified
        if preset_name:
            if preset_name in cls.BUILTIN_PRESETS:
                logger.info(f"Using built-in preset: {preset_name}")
                merged.update(cls.BUILTIN_PRESETS[preset_name])
            elif "presets" in data and preset_name in data["presets"]:
                logger.info(f"Using custom preset: {preset_name}")
                merged.update(data["presets"][preset_name])
            else:
                raise ValidationError(f"Unknown preset: {preset_name}")

        # Merge with direct configuration (direct config takes precedence)
        filter_keys = [
            "ignore_objects",
            "ignore_grantees",
            "ignore_privileges",
            "critical_privileges",
        ]
        for key in filter_keys:
            if key in data:
                # Merge lists from preset and direct config
                preset_values = merged.get(key, [])
                direct_values = data[key] or []
                merged[key] = preset_values + direct_values

        # Include non-filter keys
        for key, value in data.items():
            if key not in filter_keys and key not in ["preset", "presets"]:
                merged[key] = value

        return merged

    @classmethod
    def _load_noise_reduction(cls, data: Dict) -> NoiseReductionSettings:
        """Load noise reduction settings from configuration."""
        noise_config = data.get("noise_reduction", {})

        return NoiseReductionSettings(
            group_similar=noise_config.get("group_similar", False),
            max_similar_items=noise_config.get("max_similar_items", 10),
            ignore_grant_option_for=noise_config.get("ignore_grant_option_for", []),
        )

    @staticmethod
    def _validate_config(data: Dict, config_path: Path) -> None:
        """Validate configuration structure and types."""
        if not isinstance(data, dict):
            raise ValidationError(
                f"Configuration root must be a dictionary in {config_path}"
            )

        valid_keys = {
            "preset",
            "presets",
            "noise_reduction",
            "ignore_objects",
            "ignore_grantees",
            "ignore_privileges",
            "critical_privileges",
        }
        invalid_keys = set(data.keys()) - valid_keys

        if invalid_keys:
            logger.warning(
                f"Unknown configuration keys in {config_path}: {invalid_keys}"
            )

        # Validate preset
        if "preset" in data and not isinstance(data["preset"], str):
            raise ValidationError(f"'preset' must be a string in {config_path}")

        # Validate custom presets
        if "presets" in data:
            if not isinstance(data["presets"], dict):
                raise ValidationError(
                    f"'presets' must be a dictionary in {config_path}"
                )

            for preset_name, preset_config in data["presets"].items():
                if not isinstance(preset_config, dict):
                    raise ValidationError(
                        f"Preset '{preset_name}' must be a dictionary in {config_path}"
                    )

        # Validate filter lists
        filter_keys = [
            "ignore_objects",
            "ignore_grantees",
            "ignore_privileges",
            "critical_privileges",
        ]
        for key in filter_keys:
            if key in data and data[key] is not None:
                if not isinstance(data[key], list):
                    raise ValidationError(
                        f"Configuration key '{key}' must be a list in {config_path}"
                    )
                if not all(isinstance(item, str) for item in data[key]):
                    raise ValidationError(
                        f"All items in '{key}' must be strings in {config_path}"
                    )

    @staticmethod
    def _compile_patterns(key: str, data: Dict) -> List[Pattern[str]]:
        """Compile regex patterns from configuration."""
        patterns: Sequence[str] = data.get(key, []) or []
        compiled_patterns = []

        for pattern in patterns:
            try:
                compiled_patterns.append(re.compile(pattern))
                logger.debug(f"Compiled pattern for {key}: {pattern}")
            except re.error as exc:
                raise ValidationError(
                    f"Invalid regex pattern '{pattern}' in {key}: {exc}"
                ) from exc

        return compiled_patterns

    def is_ignored(self, record: DriftRecord) -> bool:
        """Check if a drift record matches any ignore rule."""
        if not isinstance(record, dict):
            logger.warning(f"Expected dictionary record, got {type(record)}")
            return False

        object_fqn = self._build_object_fqn(record)
        grantee = record.get("grantee_name", "")
        privilege = record.get("privilege", "")

        # Check each filter type
        if self._matches_patterns(object_fqn, self.ignore_objects):
            logger.debug(f"Ignoring object: {object_fqn}")
            return True

        if self._matches_patterns(grantee, self.ignore_grantees):
            logger.debug(f"Ignoring grantee: {grantee}")
            return True

        if self._matches_patterns(privilege, self.ignore_privileges):
            logger.debug(f"Ignoring privilege: {privilege}")
            return True

        return False

    def is_critical(self, record: DriftRecord) -> bool:
        """Check if a drift record contains a critical privilege."""
        if not self.critical_privileges:
            return True  # All privileges are critical if none specified

        privilege = record.get("privilege", "")
        return self._matches_patterns(privilege, self.critical_privileges)

    def should_ignore_grant_option_change(self, privilege: str) -> bool:
        """Check if grant option changes should be ignored for this privilege."""
        return privilege in self.noise_reduction.ignore_grant_option_for

    @staticmethod
    def _build_object_fqn(record: DriftRecord) -> str:
        """Build fully qualified name from record components."""
        components = [
            record.get("database_name", ""),
            record.get("schema_name", ""),
            record.get("object_name", ""),
        ]
        return ".".join(component for component in components if component)

    @staticmethod
    def _matches_patterns(text: str, patterns: List[Pattern[str]]) -> bool:
        """Check if text matches any of the provided patterns."""
        return any(pattern.search(text) for pattern in patterns)

    def filter_drift(
        self,
        added: List[DriftRecord],
        removed: List[DriftRecord],
        changed: List[ChangedRecord],
        transfers: Optional[List[TransferRecord]] = None,
    ) -> FilterResult:
        """Filter drift lists by removing ignored items."""
        if transfers is None:
            transfers = []

        logger.info(
            f"Filtering drift: {len(added)} added, {len(removed)} removed, "
            f"{len(changed)} changed, {len(transfers)} transfers"
        )

        filtered_added = [r for r in added if not self.is_ignored(r)]
        filtered_removed = [r for r in removed if not self.is_ignored(r)]

        # Filter changed records, optionally ignoring grant option changes
        filtered_changed = []
        for old_rec, new_rec in changed:
            if self.is_ignored(old_rec):
                continue

            # Check if this is just a grant option change we should ignore
            privilege = old_rec.get("privilege", "")
            if self.should_ignore_grant_option_change(privilege):
                # Check if the only difference is grant option
                old_grant_opt = old_rec.get("with_grant_option", False)
                new_grant_opt = new_rec.get("with_grant_option", False)
                if old_grant_opt != new_grant_opt:
                    # This is only a grant option change for an ignored privilege
                    continue

            filtered_changed.append((old_rec, new_rec))

        filtered_transfers = [
            (from_rec, to_rec)
            for from_rec, to_rec in transfers
            if not self.is_ignored(from_rec) and not self.is_ignored(to_rec)
        ]

        logger.info(
            f"After filtering: {len(filtered_added)} added, {len(filtered_removed)} removed, "
            f"{len(filtered_changed)} changed, {len(filtered_transfers)} transfers"
        )

        return filtered_added, filtered_removed, filtered_changed, filtered_transfers

    def get_stats(self) -> Dict[str, Union[int, str, None]]:
        """Get statistics about configured patterns."""
        return {
            "active_preset": self.active_preset,
            "ignore_objects": len(self.ignore_objects),
            "ignore_grantees": len(self.ignore_grantees),
            "ignore_privileges": len(self.ignore_privileges),
            "critical_privileges": len(self.critical_privileges),
            "noise_reduction_enabled": self.noise_reduction.group_similar,
        }

    @classmethod
    def list_presets(cls) -> Dict[str, str]:
        """List available built-in presets with descriptions."""
        return {
            "production": "Focus on production changes, ignore temp/personal objects",
            "development": "Development-focused filtering with common dev patterns",
            "security-audit": "Security-focused view of sensitive privileges only",
        }


def load_config(
    path: Optional[Union[str, Path]] = None, preset: Optional[str] = None
) -> Config:
    """
    Convenience function to load configuration.

    Args:
        path: Optional path to configuration file
        preset: Optional preset name to use

    Returns:
        Loaded Config instance
    """
    return Config.load(path, preset)


# ---------------------------------------------------------------------------
# Manual test and example usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        print("Available presets:")
        for name, description in Config.list_presets().items():
            print(f"  {name}: {description}")
        print()

        # Test loading different presets
        for preset_name in ["production", "development", "security-audit"]:
            print(f"Testing preset: {preset_name}")
            cfg = load_config(preset=preset_name)
            print(f"  Stats: {cfg.get_stats()}")
            print()

        # Test with custom config file if it exists
        example_path = Path("examples/grantaxis.yml")
        if example_path.exists():
            cfg = load_config(example_path)
            print(f"Loaded from {example_path}")
            print(f"Stats: {cfg.get_stats()}")

        # Test data
        dummy_added = [
            {
                "database_name": "RAW",
                "schema_name": "PUBLIC",
                "object_name": "EVENT_TMP",
                "privilege": "SELECT",
                "grantee_name": "ROLE_RAW_INGEST",
            },
            {
                "database_name": "PROD",
                "schema_name": "SALES",
                "object_name": "ORDERS",
                "privilege": "OWNERSHIP",
                "grantee_name": "ROLE_SYSADMIN",
            },
        ]

        cfg = load_config(preset="production")
        filtered_added, filtered_removed, filtered_changed, filtered_transfers = (
            cfg.filter_drift(dummy_added, [], [], [])
        )

        print("\nTest results with 'production' preset:")
        print(f"Original records: {len(dummy_added)}")
        print(f"After filtering: {len(filtered_added)}")

        for record in filtered_added:
            object_fqn = cfg._build_object_fqn(record)
            is_critical = cfg.is_critical(record)
            print(
                f"  - {object_fqn}: {record['privilege']} -> {record['grantee_name']} (critical: {is_critical})"
            )

    except (ConfigError, ValidationError) as e:
        logger.error(f"Configuration error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
