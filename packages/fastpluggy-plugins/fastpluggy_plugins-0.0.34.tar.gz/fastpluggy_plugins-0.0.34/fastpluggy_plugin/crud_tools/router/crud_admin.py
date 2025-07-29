import importlib
import inspect
from typing import Dict
from typing import Type, List

from fastapi import APIRouter, Request, Depends
from loguru import logger

from fastpluggy.core.database import Base
from fastpluggy.core.dependency import get_view_builder, get_fastpluggy
from fastpluggy.core.menu.decorator import menu_entry
from fastpluggy.core.models_tools.sqlalchemy import ModelToolsSQLAlchemy
from fastpluggy.core.tools.inspect_tools import get_module
from fastpluggy.core.widgets import TableWidget
from fastpluggy_plugin.crud_tools.config import CrudConfig

crud_admin_view_router = APIRouter(prefix='/models', tags=["front_action"])


def import_base(path: str) -> Type:
    """Dynamically import a Base class given its full import path."""
    module_path, class_name = path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def get_models_from_base(base: Type) -> List[Type]:
    """
    Pull all mapped classes out of a SQLAlchemy declarative Base
    (using the _decl_class_registry).
    """
    base_cls = import_base(base)
    mappers = getattr(base_cls, "registry", []).mappers
    result = []
    module_name = '__autodetected__'
    for mapper in mappers:  # type: ignore[attr-defined]
        cls = mapper.class_  # type: ignore[attr-defined]
        from ..router.crud import get_admin_instance
        admin = get_admin_instance(cls.__name__, default_crud_class=False)
        result.append({
            "module_name": module_name,
            "model_name": cls.__name__,
            "registered": admin is not None,
            "admin_class": admin.__class__.__name__ if admin else None
        })
    return result


def get_sqlalchemy_models(module_name: str) -> list[type]:
    module = get_module(f"{module_name}.models", reload=False)
    return [
        obj for name, obj in inspect.getmembers(module)
        if inspect.isclass(obj) and ModelToolsSQLAlchemy.is_sqlalchemy(obj) and obj is not Base
    ]


def get_admin_model_status(module_name: str) -> List[Dict[str, str]]:
    result = []
    models = get_sqlalchemy_models(module_name)
    for model in models:
        from ..router.crud import get_admin_instance
        admin = get_admin_instance(model.__name__, default_crud_class=False)
        result.append({
            "module_name": module_name,
            "model_name": model.__name__,
            "registered": admin is not None,
            "admin_class": admin.__class__.__name__ if admin else None
        })

    return result


@menu_entry(label="Models", type='admin')
@crud_admin_view_router.api_route("", methods=["GET", "POST"], name="list_models")
async def list_models(request: Request, view_builder=Depends(get_view_builder),
                      fast_pluggy=Depends(get_fastpluggy)):
    items_admin = []
    for module_name in fast_pluggy.module_manager.modules.values():
        try:
            admin = get_admin_model_status(module_name.package_name, )
            items_admin.extend(admin)
        except Exception as e:
            logger.exception(e)

    custom_base = CrudConfig().base_sqlalchemy_model
    if custom_base is not None:
        admin = get_models_from_base(custom_base)
        items_admin.extend(admin)

    from ..crud_link_helper import CrudLinkHelper
    from ..schema import CrudAction
    items = [
        TableWidget(
            data=items_admin,
            title="Crud Models",
            links=[
                CrudLinkHelper.get_crud_link(model='<model_name>', action=CrudAction.LIST),
            ]
        )
    ]

    return view_builder.generate(
        request,
        title="List of models",
        widgets=items,
    )
