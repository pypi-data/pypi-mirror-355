import re
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator
from pydantic_extra_types.semantic_version import SemanticVersion


class LowPaddingSemanticVersion:
    @staticmethod
    def parse(version: str) -> SemanticVersion:
        return SemanticVersion.parse(normalize_version(version, "start"))


class HighPaddingSemanticVersion:
    @staticmethod
    def parse(version: str) -> SemanticVersion:
        return SemanticVersion.parse(normalize_version(version, "end"))


def normalize_version(value: str, mode: Literal["start", "end"]):
    if match := re.match(r"^[A-Z]+-(.+)$", value):
        value = match.group(1)
    replacer = "0" if mode == "start" else "999999"
    result = value.replace(".*", f".{replacer}")
    while result.count(".") < 2:
        result += f".{replacer}"
    return result


class PluginVersionSpecSchema(BaseModel):
    since_build: str = Field(alias="since-build")
    until_build: str | None = Field(alias="until-build", default=None)

    since_build_semver: SemanticVersion = Field(alias="since-build-semver")
    until_build_semver: SemanticVersion | None = Field(alias="until-build-semver", default=None)

    @model_validator(mode='before')
    @classmethod
    def set_semver_fields(cls, data: Any) -> Any:
        data["since-build-semver"] = LowPaddingSemanticVersion.parse(data["since-build"])
        if ub := data.get("until-build"):
            data["until-build-semver"] = HighPaddingSemanticVersion.parse(ub)
        return data


class PluginVersionSchema(BaseModel):
    plugin_id: str
    plugin_version_id: int
    description: str | None
    change_notes: str | None
    version: str
    specs: PluginVersionSpecSchema


class PluginSchema(BaseModel):
    name: str
    versions: list[PluginVersionSchema]


class CatalogSchema(BaseModel):
    plugins: list[PluginSchema] = Field(default_factory=list)
