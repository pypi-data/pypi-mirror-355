import json
import logging
import xml.etree.ElementTree as ET
from typing import cast

from jetbrains_plugin_server.config import (IS_TEST_MODE, PLUGIN_PROD_DATA, PLUGIN_SPECS_DIR, PLUGIN_TEST_DATA, PLUGIN_VERSIONS_DIR,
                                            PLUGINS_DIR)
from jetbrains_plugin_server.model.data_listing import DataListing
from jetbrains_plugin_server.schemas import CatalogSchema, PluginSchema, PluginVersionSchema, PluginVersionSpecSchema

LOG = logging.getLogger(__name__)


def gen_json_cache(dl: DataListing, only_available_plugins: bool = True):
    """
    dl = ArtifactoryDataListing("https://...", "jetbrains/plugin-server")
    dl = FSDataListing(LOCAL)

    gen_json_cache(dl)
    """
    LOG.info("build catalog")

    result: CatalogSchema = CatalogSchema()

    available_plugins = [int(p.split(".", maxsplit=1)[0]) for p in dl.list(PLUGINS_DIR)]

    for plugin in dl.list(PLUGIN_SPECS_DIR):
        plugin_id_int = plugin.split(".", maxsplit=1)[0]

        versions_to_plugin_version_id = {
            row["version"]: row["id"]
            for row in json.loads(dl.get(PLUGIN_VERSIONS_DIR, f"{plugin_id_int}.json"))
        }

        plugin_spec = dl.get(PLUGIN_SPECS_DIR, plugin)

        root = ET.fromstring(plugin_spec)

        if not (category := root.find("category")):
            LOG.error("Plugin %s has no category", plugin)
            continue

        versions = category.findall("idea-plugin")

        result.plugins.append(PluginSchema(
            name=versions[0].find("name").text,
            versions=[
                PluginVersionSchema(
                    plugin_id=version.find("id").text,
                    plugin_version_id=versions_to_plugin_version_id[version.find("version").text],
                    version=version.find("version").text or "",
                    specs=PluginVersionSpecSchema(
                        **{cast(str, k): v for k, v in version.find("idea-version").items() if v != "n/a"}
                    ),
                    description=version.find("description").text,
                    change_notes=version.find("change-notes").text,
                )
                for version in versions
                if not only_available_plugins or
                   versions_to_plugin_version_id[version.find("version").text] in available_plugins
            ]
        ))
        LOG.info("Plugin '%s' (%s) found %s versions but only %s had available zip",
                 versions[0].find("name").text, plugin, len(versions), len(result.plugins[-1].versions))

    if IS_TEST_MODE:
        PLUGIN_TEST_DATA.write_text(json.dumps(result.model_dump(mode="json", by_alias=True), indent=4))
    else:
        PLUGIN_PROD_DATA.write_text(json.dumps(result.model_dump(mode="json", by_alias=True), indent=4))
