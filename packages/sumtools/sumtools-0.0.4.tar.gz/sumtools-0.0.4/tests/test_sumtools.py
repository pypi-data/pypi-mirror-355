"""Tests for `sumtools` package."""

from typer.testing import CliRunner

from sumtools import cli


def test_sumtools_cli():
    """Test the CLI interface."""
    runner = CliRunner()
    result = runner.invoke(cli.app)
    assert result.exit_code == 0
    assert "sumtools" in result.output
    assert "a suite for summary level GWAS downstream analysis" in result.output


def test_sumtools_import():
    """Test that the package can be imported."""
    import sumtools

    assert hasattr(sumtools, "__version__")
    assert sumtools.__version__ == "0.0.3"
