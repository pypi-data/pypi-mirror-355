"""
Tests for the release script functionality.

This module tests the core functions of the release script to ensure
they work correctly for version management and git operations.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the scripts directory to the path so we can import the release script
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

try:
    import release
except ImportError:
    pytest.skip("Release script not available", allow_module_level=True)


class TestReleaseScript:
    """Test cases for the release script functions."""

    def test_validate_version_valid_versions(self):
        """Test that valid version strings are accepted."""
        valid_versions = [
            "0.1.0",
            "1.0.0",
            "2.3.4",
            "0.1.0-alpha",
            "1.0.0-beta.1",
            "2.0.0-rc.1",
        ]

        for version in valid_versions:
            assert release.validate_version(
                version
            ), f"Version {version} should be valid"

    def test_validate_version_invalid_versions(self):
        """Test that invalid version strings are rejected."""
        invalid_versions = [
            "1.0",  # Missing patch version
            "1",  # Missing minor and patch
            "v1.0.0",  # Has 'v' prefix
            "1.0.0.0",  # Too many components
            "1.0.0-",  # Empty pre-release
            "1.0.0-alpha.",  # Invalid pre-release
            "abc.def.ghi",  # Non-numeric
            "",  # Empty string
        ]

        for version in invalid_versions:
            assert not release.validate_version(
                version
            ), f"Version {version} should be invalid"

    def test_get_current_version_success(self):
        """Test extracting version from a valid pyproject.toml."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """[project]
name = "test-package"
version = "0.2.0"
description = "Test package"
"""
            )
            f.flush()

            # Temporarily change to the directory containing the file
            original_cwd = os.getcwd()
            temp_dir = os.path.dirname(f.name)
            os.chdir(temp_dir)

            # Rename the temp file to pyproject.toml
            os.rename(f.name, os.path.join(temp_dir, "pyproject.toml"))

            try:
                version = release.get_current_version()
                assert version == "0.2.0"
            finally:
                os.chdir(original_cwd)
                os.unlink(os.path.join(temp_dir, "pyproject.toml"))

    def test_get_current_version_no_file(self):
        """Test behavior when pyproject.toml doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                version = release.get_current_version()
                assert version is None
            finally:
                os.chdir(original_cwd)

    def test_update_version_dry_run(self):
        """Test updating version in dry run mode."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """[project]
name = "test-package"
version = "0.2.0"
description = "Test package"
"""
            )
            f.flush()

            original_cwd = os.getcwd()
            temp_dir = os.path.dirname(f.name)
            os.chdir(temp_dir)

            os.rename(f.name, os.path.join(temp_dir, "pyproject.toml"))

            try:
                # Test dry run - should not modify file
                result = release.update_version("0.3.0", dry_run=True)
                assert result is True

                # Verify file wasn't changed
                with open("pyproject.toml", "r") as check_file:
                    content = check_file.read()
                    assert 'version = "0.2.0"' in content
                    assert 'version = "0.3.0"' not in content

            finally:
                os.chdir(original_cwd)
                os.unlink(os.path.join(temp_dir, "pyproject.toml"))

    def test_update_version_actual(self):
        """Test actually updating version in the file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """[project]
name = "test-package"
version = "0.2.0"
description = "Test package"
"""
            )
            f.flush()

            original_cwd = os.getcwd()
            temp_dir = os.path.dirname(f.name)
            os.chdir(temp_dir)

            os.rename(f.name, os.path.join(temp_dir, "pyproject.toml"))

            try:
                # Test actual update
                result = release.update_version("0.3.0", dry_run=False)
                assert result is True

                # Verify file was changed
                with open("pyproject.toml", "r") as check_file:
                    content = check_file.read()
                    assert 'version = "0.3.0"' in content
                    assert 'version = "0.2.0"' not in content

            finally:
                os.chdir(original_cwd)
                os.unlink(os.path.join(temp_dir, "pyproject.toml"))

    @patch("release.run_command")
    def test_check_git_status_clean(self, mock_run_command):
        """Test git status check when working directory is clean."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_run_command.return_value = mock_result

        result = release.check_git_status()
        assert result is True
        mock_run_command.assert_called_once_with(["git", "status", "--porcelain"])

    @patch("release.run_command")
    def test_check_git_status_dirty(self, mock_run_command):
        """Test git status check when working directory has changes."""
        mock_result = MagicMock()
        mock_result.stdout = " M some_file.py\n?? new_file.py"
        mock_run_command.return_value = mock_result

        result = release.check_git_status()
        assert result is False

    @patch("release.run_command")
    def test_check_git_branch_main(self, mock_run_command):
        """Test git branch check when on main branch."""
        mock_result = MagicMock()
        mock_result.stdout = "main"
        mock_run_command.return_value = mock_result

        result = release.check_git_branch()
        assert result is True

    @patch("release.run_command")
    @patch("builtins.input", return_value="n")
    def test_check_git_branch_not_main(self, mock_input, mock_run_command):
        """Test git branch check when not on main branch."""
        mock_result = MagicMock()
        mock_result.stdout = "feature-branch"
        mock_run_command.return_value = mock_result

        result = release.check_git_branch()
        assert result is False

    @patch("release.run_command")
    def test_create_git_tag_dry_run(self, mock_run_command):
        """Test creating git tag in dry run mode."""
        # Mock git tag -l to return empty (tag doesn't exist)
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_run_command.return_value = mock_result

        result = release.create_git_tag("0.3.0", dry_run=True)
        assert result is True

        # Should only check if tag exists, not create it
        mock_run_command.assert_called_once_with(
            ["git", "tag", "-l", "v0.3.0"], check=False
        )

    @patch("release.run_command")
    def test_create_git_tag_existing_tag(self, mock_run_command):
        """Test creating git tag when tag already exists."""
        # Mock git tag -l to return the tag (tag exists)
        mock_result = MagicMock()
        mock_result.stdout = "v0.3.0"
        mock_run_command.return_value = mock_result

        result = release.create_git_tag("0.3.0", dry_run=False)
        assert result is False

    def test_print_release_instructions_dry_run(self, capsys):
        """Test printing release instructions for dry run."""
        release.print_release_instructions("0.3.0", dry_run=True)
        captured = capsys.readouterr()

        assert "DRY RUN COMPLETE" in captured.out
        assert "python scripts/release.py --version 0.3.0" in captured.out

    def test_print_release_instructions_actual(self, capsys):
        """Test printing release instructions for actual release."""
        release.print_release_instructions("0.3.0", dry_run=False)
        captured = capsys.readouterr()

        assert "RELEASE PREPARATION COMPLETE" in captured.out
        assert "git push origin main" in captured.out
        assert "git push origin v0.3.0" in captured.out
        assert "GitHub Actions" in captured.out


class TestReleaseScriptIntegration:
    """Integration tests for the release script."""

    def test_version_format_edge_cases(self):
        """Test edge cases for version format validation."""
        # Test boundary cases
        assert release.validate_version("0.0.0")
        assert release.validate_version("999.999.999")
        assert release.validate_version("1.0.0-alpha")
        assert release.validate_version("1.0.0-beta.999")

        # Test invalid formats
        assert not release.validate_version("01.0.0")  # Leading zero
        assert not release.validate_version("1.0.0-")  # Trailing dash
        assert not release.validate_version("1.0.0-.")  # Invalid pre-release

    @patch("release.get_current_version")
    @patch("release.check_git_status")
    @patch("release.check_git_branch")
    @patch("release.update_version")
    @patch("release.create_git_tag")
    def test_main_dry_run_flow(
        self,
        mock_create_tag,
        mock_update_version,
        mock_check_branch,
        mock_check_status,
        mock_get_version,
    ):
        """Test the main function flow in dry run mode."""
        # Setup mocks
        mock_get_version.return_value = "0.2.0"
        mock_check_status.return_value = True
        mock_check_branch.return_value = True
        mock_update_version.return_value = True
        mock_create_tag.return_value = True

        # Mock sys.argv
        test_args = ["release.py", "--version", "0.3.0", "--dry-run"]
        with patch("sys.argv", test_args):
            # This would normally call sys.exit, but we'll catch it
            with pytest.raises(SystemExit) as exc_info:
                release.main()

            # Should exit with code 0 (success)
            assert exc_info.value.code is None or exc_info.value.code == 0

        # Verify all functions were called
        mock_get_version.assert_called_once()
        mock_check_status.assert_called_once()
        mock_check_branch.assert_called_once()
        mock_update_version.assert_called_once_with("0.3.0", True)
        mock_create_tag.assert_called_once_with("0.3.0", True)
