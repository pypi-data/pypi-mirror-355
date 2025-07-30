import re
from types import ModuleType
from typing import Callable
from ._python_interpreter import evaluate_python_code

def run_codes(code: str, state: dict[str, object]):
    """
    Run codes

    Parameters
    -----------
    code : str
        A single valid code snippet as a string.
    state: dict[str, object]
        A dictionary of variables to be used in the code snippet. E.g. {'sc': sc, 'adata': adata}
    """
    
    try:
        # Jiahang (TODO): remove str() here. may be a problem without str().
        results = evaluate_python_code(code, state=state)[0]
    except Exception as e:
        return f"ERROR: {str(e)}", e
    return results, None


def get_data_model_name(api_name: str) -> str:
    """Get the internal name of an API.

    This apition takes a module and an API, and returns the internal name of the
    API.
    """

    api_name = ''.join(_name.capitalize() for _name in re.findall(r'[a-zA-Z]+', api_name))
    return api_name