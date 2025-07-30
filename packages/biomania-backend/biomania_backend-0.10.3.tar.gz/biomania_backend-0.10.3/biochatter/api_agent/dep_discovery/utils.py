import logging
from abc import ABC, abstractmethod
logger = logging.getLogger(__name__)

from biochatter.api_agent.base.utils import run_codes
import importlib
from pydantic import BaseModel

from copy import deepcopy

# Jiahang (TODO): check whether constants are properly set up in API.

# builtin API.
# all args of builtin API are positional args, so no arg name is needed.
BUILTIN = 0

# function calling requiring no first arg name. 
# this is the case for builtin API and some special functions, e.g.
# singledispatch functions.
NO_FIRST_ARG_NAME = 1

API_CALLING = """{api_name}({args})"""

class CodeHistory(BaseModel):
    """
    A class to maintain the history of code snippets.

    Attributes:
    -----------
    code_history : list[str]
        A list to store the history of code snippets.

    Methods:
    --------
    add_code(code: str | list[str]):
        Adds a code snippet or a list of code snippets to the code history.
    """
    internal_code_history: list[str] = []

    @property
    def code_history(self) -> str:
        """
        Python code block version of code history list.

        Returns
        --------
        str
            A python code block including the whole code history.
        """
        return '\n'.join(self.internal_code_history)
    
    def add_code(self, code: str | list[str]):
        """
        Adds code snippets to the code history.

        Parameters
        -----------
        code : str | list[str]
            A single code snippet as a string or a list of code snippets. If a string is provided, the string should be a valid python code block. If a list is provided, each element should be a valid python code block. A valid python code block has no ```python and ```, and lines are separated by \\n.
        """
        if isinstance(code, list): # barely used
            self.internal_code_history.extend(code)
        else:
            self.internal_code_history.append(code)
    
    def clear(self):
        """
        Clear the code history.
        """
        self.internal_code_history = []

    def pop(self):
        """
        Pop the last code snippet from the code history.
        """
        if len(self.internal_code_history) > 0:
            return self.internal_code_history.pop()
        else:
            return None
        
def unify_bool(input_: object, type_: str):
    """
    Convert bool into correct python str format if input_ is bool, else return raw input_.
    """
    if type_ == 'bool':
        if input_ in [True, 'True', 'true']:
            return True
        elif input_ in [False, 'False', 'false']:
            return False
    return input_

# Jiahang (TODO): check if this class is similar to other use cases.
class ArgInfo(ABC):
    """
    Storing basic argument information. For now only name and value.
    """
    def __init__(self, arg_name: str, arg_val: object, arg_type: str):
        super().__init__()
        self.arg_name = arg_name
        self.arg_val = unify_bool(arg_val, arg_type)
        self.arg_type = arg_type

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.arg_name == other.arg_name and self.arg_val == other.arg_val
        return False
    
    def __repr__(self):
        return f"{self.arg_name}:{self.arg_val}"
    
    def __hash__(self):
        arg_val = self.arg_val
        if self.arg_type == "dict": # unhashable
            arg_val = tuple(sorted(arg_val.items()))
        elif self.arg_type == "list": # unhashable
            arg_val = tuple(sorted(arg_val))
        return hash((self.arg_name, arg_val))
    
    def to_py(self, require_arg_name: bool = True):
        """
        Convert the arg info to python code.
        """
        arg_val = self.arg_val
        if self.arg_type == "str":
            arg_val = f"'{arg_val}'"
        if require_arg_name:
            return f"{self.arg_name} = {arg_val}" if arg_val is not None else f"{self.arg_name} = None"
        return f"{arg_val}" if arg_val is not None else "None"

# Jiahang (TODO): this class should be used by other modules, at least all codes using `run_codes`.
# Note that, the concept of state here is different from the state in BaseAPI. This is a bad practice.
# Here, `state` includes `pkgs` and `data`. In BaseAPI, `state` is only `pkgs`.
# We should change `state` concept in BaseAPI to `pkgs`.
class State:
    def __init__(self, pkgs: dict, data: dict):
        self._pkgs = pkgs
        self._data = data
        self._data_names = list(data.keys())
        self.state = {}
        self.reset_state()
        
    def reset_state(self):
        self.state.clear()
        self.state.update(self._pkgs)
        data = deepcopy(self._data)
        self.state.update(data)
    
    @classmethod
    def copy_state(cls, state: "State") -> "State":
        pkgs = state._pkgs
        data = {}
        for name in state._data_names:
            data[name] = deepcopy(state.state[name])
        new_state = cls(pkgs, data)
        return new_state

# Jiahang (TODO): this func is used by other modules. Try to unify them.
def build_API_calling(api: dict) -> str:
    """
    Build the API calling string from the API info.
    """
    api_name = api['api']
    api_args = []

    for idx, (_arg_name, _arg_val) in enumerate(api['args'].items()):
        special = api.get('special', [])
        require_arg_name = True
        if BUILTIN in special:
            require_arg_name = False
        elif NO_FIRST_ARG_NAME in special and idx == 0:
            require_arg_name = False

        api_args.append(
            ArgInfo(
                arg_name=_arg_name, 
                arg_val=_arg_val, 
                arg_type=api['arg_types'][_arg_name]
            ).to_py(require_arg_name)
        )
    api_args_str = ", ".join(api_args)
    api_call = API_CALLING.format(api_name=api_name, args=api_args_str)
    if 'return' in api.keys():
        api_call = f"{api_name} = {api_call}"
    return api_call

def _self_check(func):
    def wrapper(self, *args, **kwargs):
        # Perform the self-check
        assert self.dep_prods is not None and self.state is not None and self.target_api is not None, \
            "At least one of the dep_prods, state and target_api is None. Please preprocess the knockoff class first."
        # If check passes, call the wrapped function
        return func(self, *args, **kwargs)
    return wrapper

class Knockoff:
    """
    The knockoff class is used to generate the knockoff code for a given API.
    The knockoff code is generated by deleting the API and then testing the target API.
    If the target API fails, then the deleted API is necessary.
    """

    def __init__(self, dep_prods: list[str], target_api: dict, state: State):
        self.dep_prods = dep_prods
        self.state = state
        self.target_api = target_api
        self.code_history = CodeHistory()
        self.code_history.clear()

    def clear(self):
        self.dep_prods = None
        self.state = None
        self.target_api = None
        self.code_history.clear()
        
    @_self_check
    def target_api_call(self):
        """
        The target API calling string from the API info.
        """
        return build_API_calling(self.target_api)

    @_self_check
    def get_knockoff(self, dep_prod: str):
        """
        Get knockoff codes for a specific dependency product.
        """
        knockoff = API_CALLING.format(
            api_name='del',
            args=dep_prod
        )
    
        """
        The knockoff calling is indeed 1) delete something, then 2) test target API calling, 
        and see if target calling failed, then the deleted product is necessary.
        However, if the error is raised during the deletion, the knockoff testing is useless.
        Deletion error usually refers to a product is non-existent.
        """
        state = State.copy_state(self.state)
        output, error = run_codes(knockoff, state=state.state)
        return knockoff, output, error
        
    @_self_check
    def run_unitary(self):
        nec_prod = []
        for dep_prod in self.dep_prods: # iterate over each dependency product
            knockoff, output, error = self.get_knockoff(dep_prod)
            if error is not None:
                logger.info(f"Knockoff test failed to built since delete is failed, "
                            f"usually meaning that the product not exists: {dep_prod}.\n"
                            f"Error: {error}\n"
                            f"Output: {output}"
                        )
                continue
            self.code_history.clear()
            self.code_history.add_code([
                knockoff,
                self.target_api_call()
            ])
            state = State.copy_state(self.state)
            output, error = run_codes(self.code_history.code_history, state=state.state)

            if isinstance(error, Exception):
                logger.info(f"Knockoff test on {dep_prod} failed: {output}\n"
                            f"Test: {dep_prod}\n"
                            f"Codes:\n{self.code_history.code_history}")
                nec_prod.append(dep_prod)
                
        return nec_prod