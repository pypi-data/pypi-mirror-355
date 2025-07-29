from pathlib import Path

import pytest

from pullapprove.config import ConfigModel, ConfigModels


@pytest.mark.parametrize(
    ("config_data", "expected"),
    [
        (
            {
                "aliases": {
                    "team": ["alice", "bob"],
                    "qa": ["carol"],
                    "extras": ["bob", "dave"],
                },
                "scopes": [
                    {
                        "name": "all",
                        "paths": ["*"],
                        "authors": ["$team", "carol", "$extras", "frank"],
                        "reviewers": ["$qa", "$team", "carol"],
                        "alternates": ["$extras", "grace", "$qa"],
                        "cc": ["$team", "$team", "eve"],
                        "labels": ["$qa", "bug", "bug"],
                    }
                ],
                "large_scale_change": {
                    "reviewers": ["$team", "hank", "$extras"],
                    "labels": ["$qa", "$qa", "feature"],
                },
            },
            {
                "authors": ["alice", "bob", "carol", "dave", "frank"],
                "reviewers": ["carol", "alice", "bob"],
                "alternates": ["bob", "dave", "grace", "carol"],
                "cc": ["alice", "bob", "eve"],
                "labels": ["carol", "bug"],
                "lsc_reviewers": ["alice", "bob", "hank", "dave"],
                "lsc_labels": ["carol", "feature"],
            },
        )
    ],
)
def test_alias_expansion(config_data, expected):
    config = ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))
    configs = ConfigModels.from_config_models({"CODEREVIEW.toml": config})

    compiled = config.compiled_config(Path("CODEREVIEW.toml"), configs.root)

    scope = compiled.scopes[0]
    assert scope.authors == expected["authors"]
    assert scope.reviewers == expected["reviewers"]
    assert scope.alternates == expected["alternates"]
    assert scope.cc == expected["cc"]
    assert scope.labels == expected["labels"]

    lsc = compiled.large_scale_change
    assert lsc.reviewers == expected["lsc_reviewers"]
    assert lsc.labels == expected["lsc_labels"]
