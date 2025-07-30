#  Copyright © 2025 China Mobile (SuZhou) Software Technology Co.,Ltd
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import logging
import os
from typing import List, Literal, Optional

import click
import typer

from ecl_mcp_server import constants, context

cli = typer.Typer()

_Transport_Type = Literal["stdio", "sse", "streamable-http"]


def setup_logging(level):
    handlers: list[logging.Handler] = []
    try:
        from rich.console import Console
        from rich.logging import RichHandler

        handlers.append(RichHandler(console=Console(stderr=True), rich_tracebacks=True))
    except ImportError:
        pass

    if not handlers:
        handlers.append(logging.StreamHandler())
    handlers.append(logging.FileHandler("ecl_mcp_server.log"))

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
        handlers=handlers,
    )


def _validate_module(value: List[str]) -> List[str]:
    modules = set(value)
    if "all" in modules and len(modules) > 1:
        click.echo(
            "Warning: DO NOT NEED supply other modules if 'all' provided",
            err=True,
            color=True,
            nl=True,
        )
    return value


def _set_timezone(timezone_param: Optional[str]):
    from datetime import timedelta, timezone

    import pytz

    if timezone_param is None:
        return timezone(timedelta(hours=8))

    try:
        offset = float(timezone_param)
    except Exception as e:
        _ = e
        try:
            return pytz.timezone(timezone_param)
        except Exception as e:
            raise ValueError(f"Unknown timezone: {timezone_param}") from e
    try:
        return timezone(timedelta(hours=offset))
    except Exception as e:
        raise ValueError(f"Unknown offset: {timezone_param}") from e


@cli.command()
def _mcp_server(
        access_key: str = typer.Argument(
            ...,
            envvar=constants.ENV_JOURNAL_AK_KEY,
            help='The AccessKey required for the China Mobile Cloud API gateway. '
                 'For more information: https://ecloud.10086.cn/op-help-center/doc/article/42472 '
                f'You can set the environment variable {constants.ENV_JOURNAL_AK_KEY} '
                 'instead of manually entering this parameter.',
        ),
        secret_key: str = typer.Argument(
            ...,
            envvar=constants.ENV_JOURNAL_SK_KEY,
            help='The SecretKey required for the China Mobile Cloud API gateway. '
                 'For more information: https://ecloud.10086.cn/op-help-center/doc/article/42472 '
                f'You can set the environment variable {constants.ENV_JOURNAL_SK_KEY} '
                 'instead of manually entering this parameter.',
        ),
        port: int = typer.Option(8000, help="Server listening port"),
        transport: _Transport_Type = typer.Option(
            "stdio",
            help='Transport protocol to use ("stdio", "sse", or "streamable-http")',
            click_type=click.Choice(["stdio", "sse", "streamable-http"]),
        ),
        log_level: Optional[str] = typer.Option(
            "INFO",
            help="Logging level",
            click_type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
        ),
        preferred_pool_id: Optional[str] = typer.Option(
            None,
            envvar=constants.ENV_JOURNAL_PREFERRED_POOL_ID,
            help="The default resource pool id used when accessing ecl-mcp-server. "
                 "Some requests require a clear specification of the resource pool id, "
                 "otherwise it will be requested to be specified in the conversation.",
        ),
        module: List[str] = typer.Option(
            ["default"],
            "--module",
            "-m",
            help="What tools should be loaded. "
                 "After specifying the module, only partial tool information is loaded to ecl-mcp-server. "
                 "This parameter can be entered multiple times to load multiple modules: -m default -m alarm",
            callback=_validate_module,
            click_type=click.Choice(constants.MODULES),
        ),
        timezone: Optional[str] = typer.Option(
            '8', "--timezone", "-tz",
            help="Configure time zone. It can be a float number that represents an offset (such as 8 or -5.5) "
                 "or a time zone name (such as Asia/Shanghai)"
        ),
):
    """ecl mcp server command"""
    from ecl_mcp_server import core

    setup_logging(log_level)

    os.environ[constants.ENV_JOURNAL_AK_KEY] = access_key
    os.environ[constants.ENV_JOURNAL_SK_KEY] = secret_key
    context.preferredPoolId = preferred_pool_id

    # Configure timezone
    context.tz = _set_timezone(timezone)

    mcp = core.Module().load(module)
    mcp.settings.port = port
    mcp.settings.debug = True
    mcp.settings.log_level = log_level

    logging.debug("mcp.settings: %s", mcp.settings)

    mcp.run(transport=transport)


def main():  # pragma: no cover
    """Main entry point for ecl-mcp-server"""
    cli()
