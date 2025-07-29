from typing import Any, Sequence, Type, get_args, get_origin, Union
from uuid import UUID

import bson
import pydantic
from beanie import Document, PydanticObjectId, Link, BackLink
from pydantic import Field, SecretStr, AwareDatetime, NaiveDatetime, FutureDatetime, PastDatetime, PastDate, FutureDate, \
    BaseModel
from starlette_admin import BaseField, StringField, IntegerField, DecimalField, EmailField, URLField, HasOne, HasMany, \
    PasswordField, DateTimeField, CollectionField
from starlette_admin.converters import StandardModelConverter, converts
from starlette_admin.exceptions import NotSupportedAnnotation as BaseNotSupportedAnnotation
from starlette_admin.helpers import slugify_class_name

from .exceptions import NotSupportedAnnotation


class BaseODMModelConverter(StandardModelConverter):
    def get_type(self, model: Document, value: Any) -> Any:
        if isinstance(value, str) and hasattr(model, value):
            return model.model_fields[value].annotation
        raise ValueError(f"Can't find attribute with key {value}")

    def convert_fields_list(
        self, *, fields: Sequence[Any], model: Type[Document], **kwargs: Any
    ) -> Sequence[BaseField]:
        fields = [v for v in fields]
        try:
            return super().convert_fields_list(fields=fields, model=model, **kwargs)
        except BaseNotSupportedAnnotation as e:
            raise NotSupportedAnnotation(*e.args) from e


class ModelConverter(BaseODMModelConverter):
    @converts(Field)
    def conv_field(self, *args: Any, type: Field, **kwargs: Any) -> BaseField:
        kwargs.update(
            {
                "type": type.pydantic_field.annotation,
                "required": type.is_required_in_doc() and not type.primary_field,
            }
        )
        return self.convert(*args, **kwargs)

    @converts(Link)
    def conv_link(self, *args: Any, type: Link, **kwargs: Any) -> BaseField:
        field_name = kwargs.get("name")
        model: Document = kwargs.get("model")
        # get the model type from the Link field
        link_model_type = get_args(type)[0]
        # check if this is a list of links
        if get_origin(model.model_fields.get(field_name).annotation) is list:
            # link_model_type = get_args(link_model_type)[0]
            return HasMany(
                **self._standard_type_common(*args, **kwargs),
                identity=slugify_class_name(link_model_type.__name__)
            )

        return HasOne(
            **self._standard_type_common(*args, **kwargs),
            identity=slugify_class_name(link_model_type.__name__)
        )

    @converts(bson.ObjectId, bson.Regex, bson.Binary, pydantic.NameEmail, PydanticObjectId, UUID, BackLink)
    def conv_bson_string(self, *args: Any, **kwargs: Any) -> BaseField:
        return StringField(**self._standard_type_common(*args, **kwargs))

    @converts(bson.Int64)
    def conv_bson_int64(self, *args: Any, **kwargs: Any) -> BaseField:
        return IntegerField(**self._standard_type_common(*args, **kwargs))

    @converts(bson.Decimal128)
    def conv_bson_decimal(self, *args: Any, **kwargs: Any) -> BaseField:
        return DecimalField(**self._standard_type_common(*args, **kwargs))

    @converts(pydantic.EmailStr)
    def conv_pydantic_email(self, *args: Any, **kwargs: Any) -> BaseField:
        return EmailField(**self._standard_type_common(*args, **kwargs))

    @converts(pydantic.AnyUrl)
    def conv_pydantic_url(self, *args: Any, **kwargs: Any) -> BaseField:
        return URLField(**self._standard_type_common(*args, **kwargs))

    @converts(SecretStr)
    def conv_secret_str(self, *args: Any, **kwargs: Any) -> BaseField:
        return PasswordField(**self._standard_type_common(*args, **kwargs))

    @converts(AwareDatetime, NaiveDatetime, FutureDatetime, PastDatetime, PastDate, FutureDate)
    def conv_aware_datetime(self, *args: Any, **kwargs: Any) -> BaseField:
        return DateTimeField(**self._standard_type_common(*args, **kwargs))

    @converts(BaseModel)
    def conv_base_model(
            self,
            name: str,
            required: bool,
            *args: Any,
            **kwargs: Any,
    ) -> BaseField:
        model_type: Union[Type[BaseModel], None] = kwargs.pop("type", None)
        if model_type is None:
            raise ValueError("Missing 'type' in kwargs for BaseModel conversion.")

        # Build subfields by converting each field in the model
        return CollectionField(
            name=name,
            required=required,
            fields=[
                self.convert(
                    *args,
                    name=field_name,
                    type=field.annotation,
                    required=field.is_required(),
                    **kwargs,
                )
                for field_name, field in model_type.model_fields.items()
            ]
        )
