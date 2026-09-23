"""Foundation-level tests."""

from marketplace_manager.core.config import DATA_DIR, LOG_DIR, PROJECT_ROOT


def test_project_paths_are_based_at_repository_root() -> None:
    """The app keeps generated files in predictable project folders."""
    assert PROJECT_ROOT.name == "MarketplaceManager"
    assert DATA_DIR == PROJECT_ROOT / "data"
    assert LOG_DIR == PROJECT_ROOT / "logs"
