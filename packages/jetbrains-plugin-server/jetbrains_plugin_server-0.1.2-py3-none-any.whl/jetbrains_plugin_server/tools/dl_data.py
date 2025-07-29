import sys

from requests import Session, get
from requests.adapters import HTTPAdapter, Retry

from jetbrains_plugin_server.config import JETBRAINS_PLUGINS_HOST, LOCAL, PLUGIN_SPECS_DIR, PLUGIN_VERSIONS_DIR, PLUGINS_DIR


def dl_data(plugins: list[str]):
    """
    The argument values can be either:
     - plugins IDs: "631" (for python)
     - plugin id+name: "631-python"
     - plugin full url: "https://plugins.jetbrains.com/plugin/631-python",
    """
    s = Session()
    retries = Retry(total=5, backoff_factor=0.1)
    s.mount('https://', HTTPAdapter(max_retries=retries))

    for plugin in plugins:
        print("PLUGIN", plugin)
        plugin = plugin.replace(f"{JETBRAINS_PLUGINS_HOST}/plugin/", "").strip("/")
        plugin_id_int = plugin.split("-", maxsplit=1)[0]

        versions_rep = get(f"{JETBRAINS_PLUGINS_HOST}/plugins/list?pluginId={plugin}")
        LOCAL.joinpath(PLUGIN_SPECS_DIR, f"{plugin_id_int}.xml").write_bytes(
            versions_rep.content
        )

        versions_id_rep = get(f"{JETBRAINS_PLUGINS_HOST}/api/plugins/{plugin_id_int}/updateVersions")
        LOCAL.joinpath(PLUGIN_VERSIONS_DIR, f"{plugin_id_int}.json").write_bytes(
            versions_id_rep.content
        )

        for row in versions_id_rep.json()[:-50:-1]:
            print(f"   VERSION {row['version']:20s}", end="")
            sys.stdout.flush()
            plugin_version_id = row["id"]
            zip_file = LOCAL.joinpath(PLUGINS_DIR, f"{plugin_version_id}.zip")
            if zip_file.exists():
                print("   already done", plugin_version_id)
                continue

            dl = s.get(
                f"{JETBRAINS_PLUGINS_HOST}/plugin/download",
                params={"updateId": plugin_version_id},
                stream=True
            )
            zip_file.write_bytes(dl.content)
            print("   done in", dl.elapsed, plugin_version_id)
