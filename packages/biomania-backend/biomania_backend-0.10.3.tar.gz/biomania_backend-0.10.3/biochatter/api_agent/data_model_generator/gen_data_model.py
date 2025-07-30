from __future__ import annotations
import os
import inspect
import json
import re
from types import MappingProxyType
from typing import Any, get_origin, get_args, Union
from copy import deepcopy
import argparse
import importlib
from tqdm import tqdm
import subprocess
from dotenv import load_dotenv
load_dotenv()

from docstring_parser import parse
import libcst as cst
import libcst.matchers as m
from pydantic import Field, create_model, PrivateAttr
from pydantic.fields import FieldInfo
from importlib.metadata import version
from types import NoneType

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from langchain.chat_models import init_chat_model
from langchain.output_parsers.fix import OutputFixingParser
from langchain.output_parsers import RetryOutputParser

from datamodel_code_generator import DataModelType, PythonVersion
from datamodel_code_generator.model import get_data_model_types
from datamodel_code_generator.parser.jsonschema import JsonSchemaParser

from jinja2 import Environment, FileSystemLoader
import warnings

from ..base.agent_abc import BaseAPI
from ..base.utils import get_data_model_name

def get_py_version() -> PythonVersion:
    """Get the Python version.
    """
    from sys import version_info
    py_version = version_info.major, version_info.minor, version_info.micro
    assert py_version[0] == 3, "Python version must be 3.x.x"
    if py_version[1] < 9:
        raise ValueError("Python version must be less than 3.14 and larger than or equal to 3.9.")
    if py_version[1] >= 9 and py_version[1] < 10:
        return PythonVersion.PY_39
    if py_version[1] >= 10 and py_version[1] < 11:
        return PythonVersion.PY_310
    if py_version[1] >= 11 and py_version[1] < 12:
        return PythonVersion.PY_311
    if py_version[1] >= 12 and py_version[1] < 13:
        return PythonVersion.PY_312
    if py_version[1] >= 13 and py_version[1] < 14:
        return PythonVersion.PY_313
    if py_version[1] >= 14:
        raise ValueError("Python version must be less than 3.14 and larger than or equal to 3.9.")
    
def data_model_to_py(data_model: type[BaseAPI], additional_imports: list[str], need_import: bool) -> str:
    """Convert a Pydantic model to a Python code.
    """
    json_schema = json.dumps(data_model.model_json_schema())
    data_model_types = get_data_model_types(
        DataModelType.PydanticV2BaseModel,
        target_python_version=get_py_version()
    )
    parser = JsonSchemaParser(
        json_schema,
        data_model_type=data_model_types.data_model,
        data_model_root_type=data_model_types.root_model,
        data_model_field_type=data_model_types.field_model,
        data_type_manager_type=data_model_types.data_type_manager,
        dump_resolve_reference_action=data_model_types.dump_resolve_reference_action,
        base_class="BaseAPI",
        additional_imports=additional_imports
    )
    codes: str = parser.parse()

    # Parse the code into a CST
    module = cst.parse_module(codes)

    class DataModelTransformer(cst.CSTTransformer):
        def __init__(self, data_model: type[BaseAPI], need_import: bool):
            self.data_model = data_model
            self.need_import = need_import
            self.doc = inspect.getdoc(data_model)
            if self.doc is None:
                self.doc = "No description available."
            self.doc = '\n    '.join(self.doc.strip().splitlines())
            self.doc = self.doc.replace('\\', '\\\\')

        def leave_Assign(self, original_node: cst.Assign, updated_node: cst.Assign) -> cst.Assign:
            # Remove model_config
            if isinstance(original_node.targets[0].target, cst.Name) and \
                original_node.targets[0].target.value == "model_config":
                return cst.RemovalSentinel.REMOVE # type: ignore[return-value]
            return updated_node

        def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
            # Add docstring to the class
            docstring = cst.SimpleString(f'"""\n    {self.doc}\n    """')

            # Add private attributes
            private_attrs = []
            keys = ["_api_name", "_products_str_repr", "_data_name"]
            for key in keys:
                call = self.data_model.__private_attributes__[key].__repr__()
                call = cst.parse_expression(call)
                call = call.with_changes(func=cst.Name("PrivateAttr"))

                private_attrs.append(
                    cst.SimpleStatementLine([
                        cst.AnnAssign(
                            target=cst.Name(key),
                            value=call,
                            annotation=cst.Annotation(
                                cst.Name("str")
                            )
                        )
                    ])
                )

            return updated_node.with_changes(
                body=updated_node.body.with_changes(
                    body=[cst.SimpleStatementLine([cst.Expr(docstring)])] + \
                    list(updated_node.body.body) + private_attrs
                )
            )

        def leave_Import(self, original_node: cst.Import, updated_node: cst.Import) -> cst.Import | cst.RemovalSentinel:
            # Remove BaseAPI import
            for name in original_node.names:
                if isinstance(name.name, cst.Name) and name.name.value == "BaseAPI":
                    return cst.RemovalSentinel.REMOVE
            return updated_node

        def leave_ImportFrom(self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom) -> cst.ImportFrom | cst.RemovalSentinel:
            # Remove imports if not needed
            if not self.need_import:
                return cst.RemovalSentinel.REMOVE
            return updated_node

    # Apply the transformer
    transformer = DataModelTransformer(data_model, need_import)
    modified_module = module.visit(transformer)
    codes = modified_module.code

    # hack: replace _products_str_repr: str = to _products_str_repr: list[str] = 
    # since libcst not support list[str] in the type annotation.
    codes = re.sub(r'_products_str_repr\s*:\s*str', '_products_str_repr: list[str]', codes)
    
    return codes

def simplify_desc(
    api_data: dict, 
    llm: BaseChatModel,
) -> dict[str, tuple[Any, Field]]:
    """Summarize the descriptions of multiple fields.
    """

    # Jiahang (TODO): common codes below, should be reused.
    output_format_annotations = {
        "doc": str,
    }
    desc = {
        "doc": api_data['description'],
    }
    for field in api_data['fields']:
        output_format_annotations[field['name']] = str
        desc[field['name']] = field['description']

    output_format = create_model(
        "OutputFormat", **output_format_annotations,  # type: ignore
    )

    parser = PydanticOutputParser(pydantic_object=output_format)
    prompt = ChatPromptTemplate([
        ("system", "Summarize descriptions of each term into one or two sentences. The response format follows these instructions:\n{format}"),
        ("user", "{desc}"),
    ])

    prompt = prompt.invoke({"desc": desc, "format": parser.get_format_instructions()})
    response = llm.invoke(prompt)

    except_tag = True
    if except_tag:
        try:
            result: dict = parser.invoke(response).model_dump()
            except_tag = False
        except OutputParserException as e:
            except_tag = True
    if except_tag:
        try:
            correct_parser = OutputFixingParser.from_llm(parser=parser, llm=llm)
            result: dict = correct_parser.invoke(response).model_dump()
            except_tag = False
        except OutputParserException as e:
            except_tag = True
    if except_tag:
        try:
            correct_parser = RetryOutputParser.from_llm(parser=parser, llm=llm, max_retries=3)
            result: dict = correct_parser.parse_with_prompt(response.content, prompt)
        except OutputParserException as e:
            print(f"The descriptions of API or arguments of {api_data['name']} are not summarized correctly. Please summarize them manually.")
            print(f"The error is: {e}")
            return api_data
        
    new_api_data = deepcopy(api_data)
    new_api_data['description'] = result['doc']
    for i in range(len(new_api_data['fields'])):
        new_api_data['fields'][i]['description'] = result[new_api_data['fields'][i]['name']]

    return new_api_data

def add_tools_dict(codes: str, data_models: list[type[BaseAPI]]) -> str:
    """Add TOOLS_DICT to the end of the code using libcst.
    
    Args:
        codes: The source code as a string
        data_models: List of data model classes to include in TOOLS_DICT
        
    Returns:
        Modified source code with TOOLS_DICT added
    """
    # Parse the source code into a CST
    module = cst.parse_module(codes)
    
    # Create a transformer to add the TOOLS dictionary
    class AddToolsTransformer(cst.CSTTransformer):
        def __init__(self, data_models: list[type[BaseAPI]]):
            self.data_models = data_models
            
        def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
            # Create dictionary elements with proper indentation
            elements = []
            for data_model in self.data_models:
                key = cst.SimpleString(f'"{data_model._api_name.default}"')
                value = cst.Name(data_model.__name__)
                elements.append(cst.DictElement(
                    key=key, 
                    value=value,
                ))
            
            # Create the TOOLS_DICT assignment with two newlines before it
            tools_dict = cst.SimpleStatementLine([
                cst.Assign(
                    targets=[cst.AssignTarget(cst.Name("TOOLS_DICT"))],
                    value=cst.Dict(elements=elements)
                )
            ])
            
            # Add two newlines and the assignment to the end of the module
            return updated_node.with_changes(
                body=list(updated_node.body) + [
                    tools_dict
                ]
            )
    
    # Apply the transformer
    modified_module = module.visit(AddToolsTransformer(data_models))
    
    # Convert the modified CST back to source code
    return modified_module.code

def remove_tools_dict(codes: str) -> str:
    # Parse the source code into a CST
    module = cst.parse_module(codes)
    
    # Create a transformer to remove the TOOLS dictionary assignment
    class RemoveToolsTransformer(cst.CSTTransformer):
        def leave_Assign(self, original_node: cst.Assign, updated_node: cst.Assign) -> cst.Assign | cst.RemovalSentinel:
            # Check if this is a TOOLS assignment
            for target in original_node.targets:
                if isinstance(target.target, cst.Name) and target.target.value == 'TOOLS_DICT':
                    return cst.RemovalSentinel.REMOVE
            return updated_node
    
    # Apply the transformer
    modified_module = module.visit(RemoveToolsTransformer())
    
    # Convert the modified CST back to source code
    return modified_module.code

def apis_to_data_models(
        api_dict: dict[str, dict], 
        need_import: bool = True,
        ) -> list[type[BaseAPI]]:
    """
    Although we have many string operations like hack in this implementation, all these hacks are bound to
    specific version of datamodel_code_generator and pydantic. They are not bound to any specific package, module
    or API, meaning that they are still generic to any API.
    """
    assert version("datamodel_code_generator") == "0.30.1", \
        "datamodel-code-generator version must be 0.30.1 since some fine-grained operations " \
        "are based on the outputs of this package. Different versions may lead to different outputs " \
        "and thus invalidate those fine-grained operations."
    
    base_attributes = set(dir(BaseAPI))
    classes_list = []
    codes_list = []

    llm = init_chat_model(os.environ.get("MODEL"), model_provider="openai", temperature=0.7)

    for api_name, _api in tqdm(api_dict.items()):
        if "_deprecated" in _api and _api['_deprecated']:
            continue
        assert 'products' in _api and 'data_name' in _api, \
            "configs should contain 'products' and 'data_name'."
        api = _api['api']
        module = inspect.getmodule(api)
        name = api.__name__
        if name.startswith("_"):
            raise Warning(f"apition {name} is private/internal and should not be included in the data model.")

        # Parse docstring for parameter descriptions
        doc = inspect.getdoc(api) or ""
        parsed_doc = parse(doc)
        doc_params = {p.arg_name: p.description or "No description available." for p in parsed_doc.params}

        sig = inspect.signature(api)
        fields = {}

        for param_name, param in sig.parameters.items():
            # Skip *args and **kwargs for now
            if param_name in ("args", "kwargs"):
                continue

            # Fetch docstring description or fallback
            description = doc_params.get(param_name, "No description available.")

            # Determine default value
            # If no default, we use `...` indicating a required field
            if param_name == _api['data_name']:
                default_value = "data"
            else:
                if param.default is not inspect.Parameter.empty:
                    default_value = param.default

                    # Convert MappingProxyType to a dict for JSON compatibility
                    if isinstance(default_value, MappingProxyType):
                        default_value = dict(default_value)

                    # Handle non-JSON-compliant float values by converting to string
                    if default_value in [float("inf"), float("-inf"), float("nan"), float("-nan")]:
                        default_value = str(default_value)
                else:
                    default_value = ...  # No default means required
            
            # Jiahang (TODO):  
            annotation = Any

            # Append the original annotation as a note in the description if
            # available
            if param.annotation is not inspect.Parameter.empty:
                # Jiahang (TODO): this is not needed, since all predicted types should be
                # basic types.
                description += f"\nOriginal type annotation: {param.annotation}"

            # If default_value is None, parameter can be Optional
            # If not required, mark as Optional[Any]
            if default_value is None:
                annotation = Any | None

            # Prepare field kwargs
            field_kwargs = {"description": description, "default": default_value}

            # If field name conflicts with BaseModel attributes, alias it
            field_name = param_name
            if param_name in base_attributes:
                alias_name = param_name + "_param"
                field_kwargs["alias"] = param_name
                field_name = alias_name

            fields[field_name] = (annotation, Field(**field_kwargs))

        try:
            fields = simplify_desc(fields, llm)
            doc = simplify_desc({"doc": parsed_doc.description}, llm)['doc']
        except OutputParserException as e:
            doc = parsed_doc.description
            print(f"The descriptions of API or arguments of {name} are not summarized correctly. Please summarize them manually.")

        # Create the Pydantic model
        fields['_api_name'] = (str, PrivateAttr(default=api_name))
        fields['_products_str_repr'] = (str, PrivateAttr(default=_api['products']))
        fields['_data_name'] = (str, PrivateAttr(default=_api['data_name']))

        data_model = create_model(
            get_data_model_name(api_name),
            __doc__ = doc, 
            __base__ = BaseAPI,
            **fields,
        )
        classes_list.append(data_model)

        additional_imports = [
            "biochatter.api_agent.base.agent_abc.BaseAPI",
            "pydantic.PrivateAttr",
        ]
        codes = data_model_to_py(data_model, additional_imports, need_import)
        codes_list.append(codes)

        # hack. Subsequent codes need no repeated imports. This is important
        # to avoid erros like __future__ import not at the top of the file.
        need_import = False

    # hack. Add TOOLS_DICT to the end of the file.
    codes = "\n\n".join(codes_list)
    return classes_list, codes

def get_output_path(package_name: str, api_dict_name: str, as_module: bool = False) -> str:
    if as_module:
        return f"biochatter.api_agent.python.{package_name}.{api_dict_name}"
    else:
        return f"biochatter/api_agent/python/{package_name}/{api_dict_name}.py"

def escape_str(s: str) -> str:
    """Escape strings. 
    Jiahang (TODO): is there any better solution to auto-escape strings?
    """
    s = ' '.join(s.strip().splitlines())
    s = s.replace('\\', '\\\\')
    s = s.replace('\n', '\\n')
    s = s.replace('\t', '\\t')
    s = s.replace('\r', '\\r')
    s = s.replace('\b', '\\b')
    s = s.replace('\f', '\\f')
    s = s.replace('\v', '\\v')
    s = s.replace('\a', '\\a')
    s = s.replace('"', '\\"')
    s = s.replace("'", "\\'")
    
    return s

def escape_desc(api_data: dict) -> dict:
    api_data['description'] = escape_str(api_data['description'])
    for field in api_data['fields']:
        field['description'] = escape_str(field['description'])
    return api_data

def _apis_to_data_models_jinja(api_dict: dict[str, dict]) -> str:
    
    base_attributes = set(dir(BaseAPI))
    apis = []

    llm = init_chat_model(os.environ.get("MODEL"), model_provider="openai", temperature=0.7)
    
    for api_name, _api in tqdm(api_dict.items()):
        if "_deprecated" in _api and _api['_deprecated']:
            continue
        assert 'products' in _api and 'data_name' in _api, \
            "configs should contain 'products' and 'data_name'."
        api = _api['api']

        # Parse docstring for parameter descriptions
        doc = inspect.getdoc(api) or ""
        parsed_doc = parse(doc)
        doc_params = {p.arg_name: p.description or "No description available." for p in parsed_doc.params}

        sig = inspect.signature(api)
        fields = []
        for param_name, param in sig.parameters.items():
            # Skip *args and **kwargs for now
            if param_name in ("args", "kwargs"):
                continue

            # Fetch docstring description or fallback
            description = doc_params.get(param_name, "No description available.")
            description = ' '.join(description.strip().splitlines())

            # Determine default value
            # If no default, we use `...` indicating a required field
        
            if param.default is not inspect.Parameter.empty:
                default_value = param.default
                default_value_expr = cst.parse_expression(str(default_value))
                default_value_module = cst.parse_module(str(default_value))

                # if isinstance(default_value_expr, cst.Integer):
                #     annotation = int
                # elif isinstance(default_value_expr, cst.Float):
                #     annotation = float
                # elif isinstance(default_value_expr, cst.SimpleString):
                #     annotation = str
                # elif isinstance(default_value_expr, cst.List):
                #     annotation = list[Any]
                # elif isinstance(default_value_expr, cst.Tuple):
                #     annotation = tuple[Any, ...]
                # elif isinstance(default_value_expr, cst.Set):
                #     annotation = set[Any]
                # elif isinstance(default_value_expr, cst.Dict):
                #     annotation = dict[Any, Any]
                # elif default_value in ["True", "False"]: # libcst does not support bool type
                #     annotation = bool
                # elif default_value is None:
                #     annotation = Any | None
                # elif isinstance(default_value_expr, cst.Name):
                #     default_value = f'"{default_value_module.code}"'
                #     annotation = Any
                # else:
                #     warnings.warn(f"Unrecognized default value type: {default_value}, skip this arg {param_name}.")
                #     continue

                # # Convert MappingProxyType to a dict for JSON compatibility
                # elif isinstance(default_value_expr, cst.Dict):
                #     default_value = default_value_module.code

                # Handle non-JSON-compliant float values by converting to string
                # elif default_value in [float("inf"), float("-inf"), float("nan"), float("-nan")]:
                #     default_value = str(default_value)
                #     default_value = f'"{default_value}"'

            else:
                default_value = ...  # No default means required
            
            # annotation = Any

            # # If default_value is None, parameter can be Optional
            # # If not required, mark as Optional[Any]
            # if default_value is None:
            #     annotation = Any | None


            # Jiahang (TODO): may deprecate this part.
            # If field name conflicts with BaseModel attributes, alias it
            # field_name = param_name
            # alias = None
            # if param_name in base_attributes:
            #     alias_name = param_name + "_param"
            #     alias = param_name
            #     field_name = alias_name
            
            # Prepare field kwargs
            field_kwargs = {
                "name": field_name,
                "description": escape_str(description), 
                "annotation": annotation,
                "default": default_value, 
                "original_annotation": param.annotation if param.annotation is not inspect.Parameter.empty else None,
                "alias": alias,
            }

            fields.append(field_kwargs)

        # try:
        #     fields = simplify_desc(fields, llm)
        #     doc = simplify_desc({"doc": parsed_doc.description}, llm)['doc']
        # except OutputParserException as e:
        #     doc = parsed_doc.description
        #     print(f"The descriptions of API or arguments of {api_name} are not summarized correctly. Please summarize them manually.")

        doc = ' '.join(parsed_doc.description.strip().splitlines())
        apis.append({
            "name": escape_str(get_data_model_name(api_name)),
            "description": escape_str(doc),
            "fields": fields,
            "products": _api['products'],
            "data_name": _api['data_name'],
        })


    env = Environment(loader=FileSystemLoader("biochatter/api_agent/data_model_generator"))
    template = env.get_template("data_model.jinja")
    codes = template.render(apis=apis)

    return codes

def is_python_builtin_type(type_annotation) -> bool:
    """
    Check if a type is a Python built-in type only.
    Only these types are considered recognizable:
    - Basic types: int, float, str, bool
    - Container types: list, dict, set, tuple
    - None
    - Any
    """
    # Handle None and Any
    if type_annotation is None or type_annotation is Any:
        return True
        
    # Get the origin type for generic types
    origin = get_origin(type_annotation)
    if origin is not None:
        # For container types (list, dict, set, tuple), check their type arguments
        if origin in (list, dict, set, tuple):
            args = get_args(type_annotation)
            # For dict, check both key and value types
            if origin is dict:
                return all(is_python_builtin_type(arg) for arg in args)
            # For other containers, check their element type
            return is_python_builtin_type(args[0])
        # For Union types, check all possible types
        elif origin is Union:
            return all(is_python_builtin_type(arg) for arg in get_args(type_annotation))
        return False

    # Check if it's a built-in type
    return type_annotation in (int, float, str, bool, list, dict, set, tuple)      

def apis_to_data_models_jinja(api_dict: dict[str, dict]) -> str:
    apis = []
    llm = init_chat_model(
        os.environ.get("MODEL"), 
        model_provider="openai", 
        temperature=0.7,
    )
    type_checker = init_chat_model(
        os.environ.get("MODEL"), 
        model_provider="openai", 
        temperature=0.7,
    )

    base_attributes = set(dir(BaseAPI))

    for api_name, _api in tqdm(api_dict.items()):
        if "_deprecated" in _api and _api['_deprecated']:
            continue
        assert 'products' in _api and 'data_name' in _api, \
            "configs should contain 'products' and 'data_name'."
        api = _api['api']

        # Parse docstring for parameter descriptions
        doc = inspect.getdoc(api) or ""
        parsed_doc = parse(doc)
        doc_params = {p.arg_name: p.description or "No description available." for p in parsed_doc.params}

        sig = inspect.signature(api)
        fields = []
        for param_name, param in sig.parameters.items():
            # Skip *args and **kwargs for now

            if param_name in ("args", "kwargs"):
                continue
            # Fetch docstring description or fallback
            description = doc_params.get(param_name, "No description available.")
            description = ' '.join(description.strip().splitlines())

            # Determine type annotation
            # Jiahang (TODO): this llm invoke with the requirements of 
            # error correct, retry, etc., should be unified as they are
            # used in many places.
            # Jiahang (TODO): extract prompts into a separate file.
            # Jiahang (TODO, high priority): weird, why str annotation can fix the prediction into
            # correct str "data", but typing.Any annotation will lead to random generation like
            # a dict {}? how much the type annotation matters?

            if param_name == _api['data_name']:
                annotation = "str"
            elif param.annotation is not inspect.Signature.empty:
                prompt = ChatPromptTemplate([
                    ("system", "You are a python function type checker. You are given a type annotation of an argument. You need to check if the type annotation is recognizable. Recognizable annotations include: Built-in types, such as int, float, str, bool, list, dict, set, tuple, and Any. These also include union and nested combination of basic types. If the type annotation is not recognizable. Unrecognizable annotations includes custom types, such as class, function, etc. Note that, combination of recognizable and unrecognizable types is also unrecognizable. If type is recognizable, return True. If not, return False. You are only required to return True or False, without any other text."),
                    ("user", "Type annotation: {annotation}"),
                ])
                response = type_checker.invoke(prompt.format(annotation=param.annotation))
                if response.content.strip() in ["True", "true", "True.", "true."]:
                    annotation = param.annotation
                else:
                    annotation = Any # Jiahang (TODO): is it a good practice? shold we use str?
            else:
                annotation = Any

            # Determine default value
            # If no default, we use `...` indicating a required field
            # Jiahang (TODO, high priority): if data input (argname=_api['data_name'] and argval='data) 
            # is fixed, why not set it to a private one since LLM dont need to predict it?
            if param_name == _api['data_name']:
                default_value = '"data"'
            elif param.default is not inspect.Signature.empty:
                # Jiahang (TODO): it seems that not all basic types are supported by openai,
                # even though they are supported by pydantic.
                basic_types = [int, float, bool, list, dict, set, tuple, NoneType]  
                if param.default in \
                    [float("inf"), float("-inf"), float("nan"), float("-nan")]:
                    default_value = f'float("{param.default}")'
                elif type(param.default) in basic_types:
                    default_value = param.default
                else:
                    # Jiahang (TODO): str() here is to avoid type error of escape_str.
                    # it looks good for now. 
                    default_value = f'"{escape_str(str(param.default))}"'
            else:
                default_value = ...  # No default means required

            # Determine field name and alias
            # Jiahang (TODO): how to handle alias? it now has bugs. there are some 
            # warnings of pydantic when internal fields are shadowed, such as 'copy' arg.
            field_name = param_name
            alias = None
            # if param_name in base_attributes:
            #     alias_name = param_name + "_param"
            #     alias = param_name
            #     field_name = alias_name
            
            if param_name == _api['data_name']:
                # special hack, where data is fixed, and LLM only needs to predict str "data"
                # Jiahang (TODO): if data arg is fixed, why not set it to a prviate one 
                # since LLM dont need to predict it?
                original_annotation = None
            elif param.annotation is not inspect.Signature.empty:
                original_annotation = param.annotation
            else:
                original_annotation = None
            # Prepare field kwargs
            field_kwargs = {
                "name": field_name,
                "description": description, 
                "annotation": annotation,
                "default": default_value, 
                "original_annotation": original_annotation,
                "alias": alias,
            }

            fields.append(field_kwargs)

        api_data = {
            "name": api_name,
            "model_name": get_data_model_name(api_name),
            "description": doc,
            "fields": fields,
            "products": _api['products'],
            "data_name": _api['data_name'],
        }
        
        api_data = simplify_desc(api_data, llm)
        api_data = escape_desc(api_data)
        apis.append(api_data)

    env = Environment(
        loader=FileSystemLoader("biochatter/api_agent/data_model_generator")
    )
    template = env.get_template("data_model.jinja")
    codes = template.render(apis=apis)

    return codes
        
if __name__ == "__main__":
    # Jiahang (TODO): provide class-based API
    # Jiahang (TODO, high priority): set up types.
    # Jiahang (TODO, high priority): data_names should have default value as "data"
    # Jiahang (TODO): now data is str type. should other Any type also be str type?
    parser = argparse.ArgumentParser()
    parser.add_argument("--package_name", type=str, required=True)
    parser.add_argument("--api_dict_name", type=str, required=True)
    parser.add_argument("--rerun_whole_file", action="store_true")
    args = parser.parse_args()

    package_name = args.package_name
    api_dict_name = args.api_dict_name
    output_path = get_output_path(package_name, api_dict_name)

    api_dict = importlib.import_module(f"biochatter.api_agent.python.{package_name}.api_dict")
    api_dict = getattr(api_dict, api_dict_name)

    if os.path.exists(output_path) and not args.rerun_whole_file:
        output_module_path = get_output_path(package_name, api_dict_name, as_module=True)
        output_module = importlib.import_module(output_module_path)
        TOOLS_DICT = deepcopy(output_module.TOOLS_DICT)

        # extract api in api_dict that is not in TOOLS_DICT
        additional_apis = {}
        for api_name, api in api_dict.items():
            if api_name not in TOOLS_DICT.keys():
                additional_apis.update({api_name: api})

        with open(output_path, "r") as f:
            codes = f.read()
        codes = remove_tools_dict(codes)

        # data_models, new_codes = apis_to_data_models(additional_apis, need_import=False)
        new_codes = apis_to_data_models_jinja(additional_apis)
        # tools_list = list(TOOLS_DICT.values()) + data_models
        # new_codes = add_tools_dict(new_codes, tools_list)

        codes = codes + "\n\n" + new_codes
        
    else:
        # data_models, codes = apis_to_data_models(api_dict)
        # codes = add_tools_dict(codes, data_models)
        codes = apis_to_data_models_jinja(api_dict)

    
    with open(output_path, "w") as f:
        f.write(codes)

    # Jiahang (TODO): use subprocess is a bad practice. but there is no public api
    # released by black. the so-called internal API is unstable, and this
    # subprocess usage is recommended.

    # code formatted by black.

    subprocess.run(["black", output_path])

    print(f"Data models and codes have been generated and saved to {output_path}.")