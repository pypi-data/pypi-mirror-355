from pathlib import Path

import click

from sciop_scraping.cli.common import spider_options
from sciop_scraping.quests.chronicling import ChroniclingAmericaQuest


@click.command("chronicling-america")
@click.option("-b", "--batch", help="Which batch to crawl. If None, crawl everything", default=None)
@click.option(
    "-o",
    "--output",
    help="Output directory to save files in. "
    "If None, $PWD/data/chronicling-america. "
    "Data will be saved in a chronicling-america subdirectory, "
    "and the crawl state will be saved in crawl_state.",
    default=None,
    type=click.Path(),
)
@click.option(
    "-c",
    "--cloudflare-cookie",
    help="When you get rate limited, you need to go solve a cloudflare challenge, "
    "grab the cookie with the key 'cf_clearance' and pass it here",
    default=None,
)
@click.option(
    "-u",
    "--user-agent",
    help="When you get rate limited, the cookie is tied to a specific user agent, "
    "copy paste that and pass it here",
    default=None,
)
@click.option(
    "--crawl-state",
    help="Use scrapy crawl state. Defaults False, "
    "because we can resume crawling using the manifest.",
    default=False,
    is_flag=True,
)
@spider_options
def chronicling_america(
    batch: str | None,
    output: Path | None = None,
    cloudflare_cookie: str | None = None,
    user_agent: str | None = None,
    crawl_state: bool = False,
    retries: int = 100,
    timeout: float = 20,
) -> None:
    """
    Scrape the Chronicling America dataset from the Library of Congress in batches

    https://chroniclingamerica.loc.gov/data/batches/

    If you get a 429 redirect, you will need to manually bypass the cloudflare ratelimit check.

    - Open https://chroniclingamerica.loc.gov/data/batches/ in a browser,
    - Pass the cloudflare check
    - Open your developer tools (often right click + inspect element)
    - Open the networking tab to watch network requests
    - Reload the page
    - Click on the request made to the page you're on to see the request headers
    - Copy your user agent and the part of the cookie after `cf_clearance=`
      and pass them to the -u and -c cli options, respectively.
    """
    if output is None:
        output = Path.cwd() / "data"

    job_dir = None
    if crawl_state:
        job_dir = output / "crawl_state" / batch
        job_dir.mkdir(exist_ok=True, parents=True)

    quest = ChroniclingAmericaQuest(subquest=batch, output=output)
    quest.run(
        scrape_kwargs={
            "job_dir": job_dir,
            "user_agent": user_agent,
            "batch": batch,
            "cf_cookie": cloudflare_cookie,
            "retries": retries,
            "download_timeout": timeout,
        }
    )
