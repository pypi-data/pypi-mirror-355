"""
A quest is a distributed scraping journey :)
A sciop instance contains a list of dataset parts to scrape,
a crawler will get a series of unclaimed parts,
crawl them, and upload the resulting torrents!
"""

import json
import warnings
from pathlib import Path
from typing import Any, ClassVar, Literal, Self

from pydantic import BaseModel, Field
from scrapy import Spider
from scrapy.crawler import CrawlerProcess


class Quest(BaseModel):
    """
    A scrape journey to go on with your friends
    """

    name: ClassVar[str]
    """
    Name that will be used when calling from the CLI.
    Each quest needs an (instance) unique name
    """
    dataset_slug: ClassVar[str]
    """
    Dataset slug on the sciop instance that this quest belongs to.
    
    Usually the same as `name`, but allowed to differ e.g.
    in the case of multiple quests for the same dataset.
    """
    spider: ClassVar[type[Spider] | None] = None
    """
    Scrapy spider to use, if any
    """

    output: Path
    """
    Output directory to write to.
    
    The output directory stores data for *all* quests and subquests.
    
    Quests should ensure that their scraper outputs data in a structure like..
    
    ```
    output
    |- quest_status.json
    |- quest_1
    |  |- subquest_1
    |  |  |- (data)
    |  |  ...
    |  |- subquest_1
    |  ...
    |- quest_2
    ...
    ```
    """
    subquest: str
    """
    The currently active subquest.
    """

    def run(self, scrape_kwargs: dict | None = None) -> "QuestStatus":
        if scrape_kwargs is None:
            scrape_kwargs = {}

        status = self.init_status()
        try:
            if status.status == "scraping":
                status, scrape_kwargs = self.before_scrape(status, **scrape_kwargs)
                status = self.scrape(status, **scrape_kwargs)
                status = self.after_scrape(status)
                status.status = "validating"
            if status.status == "validating":
                status = self.before_validate(status)
                status = self.validate_scrape(status)
                status = self.after_validate(status)
                status.status = "packing"
            if status.status == "packing":
                status = self.before_pack(status)
                status = self.pack(status)
                status = self.after_pack(status)
                status.status = "complete"
            if status.result is None:
                # status would otherwise be set to validation_error in validate_scrape
                status.result = "success"
        finally:
            self.update_log(status)

        return status

    def init_status(self) -> "QuestStatus":
        """
        Load any intermediate result from the quest log,
        or create a new one if none found.

        If we have previously attempted a subquest and ended with a validation error,
        retry from the scraping stage.
        """
        status = None
        if self.log_path.exists():
            log = QuestLog.from_json(self.log_path)
            status = log.get_subquest(self.name, self.subquest)

        if status is None:
            status = QuestStatus(
                quest=self.name,
                subquest=self.subquest,
                path=self.subquest_path,
            )
        else:
            # if we have previously completed with a validation error and are running again,
            # return to scraping state.
            if status.status == "complete" and status.result == "validation_error":
                status.status = "scraping"

        return status

    @property
    def log_path(self) -> Path:
        return self.output / "quest-log.json"

    @property
    def subquest_path(self) -> Path:
        return self.output / self.name / self.subquest

    def update_log(self, res: "QuestStatus") -> None:
        """
        Update the log, replacing the
        :param res:
        :return:
        """
        log = QuestLog.from_json(self.log_path)
        log = log.update(res)
        log.to_json(self.log_path)

    def scrape(self, res: "QuestStatus", **kwargs: Any) -> "QuestStatus":
        """
        Run the spider - default is to use the scrapy spider
        """
        return self._scrape_with_spider(res, **kwargs)

    def validate_scrape(self, res: "QuestStatus") -> "QuestStatus":
        """
        After scraping, subclasses may override to perform validation.

        Default is no-op
        """
        return res

    def pack(self, res: "QuestStatus") -> "QuestStatus":
        """
        After validating, subclasses may override to perform packing.

        Default is no-op
        """
        return res

    def before_scrape(self, res: "QuestStatus", **kwargs: any) -> tuple["QuestStatus", dict]:
        """Hook method called before scraping"""
        return res, kwargs

    def after_scrape(self, res: "QuestStatus") -> "QuestStatus":
        """Hook method called after scraping"""
        return res

    def before_validate(self, res: "QuestStatus") -> "QuestStatus":
        """Hook method called before validation"""
        return res

    def after_validate(self, res: "QuestStatus") -> "QuestStatus":
        """Hook method called after validation"""
        return res

    def before_pack(self, res: "QuestStatus") -> "QuestStatus":
        """Hook method called before packing"""
        return res

    def after_pack(self, res: "QuestStatus") -> "QuestStatus":
        """Hook method called after packing"""
        return res

    def _scrape_with_spider(self, res: "QuestStatus", **kwargs: Any) -> None:
        if self.spider is None:
            raise RuntimeError("No spider has been declared, but attempted to scrape with spider")

        process = CrawlerProcess()
        process.crawl(self.spider, **kwargs)
        process.start()
        return res


class QuestStatus(BaseModel):
    quest: str
    subquest: str
    path: Path
    """Directory where the data was scraped to"""
    scrape_errors: list["ScrapeError"] = Field(default_factory=list)
    validation_errors: list["ValidationError"] = Field(default_factory=list)
    status: Literal["scraping", "validating", "packing", "complete"] = "scraping"
    result: None | Literal["success", "validation_error"] = None


class QuestLog(BaseModel):
    subquests: list[QuestStatus] = Field(default_factory=list)

    def get_subquest(self, quest: str, subquest: str) -> QuestStatus | None:
        matches = [q for q in self.subquests if q.quest == quest and q.subquest == subquest]
        if len(matches) > 1:
            raise KeyError(f"More than one match found for quest {quest}, subquest {subquest}")
        elif len(matches) == 1:
            return matches[0]
        else:
            return None

    def update(self, res: "QuestStatus") -> Self:
        """
        Add new entry to log, replacing any previous matches
        """
        items = [q for q in self.subquests if q.quest != res.quest or q.subquest != res.subquest]
        existing = [
            q for q in self.subquests if q.quest == res.quest and q.subquest == res.subquest
        ]
        if existing:
            res = self.merge_errors(res, existing[0])
        items.append(res)
        self.subquests = items
        return self

    def merge_errors(self, res: "QuestStatus", existing: "QuestStatus") -> "QuestStatus":
        """
        Merge errors from the previous status, updating the n_errors in each.
        """
        old_scrape_map = {e.url: e for e in existing.scrape_errors}
        old_validation_map = {e.path: e for e in existing.validation_errors}

        for e in res.scrape_errors:
            if e.url in old_scrape_map:
                e.n_failures = old_scrape_map[e.url].n_failures + 1
        for e in res.validation_errors:
            if e.path in old_validation_map:
                e.n_failures = old_validation_map[e.path].n_failures + 1
        return res

    @classmethod
    def from_json(cls, path: Path) -> "QuestLog":
        if not path.exists():
            return QuestLog()

        try:
            with open(path) as f:
                log = json.load(f)
        except json.decoder.JSONDecodeError:
            warnings.warn(
                f"Quest log could not be read from {str(path)}, ignoring, will overwrite",
                stacklevel=2,
            )
            log = []
        return QuestLog(subquests=log)

    def to_json(self, path: Path) -> None:
        items = self.model_dump(by_alias=True)["subquests"]
        with open(path, "w") as f:
            json.dump(items, f, indent=2, default=str)


class ScrapeError(BaseModel):
    url: str
    type_: str = Field(..., alias="type")
    msg: str
    n_failures: int = 1


class ValidationError(BaseModel):
    path: Path
    type_: str = Field(..., alias="type")
    msg: str
    n_failures: int = 1
