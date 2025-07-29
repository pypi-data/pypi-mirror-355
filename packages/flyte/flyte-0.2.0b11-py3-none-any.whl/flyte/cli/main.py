import rich_click as click

from flyte._logging import initialize_logger, logger

from ._abort import abort
from ._common import CLIConfig
from ._create import create
from ._deploy import deploy
from ._gen import gen
from ._get import get
from ._run import run

click.rich_click.COMMAND_GROUPS = {
    "flyte": [
        {
            "name": "Running workflows",
            "commands": ["run", "abort"],
        },
        {
            "name": "Management",
            "commands": ["create", "deploy", "get"],
        },
        {
            "name": "Documentation generation",
            "commands": ["gen"],
        },
    ]
}

help_config = click.RichHelpConfiguration(
    use_markdown=True,
    use_markdown_emoji=True,
)


def _verbosity_to_loglevel(verbosity: int) -> int | None:
    """
    Converts a verbosity level from the CLI to a logging level.

    :param verbosity: verbosity level from the CLI
    :return: logging level
    """
    import logging

    match verbosity:
        case 0:
            return None
        case 1:
            return logging.WARNING
        case 2:
            return logging.INFO
        case _:
            return logging.DEBUG


@click.group(cls=click.RichGroup)
@click.option(
    "--endpoint",
    type=str,
    required=False,
    help="The endpoint to connect to. This will override any configuration file and simply use `pkce` to connect.",
)
@click.option(
    "--insecure",
    is_flag=True,
    required=False,
    help="Use an insecure connection to the endpoint. If not specified, the CLI will use TLS.",
    type=bool,
    default=None,
    show_default=True,
)
@click.option(
    "-v",
    "--verbose",
    required=False,
    help="Show verbose messages and exception traces. Repeating multiple times increases the verbosity (e.g., -vvv).",
    count=True,
    default=0,
    type=int,
)
@click.option(
    "--org",
    type=str,
    required=False,
    help="The organization to which the command applies.",
)
@click.option(
    "-c",
    "--config",
    "config_file",
    required=False,
    type=click.Path(exists=True),
    help="Path to the configuration file to use. If not specified, the default configuration file is used.",
)
@click.rich_config(help_config=help_config)
@click.pass_context
def main(
    ctx: click.Context,
    endpoint: str | None,
    insecure: bool,
    verbose: int,
    org: str | None,
    config_file: str | None,
):
    """
    The Flyte CLI is the the command line interface for working with the Flyte SDK and backend.

    It follows a simple verb/noun structure,
    where the top-level commands are verbs that describe the action to be taken,
    and the subcommands are nouns that describe the object of the action.

    The root command can be used to configure the CLI for persistent settings,
    such as the endpoint, organization, and verbosity level.

    Set endpoint and organization:

    ```bash
    $ flyte --endpoint <endpoint> --org <org> get project <project_name>
    ```

    Increase verbosity level (This is useful for debugging,
    this will show more logs and exception traces):

    ```bash
    $ flyte -vvv get logs <run-name>
    ```

    Override the default config file:

    ```bash
    $ flyte --config /path/to/config.yaml run ...
    ```

    * [Documentation](https://www.union.ai/docs/flyte/user-guide/)
    * [GitHub](https://github.com/flyteorg/flyte): Please leave a star if you like Flyte!
    * [Slack](https://slack.flyte.org): Join the community and ask questions.
    * [Issues](https://github.com/flyteorg/flyte/issues)

    """
    import flyte.config as config

    log_level = _verbosity_to_loglevel(verbose)
    if log_level is not None:
        initialize_logger(log_level)

    cfg = config.auto(config_file=config_file)
    logger.debug(f"Using config file discovered at location {cfg.source}")

    ctx.obj = CLIConfig(
        log_level=log_level,
        endpoint=endpoint,
        insecure=insecure,
        org=org,
        config=cfg,
        ctx=ctx,
    )
    logger.debug(f"Final materialized Cli config: {ctx.obj}")


main.add_command(run)
main.add_command(deploy)
main.add_command(get)  # type: ignore
main.add_command(create)  # type: ignore
main.add_command(abort)  # type: ignore
main.add_command(gen)  # type: ignore
