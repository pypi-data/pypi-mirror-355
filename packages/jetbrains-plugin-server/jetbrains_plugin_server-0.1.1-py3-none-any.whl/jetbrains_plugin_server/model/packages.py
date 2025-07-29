import markdown
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from jetbrains_plugin_server.plugin_catalog import get_plugin_catalog
from jetbrains_plugin_server.schemas import PluginSchema

router = APIRouter(
    prefix="/packages",
)


@router.get("")
def get_packages_route():
    catalog = get_plugin_catalog()
    md = "# Packages\n"
    md += "\n".join(f"- [{p.name}](/packages/{p.versions[0].plugin_id})" for p in catalog.plugins)
    md += "\n\n [Previous page](/)"
    return HTMLResponse(content=markdown.markdown(md))


@router.get("/{plugin_id}")
def get_package_route(plugin_id: str):
    catalog = get_plugin_catalog()
    plugin: PluginSchema = next(p for p in catalog.plugins if p.versions[0].plugin_id == plugin_id)
    md = f"# Package {plugin.name}\n"
    md += "\n".join(
        f"- [{v.version}](/packages/{plugin_id}/{v.version}) "
        f"compatible with IDE version in `[{v.specs.since_build} ; {v.specs.until_build}]`"
        for v in plugin.versions
    )
    md += "\n\n [Previous page](/packages)"
    return HTMLResponse(content=markdown.markdown(md))
