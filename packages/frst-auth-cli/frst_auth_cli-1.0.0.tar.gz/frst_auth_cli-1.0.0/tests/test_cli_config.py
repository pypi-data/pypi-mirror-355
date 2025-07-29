import os
import json
import tempfile
from typer.testing import CliRunner
from frst_auth_cli.cli import app, DEFAULT_CONFIG

runner = CliRunner()


def test_config_init_creates_file(monkeypatch):
    # Use a temporary directory to isolate the test
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_config_dir = os.path.join(tmpdir, ".frst_auth_cli")
        fake_config_path = os.path.join(fake_config_dir, "config.json")

        # Monkeypatch the global CONFIG_PATH
        monkeypatch.setattr("frst_auth_cli.config.CONFIG_PATH", fake_config_path)  # noqa E501

        # Call the CLI command
        result = runner.invoke(app, ["config", "init", "--force"])
        assert result.exit_code == 0
        assert os.path.exists(fake_config_path)

        # Check if the file content is correct
        with open(fake_config_path, "r") as f:
            data = json.load(f)
            assert data == DEFAULT_CONFIG


def test_config_show(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_config_dir = os.path.join(tmpdir, ".frst_auth_cli")
        fake_config_path = os.path.join(fake_config_dir, "config.json")

        # Monkeypatch the global CONFIG_PATH
        monkeypatch.setattr("frst_auth_cli.config.CONFIG_PATH", fake_config_path)  # noqa E501

        # Create a fake config before the test
        os.makedirs(fake_config_dir, exist_ok=True)
        with open(fake_config_path, "w") as f:
            json.dump(DEFAULT_CONFIG, f)

        # Run the CLI show command
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "aws-dev" in result.output  # Check for expected output content
