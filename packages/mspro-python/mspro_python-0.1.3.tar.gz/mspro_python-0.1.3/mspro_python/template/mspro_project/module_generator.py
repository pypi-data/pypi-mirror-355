#!/usr/bin/env python3
"""FastAPI Module Code-Generator
================================
Auto-generate CRUD helpers, Pydantic schemas, and FastAPI routers for your
SQLAlchemy models, **and** patch `app/crud/__init__.py` - *imports only* as well
as `app/schemas/__init__.py` (imports + __all__ + forward-refs).

Usage
-----
# 全量扫描 app.models
python module_generator.py

# 指定 models/agent.py 与 models/user.py
python module_generator.py agent user
"""
from __future__ import annotations

import argparse
import inspect
import pkgutil
import re
import sys
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from types import ModuleType
from typing import Iterable, Type, ForwardRef

from sqlalchemy.orm import DeclarativeMeta, RelationshipProperty
from sqlmodel import SQLModel
from sqlalchemy.orm import configure_mappers
from sqlalchemy.exc import ArgumentError, InvalidRequestError
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy import Integer, String, Boolean, DateTime, Float, JSON, LargeBinary, Text, Enum as SAEnum
from typing import Any, get_origin, get_args, Union, List, Optional

TYPE_MAP = {
    Integer: int, String: str, Text: str,
    LargeBinary: bytes, Boolean: bool,
    DateTime: datetime, Float: float, JSON: dict,
}

MODELS_PACKAGE = "app.models"

CRUD_DIR = Path("app/crud")
SCHEMAS_DIR = Path("app/schemas")
ROUTES_DIR = Path("app/routes")
MODELS_DIR = Path("app/models")

# ------------------------------------------------------------------ #
# TEMPLATES
# ------------------------------------------------------------------ #

CRUD_TEMPLATE = '''
# app/crud/{endpoint}.py
"""
    CRUD helpers for {model_name} (generated).
    Author: Jena
    Date: {current_date}
"""
from typing import List, Optional
from fastapi_pagination import Page
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import {model_name}
from app.schemas import {schema_name}Create, {schema_name}Update, {schema_name}Read, {schema_name}Filter
from app.utils.crud import (
    read_one, list_all, paginate_all,
    create_one, update_one, delete_one
)


async def read_{endpoint}(db: AsyncSession, {pk_name}: int = None, params: Optional[{schema_name}Filter] = None, logic: str = "and") -> Optional[{model_name}]:
    """Return one record or *None*."""
    return await read_one(db, {model_name}, "{pk_name}", {pk_name}, params, logic)


async def option_{endpoint}(db: AsyncSession, params: {schema_name}Filter = None, logic: str = "and") -> List[{model_name}]:
    """Return all record without pagination or *None*."""
    return await list_all(db, {model_name}, params, logic)


async def page_{endpoint}(db: AsyncSession, params: {schema_name}Filter = None, logic: str = "and") -> Page[{model_name}]:
    """Return all record with pagination or *None*."""
    return await paginate_all(db, {model_name}, params, logic)


async def create_{endpoint}(db: AsyncSession, obj_in: {schema_name}Create) -> {model_name}:
    return await create_one(db, {model_name}, obj_in)


async def update_{endpoint}(db: AsyncSession, {pk_name}: int, obj_in: {schema_name}Update) -> Optional[{model_name}]:
    return await update_one(db, {model_name}, {pk_name}, obj_in, "{pk_name}")


async def remove_{endpoint}(db: AsyncSession, {pk_name}: int) -> {model_name} | None:
    return await delete_one(db, {model_name}, {pk_name}, "{pk_name}")
'''

SCHEMAS_TEMPLATE = '''
# app/schemas/{endpoint}.py
"""
    Pydantic schemas for {model_name} (generated).
    Author: Jena
    Date: {current_date}
"""
from datetime import datetime
from typing import Optional, Any, List, Tuple
from pydantic import BaseModel


class {schema_name}Base(BaseModel):
{basic_fields}


class {schema_name}Read({schema_name}Base):
{read_fields}


class {schema_name}Create({schema_name}Base):
    pass


class {schema_name}Update(BaseModel):
{update_fields}

    
class {schema_name}Filter(BaseModel):
{filter_fields}
'''

ROUTE_TEMPLATE = '''
# app/routers/{endpoint}.py
"""
    FastAPI routes for {model_name} (generated).
    Author: Jena
    Date: {current_date}
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from sqlmodel.ext.asyncio.session import AsyncSession

from app.utils.dependencies import get_async_session, get_current_user
from app import crud, schemas
from app.utils.query import as_query

router = APIRouter(
    prefix="/{endpoint}", 
    tags=["{endpoint}"],
    dependencies=[Depends(get_current_user)]
)


@router.get("/", response_model=Page[schemas.{schema_name}Read])
async def page_{endpoint}s(params: schemas.{schema_name}Filter = as_query(schemas.{schema_name}Filter), db: AsyncSession = Depends(get_async_session)):
    return await crud.page_{endpoint}(db, params)


@router.get("/option", response_model=List[schemas.{schema_name}Read])
async def option_{endpoint}s(params: schemas.{schema_name}Filter = as_query(schemas.{schema_name}Filter), db: AsyncSession = Depends(get_async_session)):
    return await crud.option_{endpoint}(db, params)
    
    
@router.get("/{{{pk_name}}}", response_model=schemas.{schema_name}Read)
async def read_{endpoint}({pk_name}: int, db: AsyncSession = Depends(get_async_session)):
    return await crud.read_{endpoint}(db, {pk_name})
    

@router.post("/", response_model=schemas.{schema_name}Read)
async def create_{endpoint}(item_in: schemas.{schema_name}Create, db: AsyncSession = Depends(get_async_session)):
    return await crud.create_{endpoint}(db, item_in)


@router.put("/{{{pk_name}}}", response_model=schemas.{schema_name}Read)
async def update_{endpoint}({pk_name}: int, item_in: schemas.{schema_name}Update, db: AsyncSession = Depends(get_async_session)):
    updated = await crud.update_{endpoint}(db, {pk_name}, item_in)
    if not updated:
        raise HTTPException(status_code=404, detail="{model_name} not found")
    return updated


@router.delete("/{{{pk_name}}}", response_model=schemas.{schema_name}Read)
async def delete_{endpoint}({pk_name}: int, db: AsyncSession = Depends(get_async_session)):
    deleted = await crud.remove_{endpoint}(db, {pk_name})
    if deleted is None:
        raise HTTPException(status_code=404, detail="{model_name} not found")
    return deleted
'''


# ------------------------------------------------------------------ #
# HELPERS
# ------------------------------------------------------------------ #


def walk_model_modules(package: str) -> Iterable[ModuleType]:
    mod = __import__(package, fromlist=["*"])
    yield mod
    for _, name, _ in pkgutil.iter_modules([str(Path(mod.__file__).parent)]):
        yield import_submodule(f"{package}.{name}")


def import_submodule(name: str) -> ModuleType:
    return sys.modules.get(name) or __import__(name, fromlist=["*"])


def is_model_class(obj) -> bool:
    return inspect.isclass(obj) and issubclass(obj, SQLModel) and hasattr(obj, "__tablename__")


def camel_to_snake(name: str) -> str:
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)).lower()


def guess_from_column(col) -> type:
    """
    Best‑effort mapping from a SQLAlchemy/SQLModel Column object to
    a Python runtime type (class). Falls back to Any.
    """
    # 1. native python_type if implemented
    try:
        return col.type.python_type
    except (AttributeError, NotImplementedError):
        pass

    # 2. Enum → underlying Enum class if present
    if isinstance(col.type, SAEnum) and col.type.enum_class:
        return col.type.enum_class

    # 3. match TYPE_MAP
    for sa_type, py_type in TYPE_MAP.items():
        if isinstance(col.type, sa_type):
            return py_type

    # 4. default
    return Any


def render(t) -> str:
    """把 annotation 对象转换成源码用的字符串"""
    origin = get_origin(t)
    if origin is Union:  # Optional[T]
        args = [a for a in get_args(t) if a is not type(None)]
        return f"{render(args[0])}"
    if origin in (list, List):
        return f"List[{render(get_args(t)[0])}]"
    return getattr(t, "__name__", "Any")  # 基本类型或 Enum


def collect_relationships(model_cls) -> dict[str, tuple[str, bool]]:
    """
    用 SQLAlchemy Mapper 提取关系:
    返回 {field_name: (TargetModelName, is_list)}.
    """
    rels: dict[str, tuple[str, bool]] = {}
    for key, prop in model_cls.__mapper__.relationships.items():  # type: ignore
        assert isinstance(prop, RelationshipProperty)
        rels[key] = (prop.mapper.class_.__name__, prop.uselist)
    return rels


# ------------------------------------------------------------------ #
# __init__.py PATCHERS
# ------------------------------------------------------------------ #


def _ensure_import(init_src: str, import_line: str) -> str:
    """
    Add `import_line` right before the __all__ declaration.
    If __all__ is missing (empty file), create a stub.
    """
    if import_line in init_src:
        return init_src
    return init_src.replace("__all__: list[str] =", f"{import_line}\n__all__: list[str] =", 1)


def update_models_init(model_cls: Type[DeclarativeMeta]):
    """
    将新模型追加到 app/models/__init__.py：
      1) 加入  from .<module> import <Model>
      2) 把模型名加入 __all__ 列表
    """
    model_name = model_cls.__name__
    endpoint = camel_to_snake(model_name)
    init_path = MODELS_DIR / "__init__.py"
    if not init_path.exists() or init_path.stat().st_size == 0:
        init_path.parent.mkdir(parents=True, exist_ok=True)
        init_path.write_text(
            "from .timestamp import register_timestamp_events\n\n"
            "__all__: list[str] = []\n\n"
            "# U Register timestamp update listener\n\n"
            "register_timestamp_events()\n",
            encoding="utf-8",
        )

    src = init_path.read_text("utf-8")
    if "__all__: list[str] =" not in src:
        src += "\n__all__: list[str] = []\n"

    # 1) import 行
    src = _ensure_import(src, f"from .{endpoint} import {model_name}")

    # 2) __all__ 列表
    m = re.search(r"(__all__:\s*list\[str\]\s*=\s*\[)([^\]]*)(\])", src, flags=re.S)
    if m:
        pre, body, post = m.groups()
        if not body.strip():
            body = body + "\n    "
        else:
            body = body + "    "
        if f'"{model_name}"' not in body:
            body = body + f'"{model_name}", '
        body = body.rstrip() + "\n"
        src = src.replace(m.group(0), f"{pre}{body}{post}")

    # -- 格式化空行 ----------------------------------------------
    # 1) 把连续 >=2 空行压缩为 1
    src = re.sub(r"\n{2,}", "\n", src)

    # 2) 然后确保 OptionItem 前恰好两个空行
    src = re.sub(r"\n+(?=__all__:)", "\n\n\n", src)

    init_path.write_text(src, "utf-8")


def update_crud_init(model_cls: Type[DeclarativeMeta]):
    endpoint = camel_to_snake(model_cls.__name__)
    init_path = CRUD_DIR / "__init__.py"
    if not init_path.exists():
        return
    src = init_path.read_text("utf-8")
    if "__all__: list[str] =" not in src:
        src += "\n__all__: list[str] = []\n"

    # import *
    src = _ensure_import(src, f"from .{endpoint} import *")
    # __all__
    names = [f"read_{endpoint}", f"option_{endpoint}", f"page_{endpoint}", f"create_{endpoint}", f"update_{endpoint}",
             f"remove_{endpoint}"]
    m = re.search(r"(__all__\:\s*list\[str\]\s*=\s*\[)([^\]]*)(\])", src, flags=re.S)
    if m:
        pre, body, post = m.groups()
        if not body.strip():
            body = body + "\n    "
        else:
            body = body + "    "
        for n in names:
            if f'"{n}"' not in body:
                body = body + f'"{n}", '
        body = body.rstrip() + "\n"
        src = src.replace(m.group(0), f"{pre}{body}{post}")

    # -- 格式化空行 ----------------------------------------------
    # 1) 把连续 >=2 空行压缩为 1
    src = re.sub(r"\n{2,}", "\n", src)

    # 2) 然后确保 OptionItem 前恰好两个空行
    src = re.sub(r"\n+(?=__all__:)", "\n\n\n", src)

    init_path.write_text(src, "utf-8")


def update_schemas_init(model_cls: Type[DeclarativeMeta]):
    """
    确保 app/schemas/__init__.py 至少包含:
        from pydantic import BaseModel
        class OptionItem(BaseModel): ...
    然后按顺序插入:
        from .<endpoint> import *
        __all__ = [...]
        # Update forward references for Pydantic v2
        from .<endpoint> import <Model>Read
        <Model>Read.model_rebuild()
    """
    model_name = model_cls.__name__
    endpoint = camel_to_snake(model_name)
    init_path = SCHEMAS_DIR / "__init__.py"

    # ------------------------------------------------------------
    # 1) 若文件不存在或为空，先写入最小骨架
    # ------------------------------------------------------------
    if not init_path.exists() or init_path.stat().st_size == 0:
        init_path.parent.mkdir(parents=True, exist_ok=True)
        init_path.write_text(
            "from pydantic import BaseModel\n\n"
            "__all__: list[str] = []\n\n"
            "# Update forward references for Pydantic v2\n\n"
            "class OptionItem(BaseModel):\n"
            "    label: str\n"
            "    value: str | int\n",
            encoding="utf-8",
        )

    src = init_path.read_text("utf-8")

    # helper sets to check duplication
    existing_imports = set(re.findall(r"^from \.\w+ import \w+Read", src, flags=re.M))
    existing_rebuilds = set(re.findall(r"^\w+Read\.model_rebuild\(\)", src, flags=re.M))

    # ------------------------------------------------------------
    # 2) 确保  from .<endpoint> import *
    #   —— 紧跟在 `from pydantic import BaseModel` 之后
    # ------------------------------------------------------------
    import_star = f"from .{endpoint} import *"
    if import_star not in src:
        src = src.replace(
            "from pydantic import BaseModel",
            f"from pydantic import BaseModel\n{import_star}",
            1,
        )

    # ------------------------------------------------------------
    # 3) 确保 __all__ 列表并追加条目
    # ------------------------------------------------------------
    relations = collect_relationships(model_cls)
    all_names = [
        f"{model_name}Base",
        f"{model_name}Create",
        f"{model_name}Read",
        f"{model_name}Update",
        f"{model_name}Filter",
    ]
    if relations:
        all_names.append(f"{model_name}ReadWithRelation")
    if "__all__" not in src:
        src = src.replace(import_star, f"{import_star}\n\n__all__: list[str] = []", 1)
    m = re.search(r"(__all__\:\s*list\[str\]\s*=\s*\[)([^\]]*)(\])", src, flags=re.S)
    if m:
        prefix, body, suffix = m.groups()
        if not body.strip():
            body = body + "\n    "
        else:
            body = body + "    "
        for n in all_names:
            if f'"{n}"' not in body:
                body = body + f'"{n}", '
        body = body.rstrip() + "\n"
        src = src.replace(m.group(0), f"{prefix}{body}{suffix}")

    # ------------------------------------------------------------
    # 4) Forward-refs 片段
    # ------------------------------------------------------------
    comment = "# Update forward references for Pydantic v2"
    if comment not in src:
        # 放在 OptionItem 之前更可读
        src = src.replace("class OptionItem", f"{comment}\n\nclass OptionItem", 1)

    forward_imp = f"from .{endpoint} import {model_name}Read"
    if forward_imp not in src:
        src = src.replace(comment, f"{comment}\n{forward_imp}", 1)

    # ensure single rebuild call for the primary model
    rebuild_call = f"{model_name}Read.model_rebuild()"
    if rebuild_call not in existing_rebuilds:
        src = src.replace("\nclass OptionItem", f"\n{rebuild_call}\nclass OptionItem", 1)
        existing_rebuilds.add(rebuild_call)

    # forward refs for relationship targets (skip primitives)
    skip_primitives = {"str", "int", "float", "bool", "datetime", "date", "time", "dict", "list", "Mapped"}
    for _, (tgt, _) in relations.items():
        if tgt in skip_primitives:
            continue

        tgt_imp = f"from .{camel_to_snake(tgt)} import {tgt}Read"
        if tgt_imp not in existing_imports:
            src = src.replace(comment, f"{comment}\n{tgt_imp}", 1)
            existing_imports.add(tgt_imp)

        tgt_rebuild = f"{tgt}Read.model_rebuild()"
        if tgt_rebuild not in existing_rebuilds:
            src = src.replace("\nclass OptionItem", f"\n{tgt_rebuild}\nclass OptionItem", 1)
            existing_rebuilds.add(tgt_rebuild)

    # -- 格式化空行 ----------------------------------------------
    # 1) 把连续 >=2 空行压缩为 1
    src = re.sub(r"\n{2,}", "\n", src)

    # 2) 然后确保 OptionItem 前恰好两个空行
    src = re.sub(r"\n+(?=__all__:)", "\n\n\n", src)
    src = re.sub(r"\n+(?=# Update forward)", "\n\n\n", src)
    src = re.sub(r"\n+(?=class OptionItem)", "\n\n\n", src)

    # ------------------------------------------------------------
    # 5) 落盘
    # ------------------------------------------------------------
    init_path.write_text(src, "utf-8")


# ------------------------------------------------------------------ #
# GENERATOR
# ------------------------------------------------------------------ #


def ensure_pkg_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    (path / "__init__.py").touch(exist_ok=True)


def generate_for_model(model_cls: Type[DeclarativeMeta]):
    from typing import Any

    name = model_cls.__name__
    endpoint = camel_to_snake(name)
    pk_name = list(model_cls.__table__.primary_key.columns)[0].name

    # fields
    basics = []
    reads = []
    updates = []
    filters = []
    # 1️⃣ 先拿注解字典（兼容 Pydantic v1 / v2）
    try:
        annotations = {n: f.annotation for n, f in model_cls.model_fields.items()}
    except AttributeError:  # pydantic v1
        annotations = {n: f.outer_type_ for n, f in model_cls.__fields__.items()}

    relations = collect_relationships(model_cls)

    # 2️⃣ 遍历列时优先用注解
    for col in model_cls.__table__.columns:
        if col.name in relations:
            continue
        if col.name in annotations:  # email/username 等在这里命中
            typ = render(annotations[col.name])  # 'str' → 'Optional[str]'
        else:
            # 退回旧的 guess_from_column 逻辑
            typ = guess_from_column(col).__name__

        filters.append(f"    {col.name}: Optional[{typ}] = None")
        if typ == "str":
            filters.append(f"    {col.name}__like: Optional[str] = None")
        filters.append(f"    {col.name}__in: Optional[List[{typ}]] = None")
        filters.append(f"    {col.name}__not_in: Optional[List[{typ}]] = None")
        if typ in ("int", "float", "datetime", "date"):
            filters.append(f"    {col.name}__gte: Optional[{typ}] = None")
            filters.append(f"    {col.name}__lte: Optional[{typ}] = None")
            filters.append(f"    {col.name}__between: Optional[tuple[{typ}, {typ}]] = None")

        if col.name == pk_name:
            reads.append(f"    {col.name}: {typ}")
            continue
        updates.append(f"    {col.name}: Optional[{typ}] = None")
        basics.append(f"    {col.name}: {typ}")

    basic_fields = "\n".join(basics) or "    pass"
    read_fields = "\n".join(reads) or "    pass"
    update_fields = "\n".join(updates) or "    pass"
    filter_fields = "\n".join(filters) or "    pass"

    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    crud_code = CRUD_TEMPLATE.format(
        model_name=name,
        schema_name=name,
        endpoint=endpoint,
        pk_name=pk_name,
        current_date=current_date
    )
    route_code = ROUTE_TEMPLATE.format(
        model_name=name,
        schema_name=name,
        endpoint=endpoint,
        pk_name=pk_name,
        current_date=current_date
    )
    schema_code = SCHEMAS_TEMPLATE.format(
        model_name=name,
        schema_name=name,
        basic_fields=basic_fields,
        read_fields=read_fields,
        update_fields=update_fields,
        filter_fields=filter_fields,
        endpoint=endpoint,
        current_date=current_date,
    )

    if relations:
        rel_lines = [
            f'    {fname}: Optional[{"List[" if is_list else ""}"{tgt}Read"{"]" if is_list else ""}] = None'
            for fname, (tgt, is_list) in relations.items()
        ]
        schema_code += (
                f"\n\nclass {name}ReadWithRelation({name}Read):\n"
                + "\n".join(rel_lines) +
                "\n\n    class Config:\n        from_attributes = True\n"
        )

    code_triplets = [
        (CRUD_DIR / f"{endpoint}.py", crud_code),
        (SCHEMAS_DIR / f"{endpoint}.py", schema_code),
        (ROUTES_DIR / f"{endpoint}.py", route_code),
    ]

    for path, code in code_triplets:
        if path.exists():
            print(f"[skip] {path}")
            continue
        ensure_pkg_dir(path.parent)
        path.write_text(dedent(code).lstrip(), "utf-8")
        print(f"[ok]   {path}")

    update_crud_init(model_cls)
    update_schemas_init(model_cls)
    update_models_init(model_cls)


# ------------------------------------------------------------------ #
# CLI
# ------------------------------------------------------------------ #
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "targets",
        nargs="*",
        help="Model modules (without .py). Leave empty to scan the whole app.models package.",
    )
    args = parser.parse_args()

    models: list[Type[DeclarativeMeta]] = []
    imported_modules: list[ModuleType] = []

    # ------------------------------------------------------------
    # 1) Import modules
    # ------------------------------------------------------------
    if args.targets:
        for t in args.targets:
            qualname = f"{MODELS_PACKAGE}.{t}"
            try:
                mod = import_submodule(qualname)
                imported_modules.append(mod)
            except ModuleNotFoundError as exc:
                print(f"[warn] {exc}")
    else:
        imported_modules = list(walk_model_modules(MODELS_PACKAGE))

    # ------------------------------------------------------------
    # 2) Try configure_mappers once after all imports
    # ------------------------------------------------------------
    try:
        configure_mappers()
    except (ArgumentError, InvalidRequestError) as exc:
        print(f"[error] 关系配置错误 → {exc}")

    # ------------------------------------------------------------
    # 3) Collect model classes
    # ------------------------------------------------------------
    for mod in imported_modules:
        models.extend(
            obj
            for _, obj in inspect.getmembers(mod, is_model_class)
            if obj.__module__ == mod.__name__
        )

    if not models:
        print("No models found. Nothing to generate.")
        return

    print("Discovered:", ", ".join(m.__name__ for m in models))
    for m in models:
        generate_for_model(m)


if __name__ == "__main__":
    main()
