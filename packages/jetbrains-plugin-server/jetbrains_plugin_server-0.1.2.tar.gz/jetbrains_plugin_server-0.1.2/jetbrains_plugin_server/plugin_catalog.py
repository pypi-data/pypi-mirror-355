import json
import logging
from functools import lru_cache

from jetbrains_plugin_server.config import IS_TEST_MODE, PLUGIN_PROD_DATA, PLUGIN_TEST_DATA
from jetbrains_plugin_server.schemas import CatalogSchema

LOG = logging.getLogger(__name__)


@lru_cache()
def get_plugin_catalog() -> CatalogSchema:
    LOG.info("load catalog from file")
    if IS_TEST_MODE:
        catalog_path = PLUGIN_TEST_DATA
    else:
        catalog_path = PLUGIN_PROD_DATA
    return CatalogSchema.model_validate(json.loads(catalog_path.read_text()))
