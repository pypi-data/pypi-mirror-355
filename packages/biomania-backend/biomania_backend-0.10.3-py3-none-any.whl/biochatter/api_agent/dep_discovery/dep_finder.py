import logging
logger = logging.getLogger(__name__)
import os
import importlib
import networkx as nx
import libcst as cst
import json

from .utils import State, build_API_calling, Knockoff, CodeHistory
from biochatter.api_agent.base.utils import run_codes

# Jiahang (TODO): logs are too messy. developers may find it hard to debug according to logs.
# Jiahang (TODO): knockoff error for dependency discovery and real errors, especially errors of provided codes, are mixing.
# Jiahang (TODO): incremental dependency discovery.
# Jiahang (TODO): provide command line interface.
# Jiahang (TODO): is it necessary to have json output? what is python dict which is more 
# versatile? should we consider transferability of graph structure output?
class DependencyFinder:
    MAX_CNT = 3
    SEP_LINE = "-" * 40

    def __init__(self, 
                 package_name: str,
                 api_sel: str | list[int], 
                 debug: bool = False):
        
        api_chains = importlib.import_module(f"biochatter.api_agent.python.{package_name}.api_chains")
        api_chains = api_chains.DATA
        api_dict = importlib.import_module(f"biochatter.api_agent.python.{package_name}.api_dict")
        api_dict = getattr(api_dict, 'FULL_API_DICT')
        self.state = State(
            importlib.import_module(f"biochatter.api_agent.python.{package_name}.info_hub").PKGS,
            importlib.import_module(f"biochatter.api_agent.python.{package_name}.info_hub").DATA
        )
        self.result_dir = f'biochatter/api_agent/python/{package_name}'

        if api_sel == 'all':
            api_sel = list(api_chains.keys())

        self.api_dict = api_dict
        self.api_chains = api_chains
        self.api_sel = api_sel
        self.debug = debug

        self.code_history = CodeHistory()

    def clear(self):
        self.code_history.clear()

    def find_obj_dep_for_each_chain(self, api_chain: list):
        num_api = len(api_chain)
        res_api_chain = []
        all_dep_prod = []
        self.state.reset_state()

        res_api_chain.append(api_chain[0])

        for dep_idx in range(num_api-1):
            dep_api = api_chain[dep_idx] # the dependent api
            target_api = api_chain[dep_idx + 1] # the next api

            # Jiahang (TODO): this build api calling is also used in execution graph forward
            # pass. we should unify them.
            dep_api_call = build_API_calling(dep_api)
            self.code_history.clear()
            self.code_history.add_code(dep_api_call)
            
            # Jiahang (TODO): if State is used by other modules, arg type of run_codes would become `State` instead of `dict`.
            # then usage of run_codes should be revised.
            output, error = run_codes(self.code_history.code_history, state=self.state.state)
            if isinstance(error, Exception):
                logger.info(f"Program failed in initial calling: {output}\n"
                            f"Codes:\n{self.code_history.code_history}")
                return None, False
            
            dep_prod = dep_api['products']
            all_dep_prod.extend(dep_prod)

            """Key: discover unitary dependency of each target API on products produced by the all dependent(previous) API"""
            knockoff_runner = Knockoff(all_dep_prod, target_api, self.state)
            nec_prod = knockoff_runner.run_unitary()

            target_api['dependencies_obj'] = nec_prod
            res_api_chain.append(target_api)

        return res_api_chain, True
    
    def find_api_dep_for_each_chain(self, res_api_chain: list):
        num_api = len(res_api_chain)
        _res_api_chain = res_api_chain.copy()

        for cur_idx in range(1, num_api):
            cur_api: dict = res_api_chain[cur_idx]
            cur_dependencies = cur_api.pop('dependencies_obj')
            cur_dependencies_api = {}
            for dep_idx in range(cur_idx):
                dep_api = res_api_chain[dep_idx]
                dep_products = dep_api['products']
                consumed_prod = list(set(cur_dependencies).intersection(set(dep_products)))
                if consumed_prod: # has API dependency
                    cur_dependencies_api[dep_api['api']] = consumed_prod
            cur_api['dependencies'] = cur_dependencies_api
            _res_api_chain[cur_idx] = cur_api # this line is indeed unnecessary, but still used here.

        print(DependencyFinder.SEP_LINE)

        res_api_chain = _res_api_chain
        return res_api_chain
    
    def parse_codes(self, codes: str) -> dict:
        code_lines = [line.strip() for line in codes.split('\n')]
        code_lines = [line for line in code_lines if line]

        results = []

        # Find the function call
        class FunctionCallVisitor(cst.CSTVisitor):
            def __init__(self):
                self.func_name = None
                self.args = {}
                self.arg_types = {}
            
            def visit_Call(self, node: cst.Call):
                # Get function name
                if isinstance(node.func, cst.Name):
                    self.func_name = node.func.value
                elif isinstance(node.func, cst.Attribute):
                    parts = []
                    current = node.func
                    while isinstance(current, cst.Attribute):
                        parts.append(current.attr.value)
                        current = current.value
                    if isinstance(current, cst.Name):
                        parts.append(current.value)
                    self.func_name = ".".join(reversed(parts))
                
                # Get arguments
                for arg in node.args:
                    if arg.keyword:
                        # Determine argument type
                        if isinstance(arg.value, cst.Name):
                            self.arg_types[arg.keyword.value] = "object"
                        elif isinstance(arg.value, cst.Integer):
                            self.arg_types[arg.keyword.value] = "int"
                        elif isinstance(arg.value, cst.Float):
                            self.arg_types[arg.keyword.value] = "float"
                        elif isinstance(arg.value, cst.SimpleString):
                            self.arg_types[arg.keyword.value] = "str"
                        elif isinstance(arg.value, cst.List):
                            self.arg_types[arg.keyword.value] = "list"
                        elif isinstance(arg.value, cst.Tuple):
                            self.arg_types[arg.keyword.value] = "tuple"
                        elif isinstance(arg.value, cst.Dict):
                            self.arg_types[arg.keyword.value] = "dict"
                        elif isinstance(arg.value, cst.Set):
                            self.arg_types[arg.keyword.value] = "set"
                        elif arg.value.value in ['True', 'False']:
                            self.arg_types[arg.keyword.value] = "bool"
                        else:
                            self.arg_types[arg.keyword.value] = "object"
                        
                        temp_module = cst.Module(body=[])

                        # Jiahang (TODO): we should note how we deal with str type and 
                        # name type. 
                        # 1. name type: data, represented by "data" with type "object".
                        # 2. str type: "data", represented by "'data'" with type "str".
                        # for the sake of simplicity, we represent str type as "data" rather
                        # than "'data'" to avoid processing string of string issue.
                        # be noted that it's reasonable to have name and str type the same representation.
                        # because LLM actually predicts string representation of a name, rather than the actual variable represented by the name.
                        # so essentially, name and str are both str. 
                        # to help differentiate name and str, we tag them with type annotations.
                        # motivated by these notions, we remove '' and "" from the str type arg value, keeping it the same as name type repr.
                        
                        self.args[arg.keyword.value] = temp_module.code_for_node(arg.value)
                        if self.arg_types[arg.keyword.value] == "str":
                            self.args[arg.keyword.value] = self.args[arg.keyword.value].strip("'").strip('"')

        for code_line in code_lines:
            # Parse the code line using libcst
            module = cst.parse_module(code_line)
            visitor = FunctionCallVisitor()
            module.visit(visitor)
            
            if visitor.func_name:
                results.append({
                    'api': visitor.func_name,
                    'args': visitor.args,
                    'arg_types': visitor.arg_types
                })

        return results
    
    def check_api_validity(self, api_chain: list) -> bool:
        for api in api_chain:
            api_name = api['api']
            if api_name not in self.api_dict:
                logger.info(f"API {api_name} not found.")
                return False
            if self.api_dict[api_name].get('_deprecated', False):
                logger.info(f"API {api_name} is deprecated.")
                return False
        return True

    def add_products(self, parsed_api_chain: list) -> list:
        # import products from pre-compiled API data models
        for idx in range(len(parsed_api_chain)):
            parsed_api_chain[idx]['products'] = self.api_dict[parsed_api_chain[idx]['api']]['products']
            
        return parsed_api_chain

    def find_obj_dep_for_all_chains(self):
        cnt = 0
        res_api_chains = []
        
        for api_chain in [self.api_chains[i] for i in self.api_sel]:
            codes = api_chain['codes']
            parsed_api_chain = self.parse_codes(codes)
            if not self.check_api_validity(parsed_api_chain):
                continue
            parsed_api_chain = self.add_products(parsed_api_chain)
            res_api_chain, success = self.find_obj_dep_for_each_chain(parsed_api_chain)
            if not success:
                continue    
            res_api_chain = self.find_api_dep_for_each_chain(res_api_chain)
            res_api_chains.append(res_api_chain)
            cnt += 1

            if self.debug and cnt > DependencyFinder.MAX_CNT:
                break
        return res_api_chains
    
    def construct_dep_graph(self): # the entry point of the whole workflow

        # Jiahang (TODO, high priority):
        # Here added args is a superset of active args, developers are required to
        # filter out inactive args.
        # In the future, we should figure out a way to do this automatically.
        res_api_chains = self.find_obj_dep_for_all_chains()
        G = nx.DiGraph()
        for api_chain in res_api_chains:
            for api in api_chain:
                _api: dict = api.copy()
                dependencies: dict = _api.pop('dependencies') if 'dependencies' in _api.keys() else {}
                G.add_node(_api['api'], api= _api['api']) # dependencies should not be added
                for dep_api_name, obj_dep in dependencies.items():
                    args = _api['args']
                    arg_types = _api['arg_types']
                    G.add_edge(dep_api_name, _api['api'], 
                               dependencies=obj_dep,
                               args=args,
                               arg_types=arg_types
                            )

        # create a root node
        G.add_node('root', api='root')
        in_degrees = G.in_degree()
        init_nodes = [
            node for node, degree in in_degrees if degree == 0 and node != 'root'
        ]
        for node in init_nodes:
            data_name = self.api_dict[node]['data_name']
            G.add_edge('root', node, 
                       dependencies=['data.X'], 
                       args={data_name: "data"},
                       arg_types={data_name: "object"}
                    )

        return G, res_api_chains
    
    def __call__(self, *args, **kwds):
        G, res_APIs = self.construct_dep_graph()

        os.makedirs(os.path.dirname(self.result_dir), exist_ok=True)
        data_path = os.path.join(self.result_dir, 'raw_dep.json')
        graph_json_path = os.path.join(self.result_dir, 'graph.json')

        logger.warning("Developers are required to filter out inactive args manually for now. "
                       "Automatic active args discovery is under development.")

        if not self.debug:
            with open(data_path, 'w') as f:
                json.dump(res_APIs, f, indent=4)
            logger.info(f"Results saved to {data_path}")

            with open(graph_json_path, 'w') as f:
                json.dump(nx.node_link_data(G, edges='edges'), f, indent=4)
            logger.info(f"Graph json saved to {graph_json_path}")
        
        return G, res_APIs
