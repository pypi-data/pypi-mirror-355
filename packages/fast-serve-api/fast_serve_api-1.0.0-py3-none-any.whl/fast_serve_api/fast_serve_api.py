import inspect
import re
import traceback
import types
from typing import (
    Any,
    Literal,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, create_model

from .models.fast_serve_api_error_model import FastServeApiErrorModel
from .models.fast_serve_api_list_model import FastServeApiListModel
from .models.fast_serve_api_model import FastServeApiModel


class FastServeApi:
    """Base class that automatically converts static methods to FastAPI endpoints"""

    _app: FastAPI = None

    @classmethod
    def initialize(cls, app: FastAPI):
        """Initialize the service with a FastAPI app instance and register endpoints"""
        cls._app = app
        cls._register_endpoints()

    @classmethod
    def _register_endpoints(cls):
        """Register all static methods as FastAPI endpoints"""
        if cls._app is None:
            raise ValueError(
                f"{cls.__name__} must be initialized with a FastAPI app instance "
                f"using {cls.__name__}.initialize(app)"
            )

        service_name = cls._camel_to_snake(cls.__name__)

        for method_name, method in inspect.getmembers(
            cls, predicate=inspect.isfunction
        ):
            if method_name.startswith("_"):
                continue

            cls._register_method_as_endpoint(method, method_name, service_name)

    @classmethod
    def _register_method_as_endpoint(cls, method, method_name: str, service_name: str):
        """Register a single method as an endpoint"""
        endpoint_path = f"/{service_name}/{method_name}"

        # Get method signature and type hints
        sig = inspect.signature(method)
        type_hints = get_type_hints(method)

        # Extract method metadata
        fields = cls._extract_method_fields(sig, type_hints)
        request_model = cls._create_request_model(cls.__name__, method_name, fields)
        base_return_type = type_hints.get("return", Any)
        all_optional = all(default != ... for _, default in fields.values())

        # Create return type
        if base_return_type != Any:
            return_type = base_return_type | FastServeApiErrorModel
        else:
            return_type = FastServeApiErrorModel

        # Create and register endpoint
        endpoint_func = cls._create_endpoint_function(
            method, fields, request_model, base_return_type, all_optional
        )
        endpoint_func.__name__ = f"{service_name}_{method_name}"

        cls._app.post(
            endpoint_path,
            response_model=return_type if return_type != Any else None,
            name=f"{service_name}_{method_name}",
        )(endpoint_func)

    @staticmethod
    def _extract_method_fields(sig, type_hints) -> dict[str, tuple[Any, Any]]:
        """Extract fields from method signature"""
        fields = {}
        for param_name, param in sig.parameters.items():
            param_type = type_hints.get(param_name, Any)
            default_value = (
                param.default if param.default != inspect.Parameter.empty else ...
            )
            fields[param_name] = (param_type, default_value)
        return fields

    @staticmethod
    def _create_request_model(class_name: str, method_name: str, fields: dict):
        """Create Pydantic model for request body"""
        request_model = create_model(
            f"{class_name}{method_name.title()}Request", **fields
        )

        # Handle single-field endpoints
        if len(fields) == 1:
            extra_request_type = fields[next(iter(fields))][0]
            request_model = request_model | extra_request_type

        return request_model

    @classmethod
    def _create_endpoint_function(
        cls, method, fields, request_model, return_type_hint, all_optional
    ):
        """Create the endpoint function based on parameters"""
        if not fields:
            # No parameters
            return cls._create_no_params_endpoint(method, return_type_hint)
        elif all_optional:
            # All parameters are optional
            return cls._create_optional_params_endpoint(
                method, fields, request_model, return_type_hint
            )
        else:
            # Has required parameters
            return cls._create_required_params_endpoint(
                method, fields, request_model, return_type_hint
            )

    @classmethod
    def _create_no_params_endpoint(cls, method, return_type_hint):
        """Create endpoint for methods with no parameters"""

        async def endpoint():
            try:
                result = method()
                result = cls._process_result(result, return_type_hint)
            except Exception as e:
                result = cls._create_error_response(e)

            return cls._create_json_response(result)

        return endpoint

    @classmethod
    def _create_optional_params_endpoint(
        cls, method, fields, request_model, return_type_hint
    ):
        """Create endpoint for methods with all optional parameters"""

        async def endpoint(request: request_model | None = None):  # type: ignore
            try:
                kwargs = cls._process_request(request, fields) if request else {}
                result = method(**kwargs)
                result = cls._process_result(result, return_type_hint)
            except Exception as e:
                result = cls._create_error_response(e)

            return cls._create_json_response(result)

        return endpoint

    @classmethod
    def _create_required_params_endpoint(
        cls, method, fields, request_model, return_type_hint
    ):
        """Create endpoint for methods with required parameters"""

        async def endpoint(request: request_model):  # type: ignore
            try:
                kwargs = cls._process_request(request, fields)
                result = method(**kwargs)
                result = cls._process_result(result, return_type_hint)
            except Exception as e:
                result = cls._create_error_response(e)

            return cls._create_json_response(result)

        return endpoint

    @classmethod
    def _process_request(cls, request, fields) -> dict[str, Any]:
        """Process incoming request and extract parameters"""
        kwargs = {}

        if issubclass(type(request), BaseModel):
            # Handle Pydantic model requests
            if len(fields) == 1:
                key = next(iter(fields))
                param_type = fields[key][0]
                # Check if the request is the exact type expected by the parameter
                if type(request) is param_type:
                    # The raw value was converted to the expected model
                    kwargs[key] = request
                else:
                    # This is the wrapped request model
                    kwargs = request.model_dump()
            else:
                kwargs = request.model_dump()
        else:
            # Handle raw value for single-field endpoints
            key = next(iter(fields))
            kwargs[key] = request

        # Process parameters (convert types, handle Pydantic models, etc.)
        return cls._process_parameters(kwargs, fields)

    @classmethod
    def _process_parameters(
        cls, kwargs: dict[str, Any], fields: dict
    ) -> dict[str, Any]:
        """Process parameters: handle Pydantic models, Sets, Lists, etc."""
        processed = {}

        for key, value in kwargs.items():
            if key not in fields:
                continue

            param_type = fields[key][0]
            processed[key] = cls._convert_parameter(value, param_type)

        return processed

    @classmethod
    def _convert_parameter(cls, value: Any, param_type: Any) -> Any:
        """Convert a single parameter to the expected type"""
        # Handle Pydantic models
        if (
            isinstance(value, dict)
            and isinstance(param_type, type)
            and issubclass(param_type, BaseModel)
        ):
            return param_type(**value)

        # Handle collections
        if isinstance(value, list):
            origin = get_origin(param_type)
            args = get_args(param_type)

            # Convert to Set if needed
            if origin is set or param_type is set:
                return set(value)

            # Handle List[PydanticModel]
            if (
                origin is list
                and args
                and isinstance(args[0], type)
                and issubclass(args[0], BaseModel)
            ):
                return [
                    args[0](**item) if isinstance(item, dict) else item
                    for item in value
                ]

        return value

    @classmethod
    def _process_result(cls, result: Any, return_type_hint: Any) -> Any:
        """Process the result: validate type and convert for JSON serialization"""
        # Validate return type
        if return_type_hint is not Any and not cls._validate_return_type(
            result, return_type_hint
        ):
            raise TypeError(
                f"Return type mismatch: expected {return_type_hint}, "
                f"but got {type(result).__name__} with value {result!r}"
            )

        # Convert for JSON serialization
        return cls._prepare_result_for_json(result)

    @classmethod
    def _prepare_result_for_json(cls, result: Any) -> Any:
        """Prepare result for JSON serialization"""
        # Convert sets to lists
        if isinstance(result, set):
            return list(result)

        # Handle List[PydanticModel]
        if isinstance(result, list):
            return [
                item.model_dump() if isinstance(item, BaseModel) else item
                for item in result
            ]

        # Handle Pydantic models
        if isinstance(result, BaseModel):
            # Check if it's a valid response model
            if not (
                issubclass(result.__class__, FastServeApiModel)
                or issubclass(result.__class__, FastServeApiListModel)
            ):
                raise TypeError(
                    "Return type must be a subclass of FastServeApiModel or FastServeApiListModel."
                )
            return result.model_dump()

        return result

    @staticmethod
    def _create_error_response(exception: Exception) -> dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "message": str(exception),
            "stack_trace": "".join(
                traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                )
            ),
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        }

    @staticmethod
    def _create_json_response(result: Any) -> JSONResponse:
        """Create JSON response with appropriate status code"""
        if isinstance(result, dict):
            status_code = result.get("status_code") or status.HTTP_200_OK
        else:
            status_code = status.HTTP_200_OK

        return JSONResponse(status_code=status_code, content=result)

    @staticmethod
    def _camel_to_snake(name: str) -> str:
        """Convert CamelCase to snake_case"""
        # Remove 'Service' suffix if present
        if name.endswith("Service"):
            name = name[:-7]

        # Convert CamelCase to snake_case
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    @staticmethod
    def _validate_return_type(value: Any, expected_type: Any) -> bool:
        """Validate that a value matches the expected type annotation"""
        # Handle None type
        if expected_type is type(None):
            return value is None

        # Handle Any type
        if expected_type is Any:
            return True

        # Get origin and args for generic types
        origin = get_origin(expected_type)
        args = get_args(expected_type)

        # Handle Union types (including Optional)
        if origin is Union:
            return any(FastServeApi._validate_return_type(value, arg) for arg in args)

        # Handle new union syntax (Python 3.10+) like bool | None
        if origin is types.UnionType:
            return any(FastServeApi._validate_return_type(value, arg) for arg in args)

        # Handle Literal type
        if origin is Literal:
            return value in args

        # Handle simple types
        if origin is None:
            # For Pydantic models
            if isinstance(expected_type, type) and issubclass(expected_type, BaseModel):
                return isinstance(value, expected_type)
            # Special case: bool is a subclass of int in Python
            if expected_type is int and isinstance(value, bool):
                return False
            # For primitive types
            return isinstance(value, expected_type)

        # Handle collection types
        return FastServeApi._validate_collection_type(value, origin, args)

    @classmethod
    def _validate_collection_type(cls, value: Any, origin: Any, args: tuple) -> bool:
        """Validate collection types (List, Dict, Set, Tuple)"""
        # Handle List type
        if origin is list:
            if not isinstance(value, list):
                return False
            if not args:
                return True
            item_type = args[0]
            return all(cls._validate_return_type(item, item_type) for item in value)

        # Handle Dict type
        if origin is dict:
            if not isinstance(value, dict):
                return False
            if not args:
                return True
            key_type, value_type = args[0], args[1]
            return all(
                cls._validate_return_type(k, key_type)
                and cls._validate_return_type(v, value_type)
                for k, v in value.items()
            )

        # Handle Set type
        if origin is set:
            if not isinstance(value, set):
                return False
            if not args:
                return True
            item_type = args[0]
            return all(cls._validate_return_type(item, item_type) for item in value)

        # Handle Tuple type
        if origin is tuple:
            if not isinstance(value, tuple):
                return False
            if not args:
                return True
            # Handle Tuple[type, ...] (variable length)
            if len(args) == 2 and args[1] is ...:
                return all(cls._validate_return_type(item, args[0]) for item in value)
            # Handle Tuple[type1, type2, ...] (fixed length)
            if len(value) != len(args):
                return False
            return all(
                cls._validate_return_type(v, t)
                for v, t in zip(value, args, strict=False)
            )

        # For other generic types, just check the origin
        return isinstance(value, origin) if origin else False

    @classmethod
    def get_app(cls) -> FastAPI:
        """Get the FastAPI application instance"""
        if cls._app is None:
            raise ValueError(
                f"{cls.__name__} has not been initialized. "
                f"Call {cls.__name__}.initialize(app) first."
            )
        return cls._app
