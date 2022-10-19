"""
New Style Resources
~~~~~~~~~~~~~~~~~~~

New style resources make use of Python type annotations to simplify the
definition of data structures.

New style resources still utilise many of the existing classes eg
``ResourceBase``, ``ResourceOptions`` and all existing fields. Allowing
existing code (eg Mappings, Codecs) including custom implementations to be
utilised unchanged.

Example:

.. code-block:: python



"""
from typing import Any, Dict, Tuple, Type, Optional, TypeVar, Iterable

from odin import registration
from odin.fields import BaseField
from odin.resources import (
    ResourceBase,
    ResourceOptions,
    DEFAULT_TYPE_FIELD,
    NotProvided,
)
from .type_resolution import process_attribute, Options

__all__ = (
    "Options",
    "AnnotatedResourceType",
    "AnnotatedResource",
    "AResource",
)


MOT = TypeVar("MOT", bound=ResourceOptions)


def _new_meta_instance(
    meta_options_type: Type[MOT],
    meta_def: Optional[object],
    new_class: "AnnotatedResourceType",
) -> MOT:
    """
    Instantiate meta options instance and handle inheritance of required fields
    """
    base_meta = getattr(new_class, "_meta", None)
    new_meta = meta_options_type(meta_def)
    new_class.add_to_class("_meta", new_meta)

    # Namespace is inherited
    if base_meta and new_meta.name_space is NotProvided:
        new_meta.name_space = base_meta.name_space
    if new_meta.name_space is NotProvided:
        new_meta.name_space = new_class.__module__

    # Type field is inherited and default if not provided
    if base_meta and new_meta.type_field is NotProvided:
        new_meta.type_field = base_meta.type_field
    if new_meta.type_field is NotProvided:
        new_meta.type_field = DEFAULT_TYPE_FIELD

    # Key field is inherited
    if base_meta and new_meta.key_field_names is None:
        new_meta.key_field_names = base_meta.key_field_names

    # Field sorting is inherited
    if new_meta.field_sorting is NotProvided:
        new_meta.field_sorting = base_meta.field_sorting if base_meta else False

    return new_meta


def _iterate_attrs(attrs: Dict[str, Any]) -> Iterable[Tuple[str, BaseField]]:
    """
    Iterate through attributes and combine with annotations
    """
    annotations = attrs.pop("__annotations__", None) or {}

    # Yield any annotations processed into field instances
    for name, type_ in annotations.items():
        # Ignore all uppercase entries (consts)
        if not name.isupper():
            value = attrs.pop(name, NotProvided)
            yield name, process_attribute(type_, value)

    # Process any leftover fields
    yield from attrs.items()


class AnnotatedResourceType(type):
    def __new__(
        mcs,
        name: str,
        bases,
        attrs: dict,
        meta_options_type: Type[MOT] = ResourceOptions,
        abstract: bool = False,
    ):
        super_new = super().__new__

        # attrs will never be empty for classes declared in the standard way
        # (i.e. with the `class` keyword). This is quite robust.
        if name == "NewBase" and attrs == {}:
            return super_new(mcs, name, bases, attrs)

        parents = [
            base
            for base in bases
            if (
                isinstance(base, AnnotatedResourceType)
                and not (base.__name__ == "NewBase" and base.__mro__ == (base, object))
            )
        ]
        if not parents:
            # If this isn't a subclass of NewResource, don't do anything special.
            return super_new(mcs, name, bases, attrs)

        # Create the class.
        new_class = super_new(mcs, name, bases, {"__module__": attrs.pop("__module__")})

        # Create new meta instance
        new_meta = _new_meta_instance(
            meta_options_type, attrs.pop("Meta", None), new_class
        )

        # Bail out early if we have already created this class.
        r = registration.get_resource(new_meta.resource_name)
        if r is not None:
            return r

        # Add all field attributes to the class.
        for name, field in _iterate_attrs(attrs):
            new_class.add_to_class(name, field)

        # Sort the fields
        if not new_meta.field_sorting:
            new_meta.fields = sorted(new_meta.fields, key=hash)

        # Give fields an opportunity to do additional operations after the
        # resource is full populated and ready.
        for field in new_meta.all_fields:
            if hasattr(field, "on_resource_ready"):
                field.on_resource_ready()

        if abstract:
            return new_class

        # Register resource
        registration.register_resources(new_class)

        # Because of the way imports happen (recursively), we may or may not be
        # the first time this model tries to register with the framework. There
        # should only be one class for each model, so we always return the
        # registered version.
        return registration.get_resource(new_meta.resource_name)

    def add_to_class(cls, name, value):
        if hasattr(value, "contribute_to_class"):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)


class AnnotatedResource(
    ResourceBase, metaclass=AnnotatedResourceType, meta_options_type=ResourceOptions
):
    """
    New Style Resource utilising type annotations for defining fields
    """


AResource = AnnotatedResource
