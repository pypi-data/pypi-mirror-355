import logging

import uvicorn
from fastapi import FastAPI

from extratools_api.crudl import add_crudl_endpoints_for_mapping

app = FastAPI(debug=True)

data_store = {}

add_crudl_endpoints_for_mapping(
    app,
    "/admin/item",
    data_store,
    values_in_list=True,
)

add_crudl_endpoints_for_mapping(
    app,
    "/readonly/item",
    data_store,
    readonly=True,
)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level=logging.DEBUG,
    )
