"""
Common options for cli commands
"""

import click


def spider_options(f: click.Command) -> click.Command:
    """Common options that all spider cli commands should support"""
    f = click.option("--retries", type=int, help="Number of retries")(f)
    f = click.option("--timeout", type=int, help="Timeout for spider in seconds")(f)
    return f
