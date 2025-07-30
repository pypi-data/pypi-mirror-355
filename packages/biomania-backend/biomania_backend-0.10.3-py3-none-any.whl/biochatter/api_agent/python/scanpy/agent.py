from biochatter.api_agent.base.agent_abc import BaseQueryBuilder, BaseFetcher, BaseInterpreter
from biochatter.llm_connect import Conversation
from biochatter.api_agent.dep_graph import DependencyGraph, ExecutionGraph
from biochatter.api_agent.dep_graph.utils import is_active_dep, retrieve_products, aggregate_deps
from biochatter.api_agent.base.agent_abc import BaseAPI, ArgDefaultChangeVerifier
from .api_hub import TARGET_TOOLS_DICT, TOOLS_DICT
from .info_hub import api_names, dependencies
from .base import ScanpyDependency
from langchain_core.output_parsers import PydanticToolsParser
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel
import networkx as nx
import matplotlib

import json
from queue import Queue
import scanpy
from typing import Any
from tqdm import tqdm
class ScanpyQueryBuilder(BaseQueryBuilder):
    def __init__(self, 
                 conversation: Conversation,
                 verifier: ArgDefaultChangeVerifier | None = None
                 ):
        super().__init__(conversation=conversation)
        self.verifier = verifier
        self.dep_graph = DependencyGraph(api_names=api_names, 
                                         dependencies=dependencies, 
                                         api_class_dict=TOOLS_DICT,
                                         dep_class=ScanpyDependency)
    def build_api_query(
        self,
        question: str,
    ) -> list[ExecutionGraph]:

        tools = list(TARGET_TOOLS_DICT.values())

        api: BaseModel = self._parametrise_api(question, tools)
        execution_graph = self._trace_back(question, api)

        return [execution_graph]
    
    def _parametrise_api(
        self,
        question: str,
        tools: list[BaseAPI | type],
        batch_size: int = 3, # Jiahang (TODO): support parallel batching.
    ):
        # batch over tools
        # Jiahang (TODO): no need for arg prediction for each batch. we can prediction
        # api over all batches, and prediction arguments when the final winner appears.

        # Jiahang (TODO): arg prediction sucks since args too many.
        # 1. arg modification verifier: ask llm whether this arg different from the default 
        # value is a correct modification according to the user query.
        # 2. arg importance scorer: only involve important args to reduce the number of args.
        assert len(tools) > 0, "tools should not be empty"
        tool_class = tools[0]
        if len(tools) == 1:
            llm_with_tools: BaseChatModel = \
                self.conversation.chat.bind_tools([tool_class], 
                                                  tool_choice="required")
            parser = PydanticToolsParser(tools=[tool_class])
            tool = llm_with_tools.invoke(question)
            tool: BaseAPI = parser.invoke(tool)[0]
        
        for i in tqdm(range(1, len(tools), batch_size)):
            batch_tools = tools[i:i+batch_size]
            batch_tools.append(tool_class)
            llm_with_tools: BaseChatModel = self.conversation.chat.bind_tools(batch_tools, tool_choice="required")
            parser = PydanticToolsParser(tools=batch_tools)
            # Jiahang (TODO): I found openai llm n -> 1 and temperature -> 0.0,
            # hindering majority vote and revising incorrect results through multiple trials.
            tools_batch = llm_with_tools.invoke(question)
            tool: BaseAPI = parser.invoke(tools_batch)[0]
            tool_class = tool.__class__

        if tool._api_name != "root":
            if self.verifier is not None:
                tool = self.verifier.verify(tool, question)
            tool.set_products_keys_info()
        
        return tool
    
    def _trace_back(
            self, 
            question: str,
            api: BaseAPI
        ) -> ExecutionGraph:
        execution_graph = ExecutionGraph()
        execution_graph.add_api(api)
        next_api_queue = Queue()
        next_api_queue.put(api)

        while not next_api_queue.empty():
            api = next_api_queue.get()
            for in_dep in self.dep_graph.in_deps(api._api_name):
                if is_active_dep(in_dep, api):
                    # Jiahang (TODO): note that the api (node) names of execution graph is a primary key.
                    # It is worth considering whether multiple predecessors of the same API could be added.
                    # That means, the same API with different arguments may occur in the final API chain.
                    # For now, we only allow a single instance of each API.
                    if in_dep.u_api_name not in execution_graph.nodes:
                        active_predecessor = self.dep_graph.get_api(in_dep.u_api_name)
                        active_predecessor = self._parametrise_api(question, [active_predecessor], batch_size=1) # Jiahang (TODO): batch_size=1 is a hack.
                        execution_graph.add_api(active_predecessor)
                        next_api_queue.put(active_predecessor)
                    execution_graph.add_dep(in_dep)
        return execution_graph
    
class ScanpyFetcher(BaseFetcher):
    def fetch_results(
        self,
        execution_graph: list[ExecutionGraph],
        data: object | None = None, # Jiahang (TODO): we pass a list to follow the interface. Bad practice.
        ax: matplotlib.axes.Axes | None = None,
        retries: int | None = 3,
    ) -> object:
        code_lines = []
        execution_graph: ExecutionGraph = execution_graph[0]
        root = execution_graph.get_api("root")
        root._deps.data = data
        execution_graph.update_api(root)

        # topological sort
        topo_sort = list(nx.topological_sort(execution_graph))
        topo_sort = execution_graph.get_apis(topo_sort)
        for api in topo_sort:
            in_deps = execution_graph.in_deps(api._api_name)
            if len(in_deps) > 0:
                api = aggregate_deps(in_deps, api)
            # Jiahang (TODO, high priority): question="visualize diffusion map embedding of cells which are clustered by leiden algorithm."
            # predict sc.pl.diffmap must set n_comps=2, leading to error.
            # this cannot be prevented by prompts, like
            # "Predict an argument value only when user clearly specifies. Leave arguments as default otherwise."
            # and "n_comps=15".
            # it's weird that the second one cannot work either.
            api.execute(state={'sc': scanpy})
            execution_graph.update_api(api)
            out_deps = execution_graph.out_deps(api._api_name)
            for out_dep in out_deps:
                out_dep = retrieve_products(api, out_dep)
                execution_graph.update_dep(out_dep)
            code_lines.append(api._api_calling)
        print('\n'.join(code_lines)) # Jiahang (TODO): using logger to do the printing.
        return code_lines
    
class ScanpyInterpreter(BaseInterpreter):
    def summarise_results(
        self,
        question: str,
        response: object,
    ) -> str:
        # Jiahang (TODO): no need to summarise the results for Scanpy.
        return response