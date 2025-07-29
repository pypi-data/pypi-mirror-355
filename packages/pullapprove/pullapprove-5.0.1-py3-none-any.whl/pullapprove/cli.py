import os
import sys
from pathlib import Path
from textwrap import dedent

import click
from pydantic import ValidationError

from . import git
from .config import CONFIG_FILENAME, CONFIG_FILENAME_PREFIX, ConfigModel, ConfigModels
from .matches import match_diff, match_files


@click.group()
def cli():
    pass


@cli.command()
@click.option("--filename", default=CONFIG_FILENAME, help="Configuration filename")
def init(filename):
    config_path = Path(filename)
    if config_path.exists():
        click.secho(f"{CONFIG_FILENAME} already exists!", fg="red")
        sys.exit(1)

    # Could we use blame to guess?
    # go straight to agent?
    # gh auth status can give us the user? or ask what's their username?
    # keep it simple - agent can do more when I get to it

    contents = """
    [[scopes]]
    name = "default"
    paths = ["**/*"]
    request = 1
    require = 1
    reviewers = ["<YOU>"]

    [[scopes]]
    name = "pullapprove"
    paths = ["**/CODEREVIEW.toml"]
    request = 1
    require = 1
    """
    config_path.write_text(dedent(contents).strip() + "\n")
    click.secho(f"Created {filename}")


@cli.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--quiet", is_flag=True)
def check(path, quiet):
    """
    Locally validate config files
    """

    errors = {}

    configs = ConfigModels(root={})

    for root, _, files in os.walk(path):
        for f in files:
            if f.startswith(CONFIG_FILENAME_PREFIX):
                config_path = Path(root) / f

                if not quiet:
                    click.echo(config_path, nl=False)
                try:
                    configs.add_config(
                        ConfigModel.from_filesystem(config_path), config_path
                    )

                    if not quiet:
                        click.secho(" -> OK", fg="green")
                except ValidationError as e:
                    if not quiet:
                        click.secho(" -> ERROR", fg="red")

                    errors[config_path] = e

    for path, error in errors.items():
        click.secho(str(path), fg="red")
        print(error)

    if errors:
        sys.exit(1)

    return configs


@cli.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--changed", is_flag=True)
@click.option("--json", "as_json", is_flag=True)
@click.option("--by", type=click.Choice(["scope", "path"]), default="path")
@click.pass_context
def ls(ctx, path, changed, as_json, by):
    """
    List files and lines that match scopes
    """
    configs = ctx.invoke(check, path=path, quiet=True)

    if changed:
        iterator = git.git_ls_changes(path)
    else:
        iterator = git.git_ls_files(path)

    results = match_files(configs, iterator)
    if as_json:
        click.echo(results.model_dump_json(indent=2))
    else:
        results.print(by=by)


@cli.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--json", "as_json", is_flag=True)
@click.option("--staged", is_flag=True)
@click.option("--by", type=click.Choice(["scope", "path"]), default="path")
@click.pass_context
def diff(ctx, path, as_json, staged, by):
    configs = ctx.invoke(check, path=path, quiet=True)

    diff_args = []
    if staged:
        diff_args.append("--staged")

    diff_stream = git.git_diff_stream(path, *diff_args)

    results, _ = match_diff(configs, diff_stream)
    if as_json:
        click.echo(results.model_dump_json(indent=2))
    else:
        results.print(by=by)


# @cli.command()
# @click.option("--check", is_flag=True)
# @click.argument("path", type=click.Path(exists=True), default=".")
# def coverage(path, check):
#     config = load_root_config()
#     num_matched = 0
#     num_total = 0

#     for f in git.git_ls_files(path):
#         file_path = Path(f)
#         matched = False

#         # TODO doesn't include line patterns...

#         for scope in config.config.scopes:
#             if scope.matches_path(file_path):
#                 matched = True
#                 break

#         if matched:
#             num_matched += 1
#         num_total += 1

#     percentage = f"{num_matched / num_total:.1%}"
#     click.echo(f"{num_matched}/{num_total} files covered ({percentage})")

#     if check and num_matched != num_total:
#         sys.exit(1)


# list - find open PRs, find status url and send json request (needs PA token)
