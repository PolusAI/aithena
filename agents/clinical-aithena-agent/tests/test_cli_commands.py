"""Smoke tests for the ct-aithena CLI commands.

Tests help text output and basic argument parsing for all CLI commands
without actually executing database operations.
"""

from typer.testing import CliRunner

import pytest

from polus.aithena.clinical_aithena.cli.main import app


runner = CliRunner()


class TestCLIRoot:
    """Tests for the root CLI application."""

    def test_no_args_shows_help(self):
        """Test that running with no args shows help (exit code 0 or 2 for no_args_is_help)."""
        result = runner.invoke(app, [])
        assert result.exit_code in (0, 2)
        assert "Clinical Aithena CLI" in result.output

    def test_help_flag(self):
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "ct-aithena" in result.output or "Clinical Aithena" in result.output

    def test_version_flag(self):
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()


class TestInitDBCommand:
    """Smoke tests for the initdb command."""

    def test_help(self):
        """Test initdb --help displays help text."""
        result = runner.invoke(app, ["initdb", "--help"])
        assert result.exit_code == 0
        assert "database" in result.output.lower() or "Database" in result.output

    def test_help_shows_database_url_option(self):
        """Test that initdb help shows the database-url option."""
        result = runner.invoke(app, ["initdb", "--help"])
        assert result.exit_code == 0
        assert "database" in result.output.lower()


class TestUpdateDBCommand:
    """Smoke tests for the updatedb command."""

    def test_help(self):
        """Test updatedb --help displays help text."""
        result = runner.invoke(app, ["updatedb", "--help"])
        assert result.exit_code == 0
        assert "update" in result.output.lower() or "download" in result.output.lower()

    def test_help_shows_database_url_option(self):
        """Test that updatedb help shows the database-url option."""
        result = runner.invoke(app, ["updatedb", "--help"])
        assert result.exit_code == 0
        assert "database" in result.output.lower()


class TestTransformCommand:
    """Smoke tests for the transform command."""

    def test_help(self):
        """Test transform --help displays help text."""
        result = runner.invoke(app, ["transform", "--help"])
        assert result.exit_code == 0
        assert "transform" in result.output.lower() or "trial" in result.output.lower()

    def test_help_shows_database_url_option(self):
        """Test that transform help shows the database-url option."""
        result = runner.invoke(app, ["transform", "--help"])
        assert result.exit_code == 0
        assert "database" in result.output.lower()


class TestEmbedCommand:
    """Smoke tests for the embed command."""

    def test_help(self):
        """Test embed --help displays help text."""
        result = runner.invoke(app, ["embed", "--help"])
        assert result.exit_code == 0
        assert "embed" in result.output.lower()

    def test_help_shows_database_url_option(self):
        """Test that embed help shows the database-url option."""
        result = runner.invoke(app, ["embed", "--help"])
        assert result.exit_code == 0
        assert "database" in result.output.lower()

    def test_help_shows_litellm_option(self):
        """Test that embed help shows the litellm-url option."""
        result = runner.invoke(app, ["embed", "--help"])
        assert result.exit_code == 0
        assert "litellm" in result.output.lower()


class TestDiffStudyCommand:
    """Smoke tests for the diff-study command."""

    def test_help(self):
        """Test diff-study --help displays help text."""
        result = runner.invoke(app, ["diff-study", "--help"])
        assert result.exit_code == 0
        # Just verify it doesn't crash and shows something
        assert len(result.output) > 0
