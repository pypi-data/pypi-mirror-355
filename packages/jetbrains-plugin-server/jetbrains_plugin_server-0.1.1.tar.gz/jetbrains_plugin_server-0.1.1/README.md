<!--

THIS README FILE IS RENDERED ON '/' ENDPOINT WHEN NO "build" ARG IS GIVEN

-->

Creates a jetbrains-compatible plugin server with a given list of plugins

## How-to use

- use the script `dl_data.py` to fetch plugins metadata and data from jetbrains server
- (optional) upload these data to an artifactory
- use the script `gen_json_cache.py` to generate a JSON file that contains all the metadata together
- start the server
- register your server [in your IDE][jb-custom-repo]

## Tools

- `jetbrains_plugin_server/tools/dl_data.py` to fetch plugins specifications, versions and content from jetbrains to a
  local filesystem
- `jetbrains_plugin_server/tools/gen_json_cache.py` to build a JSON cache to answer faster, using either a filesystem
  storage or an
  artifactory

## Paths

- `/` to get the readme OR the compliant xml content if url param `build` is provided
- `/cache` to get the full JSON cache of the server
- `/packages` to get a nicer view of the available packages
- `/docs` the openapi spec of the app, provided by FastAPI

[jb-custom-repo]: https://www.jetbrains.com/help/idea/managing-plugins.html#add_plugin_repos
