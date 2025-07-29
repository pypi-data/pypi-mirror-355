from pydantic_extra_types.semantic_version import SemanticVersion

from jetbrains_plugin_server.plugin_catalog import get_plugin_catalog
from jetbrains_plugin_server.schemas import LowPaddingSemanticVersion, PluginVersionSchema


def get_plugins(build: str) -> list[tuple[str, PluginVersionSchema]]:
    catalog = get_plugin_catalog()
    build_version = LowPaddingSemanticVersion.parse(build)
    return [
        (plugin.name, version_found)
        for plugin in catalog.plugins
        if (version_found := get_latest_compatible(build_version, plugin.versions))
    ]


def get_latest_compatible(
        build_version: SemanticVersion,
        plugin_versions: list[PluginVersionSchema]
):
    for plugin_version in plugin_versions:
        if is_compatible(build_version, plugin_version):
            return plugin_version

    return None


def is_compatible(
        build_version: SemanticVersion,
        plugin_version: PluginVersionSchema
) -> bool:
    since, until = plugin_version.specs.since_build_semver, plugin_version.specs.until_build_semver
    if until:
        return since <= build_version <= until
    return since <= build_version
