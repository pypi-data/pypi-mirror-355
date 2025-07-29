from typing import List, Union, Literal, Tuple, Any

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from pydantic import BaseModel
from sqlalchemy import inspect, desc, func
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel, select, or_, and_, Session


def get_default_order_by(model: type[SQLModel]):
    """根据模型动态获取排序字段，优先使用主键，否则尝试 created_at 字段。"""
    try:
        primary_keys = inspect(model).primary_key
        if primary_keys:
            return desc(primary_keys[0])  # 主键倒序
    except Exception:
        pass

    if hasattr(model, "created_at"):
        return desc(getattr(model, "created_at"))

    return None


def build_filters_from_params(params: BaseModel, model: type[SQLModel]) -> List:
    filters = []
    data = params.dict(exclude_none=True)

    for key, value in data.items():
        if '__' in key:
            field, op = key.split('__', 1)
        else:
            field, op = key, 'eq'

        if not hasattr(model, field):
            continue

        column = getattr(model, field)

        if op == 'eq':
            filters.append(column == value)
        elif op == 'like':
            filters.append(column.like(f"%{value}%"))
        elif op == 'in':
            filters.append(column.in_(value))
        elif op == 'not_in':
            filters.append(~column.in_(value))
        elif op == 'gte':
            filters.append(column >= value)
        elif op == 'lte':
            filters.append(column <= value)
        elif op == 'between' and isinstance(value, (tuple, list)) and len(value) == 2:
            filters.append(column.between(value[0], value[1]))

    return filters


async def read_one(
        db: AsyncSession,
        model: type[SQLModel],
        id_field: str = "id",
        obj_id: int = None,
        params: BaseModel = None,
        logic: str = "and"
):
    statement = select(model)
    order_clause = get_default_order_by(model)
    filters = []
    if obj_id is not None:
        order_clause = None
        filters.append(getattr(model, id_field) == obj_id)
    if params:
        filters.extend(build_filters_from_params(params, model))
    if filters:
        statement = statement.where(or_(*filters) if logic == "or" else and_(*filters))
    if order_clause is not None:
        statement = statement.order_by(order_clause)
    result = await db.execute(statement)
    return result.scalars().first()


async def list_all(
        db: AsyncSession,
        model: type[SQLModel],
        params: BaseModel = None,
        logic: str = "and",
        join_models: List[type[SQLModel]] = None,
        join_ons: List[Tuple[Any, Any]] = None,
        join_filters: List[Any] = None,
):
    order_clause = get_default_order_by(model)
    statement = select(model)
    if join_models and join_ons:
        for join_model, join_on in zip(join_models, join_ons):
            # join_on is expected to be a tuple: (left_column, right_column)
            left_col, right_col = join_on
            statement = statement.join(join_model, left_col == right_col)
    if order_clause is not None:
        statement = statement.order_by(order_clause)
    if params:
        filters = build_filters_from_params(params, model)
        if filters:
            statement = statement.where(or_(*filters) if logic == "or" else and_(*filters))
    if join_filters:
        for jf in join_filters:
            statement = statement.where(jf)
    result = await db.execute(statement)
    return result.scalars().all()


async def paginate_all(
        db: AsyncSession,
        model: type[SQLModel],
        params: BaseModel = None,
        logic: str = "and",
        join_models: List[type[SQLModel]] = None,
        join_ons: List[Tuple[Any, Any]] = None,
        join_filters: List[Any] = None,
) -> Page:
    order_clause = get_default_order_by(model)
    statement = select(model)
    if join_models and join_ons:
        for join_model, join_on in zip(join_models, join_ons):
            # join_on is expected to be a tuple: (left_column, right_column)
            left_col, right_col = join_on
            statement = statement.join(join_model, left_col == right_col)
    if order_clause is not None:
        statement = statement.order_by(order_clause)
    if params:
        filters = build_filters_from_params(params, model)
        if filters:
            statement = statement.where(or_(*filters) if logic == "or" else and_(*filters))
    if join_filters:
        for jf in join_filters:
            statement = statement.where(jf)
    return await paginate(db, statement)


async def create_one(
        db: AsyncSession,
        model: type[SQLModel],
        obj_in: BaseModel
):
    obj = model(**obj_in.dict())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def update_one(
        db: AsyncSession,
        model: type[SQLModel],
        obj_id: int,
        obj_in: BaseModel,
        id_field: str = "id"
):
    obj = await read_one(db, model, id_field=id_field, obj_id=obj_id)
    if not obj:
        return None
    for field, value in obj_in.dict(exclude_unset=True).items():
        setattr(obj, field, value)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def delete_one(
        db: AsyncSession,
        model: type[SQLModel],
        obj_id: int,
        id_field: str = "id"
):
    obj = await read_one(db, model, id_field=id_field, obj_id=obj_id)
    if not obj:
        return None
    await db.delete(obj)
    await db.commit()
    return obj


async def calculate_by_field(
        db: AsyncSession,
        model: type[SQLModel],
        field: Union[str, List[str]],
        func_name: Literal["count", "sum", "avg", "max", "min"] = "count",
        params: BaseModel = None,
        logic: str = "and",
        group_by: Union[str, List[str], None] = None
):
    fields = [field] if isinstance(field, str) else field
    for f in fields:
        if not hasattr(model, f):
            raise ValueError(f"Model {model} has no field {f}")

    aggregate_func = getattr(func, func_name.lower(), None)
    if not aggregate_func:
        raise ValueError(f"Unsupported aggregate function: {func_name}")

    agg_columns = [aggregate_func(getattr(model, f)).label(f"{func_name}_{f}") for f in fields]

    if group_by:
        if isinstance(group_by, str):
            group_by = [group_by]
        group_columns = []
        for gb_field in group_by:
            if not hasattr(model, gb_field):
                raise ValueError(f"Model {model} has no field {gb_field}")
            group_columns.append(getattr(model, gb_field))
        statement = select(*group_columns, *agg_columns).group_by(*group_columns)
    else:
        statement = select(*agg_columns)

    if params:
        filters = build_filters_from_params(params, model)
        if filters:
            statement = statement.where(or_(*filters) if logic == "or" else and_(*filters))

    result = await db.execute(statement)
    if group_by:
        return result.all()
    else:
        if len(fields) == 1:
            return result.scalar_one_or_none()
        else:
            return result.one_or_none()


def read_one_sync(
        db: Session,
        model: type[SQLModel],
        id_field: str = "id",
        obj_id: int = None,
        params: BaseModel = None,
        logic: str = "and"
):
    statement = select(model)
    order_clause = get_default_order_by(model)
    filters = []
    if obj_id is not None:
        order_clause = None
        filters.append(getattr(model, id_field) == obj_id)
    if params:
        filters.extend(build_filters_from_params(params, model))
    if filters:
        statement = statement.where(or_(*filters) if logic == "or" else and_(*filters))
    if order_clause is not None:
        statement = statement.order_by(order_clause)
    result = db.execute(statement)
    return result.scalars().first()


def list_all_sync(
        db: Session,
        model: type[SQLModel],
        params: BaseModel = None,
        logic: str = "and",
        join_models: List[type[SQLModel]] = None,
        join_ons: List[Tuple[Any, Any]] = None,
        join_filters: List[Any] = None,
):
    order_clause = get_default_order_by(model)
    statement = select(model)
    if join_models and join_ons:
        for join_model, join_on in zip(join_models, join_ons):
            # join_on is expected to be a tuple: (left_column, right_column)
            left_col, right_col = join_on
            statement = statement.join(join_model, left_col == right_col)
    if order_clause is not None:
        statement = statement.order_by(order_clause)
    if params:
        filters = build_filters_from_params(params, model)
        if filters:
            statement = statement.where(or_(*filters) if logic == "or" else and_(*filters))
    if join_filters:
        for jf in join_filters:
            statement = statement.where(jf)
    result = db.execute(statement)
    return result.scalars().all()


def paginate_all_sync(
        db: Session,
        model: type[SQLModel],
        params: BaseModel = None,
        logic: str = "and",
        join_models: List[type[SQLModel]] = None,
        join_ons: List[Tuple[Any, Any]] = None,
        join_filters: List[Any] = None,
) -> Page:
    order_clause = get_default_order_by(model)
    statement = select(model)
    if join_models and join_ons:
        for join_model, join_on in zip(join_models, join_ons):
            # join_on is expected to be a tuple: (left_column, right_column)
            left_col, right_col = join_on
            statement = statement.join(join_model, left_col == right_col)
    if order_clause is not None:
        statement = statement.order_by(order_clause)
    if params:
        filters = build_filters_from_params(params, model)
        if filters:
            statement = statement.where(or_(*filters) if logic == "or" else and_(*filters))
    if join_filters:
        for jf in join_filters:
            statement = statement.where(jf)
    return paginate(db, statement)


def create_one_sync(
        db: Session,
        model: type[SQLModel],
        obj_in: BaseModel
):
    obj = model(**obj_in.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_one_sync(
        db: Session,
        model: type[SQLModel],
        obj_id: int,
        obj_in: BaseModel,
        id_field: str = "id"
):
    obj = read_one_sync(db, model, id_field=id_field, obj_id=obj_id)
    if not obj:
        return None
    for field, value in obj_in.dict(exclude_unset=True).items():
        setattr(obj, field, value)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_one_sync(
        db: Session,
        model: type[SQLModel],
        obj_id: int,
        id_field: str = "id"
):
    obj = read_one_sync(db, model, id_field=id_field, obj_id=obj_id)
    if not obj:
        return None
    db.delete(obj)
    db.commit()
    return obj
