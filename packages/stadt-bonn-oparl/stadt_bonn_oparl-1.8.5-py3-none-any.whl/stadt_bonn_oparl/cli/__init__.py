#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "cyclopts",
#   "logfire",
# ]
# ///

"""
Main entry point and setup for the CLI application.

This module initializes the cyclopts application, configures logging based on
verbosity flags, defines global CLI options, and registers all command groups
from the cli subpackages.
"""


from typing import Annotated

import cyclopts
import logfire

from stadt_bonn_oparl import __version__
from stadt_bonn_oparl.cli import meeting
from stadt_bonn_oparl.logging import configure_logging

from ..papers.classifier import analyse_paper
from .check_references import checker
from .consultation import consultation
from .convert import convert
from .download import download
from .enrich import enrich
from .extract import extract
from .filter import filter_fields
from .find import find
from .meeting import meeting
from .research import research_stakeholders, research_topic
from .vectordb import vectordb


app = cyclopts.App(
    help="Stadt Bonn OPARL Papers CLI",
    version=__version__,
    name="oparl-cli",
    config=cyclopts.config.Env(
        "OPARL_",  # Every environment variable will begin with this.
    ),
    default_parameter=cyclopts.Parameter(negative=()),
)


# https://github.com/BrianPugh/cyclopts/issues/212
app.meta.group_parameters = cyclopts.Group("Global Parameters", sort_key=0)


@app.meta.default
def app_launcher(
    *tokens: Annotated[str, cyclopts.Parameter(show=False, allow_leading_hyphen=True)],
    very_verbose: Annotated[
        list[bool],
        cyclopts.Parameter(
            name=["--very-verbose", "-vv"],
            required=False,
            show_default=False,
            help="Increase verbosity level.",
        ),
    ] = [],
    verbose: Annotated[
        list[bool],
        cyclopts.Parameter(
            name=["--verbose", "-v"],
            required=False,
            show_default=False,
            help="Increase verbosity level.",
        ),
    ] = [],
    enable_logfire: Annotated[
        bool,
        cyclopts.Parameter(
            name=["logfire", "-l"],
            required=False,
            help="Enable logging to Pydantic's logfire.",
        ),
    ] = False,
):
    """
    Default entry point for handling global options and configuring the application.

    This function is decorated with @app.default and processes global flags
    like verbosity before any subcommand is executed. It configures logging
    based on the verbosity flags.

    Subcommands are registered after this function definition.

    Args:
        verbose: A list of boolean flags indicating verbosity levels.
    """
    # Calculate verbosity level
    verbosity = sum(verbose)
    if very_verbose:
        verbosity = 2
    configure_logging(verbosity)

    if enable_logfire:
        from dotenv import load_dotenv

        load_dotenv()

        logfire.configure()
        logfire.instrument_pydantic()
        logfire.instrument_system_metrics()
        logfire.instrument_httpx()  # This is causing HTTP request logs

    app(tokens)


app.meta.command(obj=download, name=["download", "dl"])

app.meta.command(convert)

app.meta.command(analyse_paper, name=["analyse", "classify", "classify-paper"])

app.meta.command(find)

app.meta.command(filter_fields)

app.meta.command(enrich)

app.meta.command(extract)

app.meta.command(research_stakeholders, name=["research-stakeholders", "stakeholders"])
app.meta.command(research_topic, name=["research-topic", "topic"])

app.meta.command(vectordb)

app.meta.command(meeting, name=["meeting", "meetings", "m"])

app.meta.command(consultation, name=["consultation", "c"])

app.meta.command(checker, name=["check", "chk"])
