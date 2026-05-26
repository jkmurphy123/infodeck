"""Tests for InfodeckConfig."""

from pathlib import Path

from infodeck.config import InfodeckConfig, load_config


class TestInfodeckConfig:
    def test_defaults(self):
        config = InfodeckConfig()
        assert config.ui.title == "Infodeck"
        assert config.ui.default_mode == "github"
        assert config.github.owner == "jkmurphy123"
        assert config.github.max_repos == 50
        assert config.memory.backup_on_save is True
        assert config.memory.hermes_dir == "/home/ubuntu/.hermes"

    def test_project_root_without_source(self):
        config = InfodeckConfig()
        assert config.project_root == Path.cwd()

    def test_project_root_with_source(self):
        config = InfodeckConfig(source_path=Path("/tmp/frontend.yaml"))
        assert config.project_root == Path("/tmp")

    def test_cache_dir(self):
        config = InfodeckConfig(source_path=Path("/tmp/frontend.yaml"))
        assert config.cache_dir == Path("/tmp/cache")

    def test_load_config_from_file(self, tmp_path):
        config_path = tmp_path / "frontend.yaml"
        config_path.write_text("""
ui:
  title: Custom Title
  default_mode: memory
github:
  owner: testowner
  max_repos: 20
""")
        config = load_config(config_path)
        assert config.ui.title == "Custom Title"
        assert config.ui.default_mode == "memory"
        assert config.github.owner == "testowner"
        assert config.github.max_repos == 20
        assert config.source_path == config_path

    def test_load_config_nonexistent(self):
        config = load_config(Path("/nonexistent/config.yaml"))
        assert config.ui.title == "Infodeck"

    def test_load_config_no_path_no_default(self):
        config = load_config(None)
        assert config.ui.title == "Infodeck"
