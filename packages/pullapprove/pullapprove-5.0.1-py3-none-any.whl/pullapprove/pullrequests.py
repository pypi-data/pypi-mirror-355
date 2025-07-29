import re
from collections.abc import Generator
from enum import Enum
from random import Random
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .config import (
    ConfigModel,
    ConfigModels,
    LargeScaleChangeModel,
    OwnershipChoices,
    ReviewedForChoices,
    ScopeModel,
)
from .matches import ChangeMatches, ScopeCodeMatch, ScopePathMatch, match_diff


# Could be a bool if these are literally the only two states?
class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    PENDING = "PENDING"
    EMPTY = ""


class User(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host_id: str = Field(min_length=1)
    username: str = Field(min_length=1)
    avatar_url: str

    def __str__(self) -> str:
        return self.username

    def __eq__(self, value):
        if isinstance(value, User):
            return self.host_id == value.host_id
        elif isinstance(value, str):
            return self.host_id == value or self.username == value
        return False


class ReviewStates(str, Enum):
    APPROVED = "APPROVED"
    PENDING = "PENDING"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    EMPTY = ""


class Review(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host_id: str = Field(min_length=1)
    host_url: str = Field(min_length=1)
    body: str
    state: ReviewStates
    submitted_at: str
    user: User

    def get_reviewed_for_scopes(self):
        if self.body:
            # Parse Reviewed-for: <scope> from the body (could be comma separated)
            if matches := re.findall(
                r"Reviewed-for:\s*(\S+)", self.body, re.IGNORECASE
            ):
                return [match.strip() for match in matches[0].split(",")]

        return []


class Reviewer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviews: list[Review]
    user: User

    def __str__(self) -> str:
        return str(self.user)

    def latest_review(self, scope=None) -> Review | None:
        if not self.reviews:
            return None

        # Most recent valid review is the one we want
        sorted_reviews = sorted(
            self.reviews, key=lambda r: r.submitted_at, reverse=True
        )

        for review in sorted_reviews:
            if scope and scope.reviewed_for != ReviewedForChoices.IGNORED:
                review_scopes = review.get_reviewed_for_scopes()

                # Some scopes are required, so review_scopes can't be empty
                if (
                    scope.reviewed_for == ReviewedForChoices.REQUIRED
                    and not review_scopes
                ):
                    continue

                if review_scopes and scope.name not in review_scopes:
                    continue

                # Otherwise review_scopes are [] and that is ok for everything

            # If a review has no known state, we skip it (commented on GitHub)
            if review.state:
                return review

        return None

    def get_review_state(self) -> ReviewStates:
        if review := self.latest_review():
            return review.state

        # They are pending if they are a reviewer with no specific state
        return ReviewStates.PENDING


class Branch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    # could be fork, other repo...


class Commit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sha: str = Field(min_length=1)
    message: str
    author: User
    coauthors: list[User]


class PullRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_branch: Branch
    head_branch: Branch
    commits: list[Commit]
    reviewers: list[Reviewer]  # Includes requested and previous reviewers
    author: User
    diff: str | Generator = Field(exclude=True, default="")
    number: int
    draft: bool

    # Configs actually come from outside the PR, so we don't attach it here

    def get_reviewer(self, identifier):
        for reviewer in self.reviewers:
            if reviewer.user.host_id == identifier:
                return reviewer

            if reviewer.user.username == identifier:
                return reviewer

        return None

    def process_configs(self, configs: ConfigModels) -> Optional["PullRequestResults"]:
        if not configs:
            return None

        filtered_configs = configs.filter_for_pullrequest(self)

        # If there are no configs, or they are are disabled, then we can return early
        if not filtered_configs:
            return None

        change_matches, config_paths_modified = match_diff(filtered_configs, self.diff)

        # If it's a large scale change, that's the only thing we need to consider (after branches)
        if change_matches.large_scale_change:
            return self.process_large_scale_change(change_matches)

        results = PullRequestResults(
            pullrequest=self,
            status=Status.PENDING,
            description="",
            labels=[],
            large_scale_change_results=None,
            scope_results={},
            path_results={},
            code_results={},
            review_results={},
            config_results={
                path: ConfigResult.from_config_model(config)
                for path, config in change_matches.configs.items()
            },
            config_paths_modified=config_paths_modified,
        )

        # Iterate the active scopes and get their results
        for scope_name, scope_model in change_matches.scopes.items():
            reviews = []
            review_points = 0
            pending_points = 0

            for reviewer in self.reviewers:
                # Could maybe enable host id, or email too
                if (
                    reviewer.user.username not in scope_model.reviewers
                    and reviewer.user.username not in scope_model.alternates
                ):
                    continue

                if review := reviewer.latest_review(scope=scope_model):
                    reviews.append(review.host_id)
                    results.review_results[review.host_id] = ReviewResult(
                        review=review,
                        scopes=review.get_reviewed_for_scopes(),
                    )

                    if review.state == ReviewStates.APPROVED:
                        review_points += 1
                    elif review.state in (
                        ReviewStates.PENDING,
                        ReviewStates.CHANGES_REQUESTED,
                    ):
                        pending_points += 1
                else:
                    # They exist on the PR but with no review yet
                    pending_points += 1

            if self.author.username in scope_model.reviewers:
                author_points = scope_model.author_value
            else:
                author_points = 0

            # TODO commit points
            commit_points = 0

            points = review_points + author_points + commit_points

            if any(
                results.review_results[review].review.state
                == ReviewStates.CHANGES_REQUESTED
                for review in reviews
            ):
                status = Status.FAIL
            elif points >= scope_model.require:
                status = Status.PASS
            else:
                status = Status.PENDING

            matched_paths = []
            for path, path_match in change_matches.paths.items():
                if scope_name in path_match.scopes:
                    matched_paths.append(path)

            matched_code = []
            for code, code_match in change_matches.code.items():
                if scope_name in code_match.scopes:
                    matched_code.append(code)

            results.scope_results[scope_name] = ScopeResult(
                scope=scope_model,
                status=status,
                points=points,
                # separate commit points, review points, author points etc?
                points_pending=pending_points,  # Not using this anywhere? would tell us how many to request...
                reviews=reviews,
                matched_paths=matched_paths,
                matched_code=matched_code,
            )

        # Now we have to get the status of the results overall by looking
        # at the paths and code, because scopes can combine based on their ownership model,
        # so looking at scopes alone isn't enough.

        for path, path_match in change_matches.paths.items():
            results.path_results[path] = PathResult(
                path=path_match,
                status=results.status_for_scope_names(path_match.scopes),
                reviews=results.reviews_for_scope_names(path_match.scopes),
            )

        for code_hash, code_match in change_matches.code.items():
            results.code_results[code_hash] = CodeResult(
                code=code_match,
                status=results.status_for_scope_names(code_match.scopes),
                reviews=results.reviews_for_scope_names(code_match.scopes),
            )

        # TODO what happens if no scopes match?
        # configurable in pullapprove.com?

        results.status = results.compute_status()
        results.description = results.compute_description()
        results.labels = results.compute_labels()

        return results

    def process_large_scale_change(
        self, change_matches: ChangeMatches
    ) -> "PullRequestResults":
        lsc = change_matches.large_scale_change
        reviews = []
        review_points = 0
        pending_points = 0
        review_results = {}

        config_results = {
            path: ConfigResult.from_config_model(config)
            for path, config in change_matches.configs.items()
        }

        for reviewer in self.reviewers:
            # Could maybe enable host id, or email too
            if reviewer.user.username not in lsc.reviewers:
                continue

            # TODO what about Reviewed-for?
            if review := reviewer.latest_review(scope=None):
                reviews.append(review.host_id)
                review_results[review.host_id] = ReviewResult(
                    review=review,
                    scopes=review.get_reviewed_for_scopes(),
                )

                if review.state == ReviewStates.APPROVED:
                    review_points += 1
                elif review.state in (
                    ReviewStates.PENDING,
                    ReviewStates.CHANGES_REQUESTED,
                ):
                    pending_points += 1
            else:
                # They exist on the PR but with no review yet
                pending_points += 1

        if any(
            review_results[review].review.state == ReviewStates.CHANGES_REQUESTED
            for review in reviews
        ):
            status = Status.FAIL
            description = "Large-scale change: changes requested"
        elif review_points >= lsc.require:
            status = Status.PASS
            description = "Large-scale change: approved"
        else:
            status = Status.PENDING
            description = f"Large-scale change: {review_points} of {lsc.require} reviewers approved"

        # If reviewers were not defined (default LSC config),
        # then we show an error.
        if not lsc.reviewers:
            status = Status.FAIL
            description = (
                "Large-scale change: configuration required (no reviewers defined)"
            )

        return PullRequestResults(
            status=status,
            description=description,
            labels=lsc.labels,
            large_scale_change_results=LargeScaleChangeResults(
                large_scale_change=lsc,
                status=status,
                points=review_points,
                points_pending=pending_points,
                reviews=reviews,
            ),
            scope_results={},
            path_results={},
            code_results={},
            review_results=review_results,
            pullrequest=self,
            config_results=config_results,
            config_paths_modified=[],
        )


class LargeScaleChangeResults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    large_scale_change: LargeScaleChangeModel
    status: Status
    points: int
    points_pending: int
    reviews: list[str]


class PullRequestResults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # No defaults in this model, so we will always get all fields represented in the export
    status: Status
    description: str
    labels: list[str]
    # comments?

    config_paths_modified: list[str] = Field(
        default_factory=list
    )  # Paths that were modified in the PR

    pullrequest: PullRequest

    large_scale_change_results: LargeScaleChangeResults | None
    scope_results: dict[str, "ScopeResult"]
    path_results: dict[str, "PathResult"]
    code_results: dict[str, "CodeResult"]
    review_results: dict[str, "ReviewResult"]  # Latest reviews and their scopes...
    config_results: dict[str, "ConfigResult"]

    def as_dict(self) -> dict:
        """
        Dump the results as a dictionary and remove any values that aren't the same
        as the defaults (we always use "empty" defaults) -- this keeps the stored JSON more minimal.

        In the UI, the actual models are reloaded from the dict, so it is ok that we don't have all the information in the stored dict.
        """
        return self.model_dump(exclude_defaults=True)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

    def get_scope_results_by_name(self, names):
        """
        Get scopes by name (from other result objects),
        and return them in as ordered_scope_results() order.
        """
        filtered_scopes = [
            scope_result
            for scope_result in self.ordered_scope_results()
            if scope_result.scope.name in names
        ]
        return filtered_scopes

    def ordered_scope_results(self):
        """Order by ownership (primary will naturally come first, then appended, then global)"""
        return sorted(
            self.scope_results.values(),
            key=lambda s: s.scope.ownership,
        )

    def scope_results_pending(self):
        """Get all scope results that are pending"""
        return [
            scope_result
            for scope_result in self.scope_results.values()
            if scope_result.status == Status.PENDING
            and scope_result.scope.ownership != OwnershipChoices.GLOBAL
        ]

    def path_results_pending(self):
        """Get all path results that are pending"""
        return [
            path_result
            for path_result in self.path_results.values()
            if path_result.status == Status.PENDING
        ]

    def code_results_pending(self):
        """Get all code results that are pending"""
        return [
            code_result
            for code_result in self.code_results.values()
            if code_result.status == Status.PENDING
        ]

    def status_for_scope_names(self, scope_names: list[str]) -> Status:
        """
        Get the status for a list of scopes.
        This is used to get the status for a list of scopes.
        """
        scope_results = [self.scope_results[scope_name] for scope_name in scope_names]

        # If there's a single scope, use that result (whether it is global, or normal, etc)
        if len(scope_results) == 1:
            return scope_results[0].status

        # If any scope failed, then we fail
        if any(scope.status == Status.FAIL for scope in scope_results):
            return Status.FAIL

        global_scopes = [
            scope
            for scope in scope_results
            if scope.scope.ownership == OwnershipChoices.GLOBAL
        ]
        nonglobal_scopes = [
            scope
            for scope in scope_results
            if scope.scope.ownership != OwnershipChoices.GLOBAL
        ]

        # If any global scopes approved, then we pass
        if any(scope.status == Status.PASS for scope in global_scopes):
            return Status.PASS

        # If all regular scopes approved, then we pass
        if all(scope.status == Status.PASS for scope in nonglobal_scopes):
            return Status.PASS

        return Status.PENDING

    def reviews_for_scope_names(self, scope_names: list[str]) -> list[str]:
        """
        Get the reviews for a list of scopes.
        This is used to get the reviews for a list of scopes.
        """
        scope_results = [self.scope_results[scope_name] for scope_name in scope_names]
        reviews = []
        for scope in scope_results:
            reviews.extend(scope.reviews)
        return reviews

    def compute_status(self) -> Status:
        if self.pullrequest.draft:
            return Status.PENDING

        # Assume passing status to start
        # TODO is this the unmatched status? what if there are no enabled scopes
        status = Status.PASS

        for path_results in self.path_results.values():
            if path_results.status == Status.FAIL:
                return Status.FAIL  # Immediately fail if any fail
            elif path_results.status == Status.PENDING:
                status = Status.PENDING  # Move to pending (could fail later)

        for code_results in self.code_results.values():
            if code_results.status == Status.FAIL:
                return Status.FAIL  # Immediately fail if any fail
            elif code_results.status == Status.PENDING:
                status = Status.PENDING  # Move to pending (could fail later)

        return status

    def compute_description(self) -> str:
        if self.pullrequest.draft:
            return "Draft is not ready for review"

        if self.status == Status.PASS:
            # In success, want to know how many scopes passed
            scopes_passed = [
                scope
                for scope in self.scope_results.values()
                if scope.status == Status.PASS
            ]

            if not scopes_passed:
                # If the status was pass, but there are no scopes, then there were none assigned
                return "No review scopes are required"

            scope_text = "scope" if len(scopes_passed) == 1 else "scopes"
            return f"{len(scopes_passed)} review {scope_text} passed"
        elif self.status == Status.FAIL:
            scopes_failed = [
                scope
                for scope in self.scope_results.values()
                if scope.status == Status.FAIL
            ]
            scope_text = "scope" if len(scopes_failed) == 1 else "scopes"
            return f"{len(scopes_failed)} review {scope_text} failed"
        elif self.status == Status.PENDING:
            # In pending, want to know how many scopes are pending
            scopes_passed = [
                scope
                for scope in self.scope_results.values()
                if scope.status == Status.PASS
            ]
            scopes_pending = [
                scope
                for scope in self.scope_results.values()
                if scope.status == Status.PENDING
                and scope.scope.ownership != OwnershipChoices.GLOBAL
            ]
            pending_text = "scope" if len(scopes_pending) == 1 else "scopes"
            if scopes_passed:
                passed_text = "scope" if len(scopes_passed) == 1 else "scopes"
                return f"{len(scopes_pending)} review {pending_text} pending, {len(scopes_passed)} review {passed_text} passed"
            else:
                return f"{len(scopes_pending)} review {pending_text} pending"
        else:
            return ""

    def compute_labels(self) -> list[str]:
        labels = set()

        for scope_result in self.scope_results.values():
            labels.update(scope_result.scope.labels)

        return list(labels)

    def compute_overview(self) -> str:
        """Build a concise markdown overview for GitHub pull request comments."""
        overview = ""
        overview += f"**{self.status.value}**: {self.description}\n\n"

        if self.large_scale_change_results:
            lsc = self.large_scale_change_results
            overview += (
                "### Large Scale Change\n\n"
                f"- Status: {lsc.status.value}\n"
                f"- Points: {lsc.points} (Pending: {lsc.points_pending})\n"
            )

        overview += "## Matched Scopes\n\n"
        matched_scopes = [
            sr
            for sr in self.ordered_scope_results()
            if sr.matched_paths or sr.matched_code
        ]

        if matched_scopes:
            for scope_result in matched_scopes:
                line = (
                    f"- **{scope_result.scope.printed_name()}**: {scope_result.status.value}"
                    f" ({scope_result.points}/{scope_result.scope.require})"
                )
                if scope_result.scope.cc:
                    line += " cc: " + " ".join(f"@{u}" for u in scope_result.scope.cc)
                overview += line + "\n"

                if scope_result.scope.instructions:
                    overview += (
                        "  <details>\n"
                        f"  {scope_result.scope.instructions}\n"
                        "  </details>\n"
                    )
        else:
            overview += "- None\n"

        return overview

    def rebuild_config_models(self) -> ConfigModels:
        """
        Rebuild the ConfigModels from the config_results.
        This is useful for when we want to get the configs back from the results.
        """
        configs = ConfigModels(root={})
        for path, config_result in self.config_results.items():
            configs.add_config(config_result.config, path)
        return configs


class ConfigResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    config: ConfigModel

    @classmethod
    def from_config_model(cls, config_model: ConfigModel):
        return cls(
            config=config_model,
        )


class ReviewResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review: Review
    scopes: list[str]


class ScopeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: ScopeModel
    status: Status  # and/or review_status?
    points: int
    points_pending: int

    reviews: list[str]  # Review references
    matched_paths: list[str]  # Path result references
    matched_code: list[str]  # Code result references

    def is_notable(self):
        # In some cases, we don't care much about scopes that are global and not in use, for example
        if (
            self.scope.ownership == OwnershipChoices.GLOBAL
            and self.status == Status.PENDING
        ):
            return False
        return True

    def reviewers_to_request(
        self, pullrequest_results: PullRequestResults
    ) -> list[str]:
        if self.scope.request == 0 or not self.scope.reviewers:
            return []

        additional_reviewers_needed = (
            self.scope.request - self.points - self.points_pending
        )
        if additional_reviewers_needed <= 0:
            return []

        already_reviewed = pullrequest_results.review_results.values()

        eligible_logins = [
            login for login in self.scope.reviewers if login not in already_reviewed
        ]

        # Remove the author from the list of eligible reviewers
        if pullrequest_results.pullrequest.author.username in eligible_logins:
            eligible_logins.remove(pullrequest_results.pullrequest.author.username)

        if self.scope.request < 0:
            return eligible_logins

        # Put the reviewers in a predictable random order for this PR
        Random(pullrequest_results.pullrequest.number).shuffle(eligible_logins)

        return eligible_logins[:additional_reviewers_needed]


class PathResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: ScopePathMatch
    status: Status
    reviews: list[str]  # Review references


class CodeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: ScopeCodeMatch
    status: Status
    reviews: list[str]  # Review references
