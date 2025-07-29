from pathlib import Path

from pullapprove.config import ConfigModel, ConfigModels
from pullapprove.matches import match_diff


def test_empty_configs():
    configs = ConfigModels.from_configs_data({"CODEREVIEW.toml": {}})
    assert bool(configs)
    assert "CODEREVIEW.toml" in configs
    assert not configs["CODEREVIEW.toml"].template


def test_angular_diff(snapshot):
    cfg = ConfigModel.from_filesystem(Path(__file__).parent / "config.toml")
    configs = ConfigModels.from_config_models({"CODEREVIEW.toml": cfg})
    diff = (Path(__file__).parent / "test.diff").read_text()
    matches, config_paths_modified = match_diff(configs, diff)
    assert not config_paths_modified
    assert snapshot("angular.json") == matches.model_dump()
