import json
from collections.abc import Awaitable, Callable, Iterable, Mapping, MutableMapping
from http import HTTPStatus
from typing import Annotated, Any, cast

from extratools_core.crudl import CRUDLWrapper, RLWrapper
from extratools_core.json import JsonDict
from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, ValidationError


def add_crudl_endpoints[KT: str, VT: JsonDict | BaseModel](
    app: FastAPI,
    path_prefix: str,
    *,
    create_func: Callable[[KT, JsonDict], Awaitable[VT | None]] | None = None,
    read_func: Callable[[KT], Awaitable[VT]] | None = None,
    update_func: Callable[[KT, JsonDict], Awaitable[VT | None]] | None = None,
    delete_func: Callable[[KT], Awaitable[VT | None]] | None = None,
    list_func: Callable[[JsonDict | None], Awaitable[Iterable[tuple[KT, Any]]]] | None = None,
) -> None:
    path_prefix = path_prefix.rstrip("/")

    if create_func:
        @app.put(path_prefix + "/{identifier}")
        async def create_endpoint(
            identifier: KT,
            put_body: Annotated[JsonDict, Body()],
        ) -> VT | None:
            return await create_func(
                identifier,
                put_body,
            )

    if read_func:
        @app.get(path_prefix + "/{identifier}")
        async def read_endpoint(identifier: KT) -> VT:
            return await read_func(
                identifier,
            )

    if update_func:
        @app.patch(path_prefix + "/{identifier}")
        async def update_endpoint(
            identifier: KT,
            patch_body: Annotated[JsonDict, Body()],
        ) -> VT | None:
            return await update_func(
                identifier,
                patch_body,
            )

    if delete_func:
        @app.delete(path_prefix + "/{identifier}")
        async def delete_endpoint(identifier: KT) -> VT | None:
            return await delete_func(identifier)

    if list_func:
        @app.get(path_prefix + "/")
        async def list_endpoint(filter_body: str | None = None) -> dict[KT, Any]:
            try:
                return dict(await list_func(
                    json.loads(filter_body) if filter_body
                    else None,
                ))
            except json.JSONDecodeError as e:
                raise HTTPException(HTTPStatus.BAD_REQUEST) from e


class FilterKeys(BaseModel):
    model_config = ConfigDict(extra="forbid")

    includes: list[str] | None = None
    excludes: list[str] | None = None


def add_crudl_endpoints_for_mapping[KT: str, VT: JsonDict](
    app: FastAPI,
    path_prefix: str,
    mapping: Mapping[KT, VT],
    *,
    values_in_list: bool = False,
    readonly: bool | None = None,
) -> None:
    mutable: bool = isinstance(mapping, MutableMapping)
    if readonly is None:
        readonly = not mutable

    async def read_func(key: KT) -> VT:
        try:
            return crudl_store.read(key)
        except KeyError as e:
            raise HTTPException(HTTPStatus.NOT_FOUND) from e

    async def list_func(filter_keys: JsonDict | None) -> Iterable[tuple[KT, VT | None]]:
        try:
            filter_keys_model: FilterKeys | None = (
                FilterKeys.model_validate(filter_keys, strict=True) if filter_keys
                else None
            )
        except ValidationError as e:
            raise HTTPException(HTTPStatus.BAD_REQUEST) from e

        return crudl_store.list(
            None if filter_keys_model is None
            else lambda key: (
                (filter_keys_model.includes is None or key in (filter_keys_model.includes))
                and key not in (filter_keys_model.excludes or [])
            ),
        )

    if mutable and not readonly:
        crudl_store = CRUDLWrapper[KT, VT](
            mapping,
            values_in_list=values_in_list,
        )

        async def create_func(key: KT, value: JsonDict) -> None:
            try:
                crudl_store.create(key, cast("VT", value))
            except KeyError as e:
                raise HTTPException(HTTPStatus.CONFLICT) from e

        async def update_func(key: KT, value: JsonDict) -> None:
            try:
                crudl_store.update(key, cast("VT", value))
            except KeyError as e:
                raise HTTPException(HTTPStatus.NOT_FOUND) from e

        async def delete_func(key: KT) -> None:
            try:
                crudl_store.delete(key)
            except KeyError as e:
                raise HTTPException(HTTPStatus.NOT_FOUND) from e

        add_crudl_endpoints(
            app,
            path_prefix,
            read_func=read_func,
            list_func=list_func,
            create_func=create_func,
            update_func=update_func,
            delete_func=delete_func,
        )
    else:
        crudl_store = RLWrapper[KT, VT](
            mapping,
            values_in_list=values_in_list,
        )

        add_crudl_endpoints(
            app,
            path_prefix,
            read_func=read_func,
            list_func=list_func,
        )
