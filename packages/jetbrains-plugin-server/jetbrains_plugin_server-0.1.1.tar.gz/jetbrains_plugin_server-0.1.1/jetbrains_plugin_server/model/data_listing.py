from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import requests


class DataListing(ABC):
    @abstractmethod
    def list(self, directory) -> list[str]:
        raise NotImplementedError()

    @abstractmethod
    def get(self, directory, file) -> Any:
        raise NotImplementedError()


class FSDataListing(DataListing):

    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)

    def list(self, directory) -> list[str]:
        return [
            p.name
            for p in self.base_path.joinpath(directory).glob("*")
        ]

    def get(self, directory, file) -> Any:
        return self.base_path.joinpath(directory, file).read_text(encoding="utf8")


class ArtifactoryDataListing(DataListing):

    def __init__(self, base_url: str, repo_name: str):
        self.base_url = base_url.strip("/")
        self.repo_name = repo_name.strip("/")

    def list(self, directory) -> list[str]:
        url = f"{self.base_url}/artifactory/api/storage/{self.repo_name}/{directory}"
        files_rep = requests.get(url)
        files = files_rep.json()
        return [
            Path(file["uri"]).name
            for file in files["children"]
        ]

    def get(self, directory, file) -> Any:
        url = f"{self.base_url}/artifactory/{self.repo_name}/{directory}/{file}"
        return requests.get(url).text
