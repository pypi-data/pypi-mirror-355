from pullapprove.pullrequests import (
    Branch,
    PullRequest,
    PullRequestResults,
    ScopeModel,
    ScopeResult,
    Status,
    User,
)


def _minimal_pr():
    return PullRequest(
        base_branch=Branch(name="main"),
        head_branch=Branch(name="feature"),
        commits=[],
        reviewers=[],
        author=User(host_id="1", username="alice", avatar_url=""),
        diff="",
        number=1,
        draft=False,
    )


def test_compute_overview_example(snapshot):
    scope = ScopeModel(
        name="docs",
        paths=["docs/**"],
        reviewers=["bob"],
        cc=["charlie", "dave"],
        instructions="Ensure documentation follows guidelines.",
        require=1,
    )
    scope_result = ScopeResult(
        scope=scope,
        status=Status.PENDING,
        points=0,
        points_pending=1,
        reviews=[],
        matched_paths=["docs/readme.md"],
        matched_code=[],
    )

    results = PullRequestResults(
        status=Status.PENDING,
        description="1 review scope pending",
        labels=[],
        pullrequest=_minimal_pr(),
        large_scale_change_results=None,
        scope_results={"docs": scope_result},
        path_results={},
        code_results={},
        review_results={},
        config_results={},
        config_paths_modified=[],
    )

    overview = results.compute_overview()
    assert snapshot("overview.txt") == overview
