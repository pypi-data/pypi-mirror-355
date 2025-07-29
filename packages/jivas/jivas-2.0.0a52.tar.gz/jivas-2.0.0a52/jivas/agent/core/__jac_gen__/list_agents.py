from __future__ import annotations
from jaclang import *
import typing
from enum import Enum, auto
if typing.TYPE_CHECKING:
    from jivas.agent.core.agent_graph_walker import agent_graph_walker
else:
    agent_graph_walker, = jac_import('jivas.agent.core.agent_graph_walker', items={'agent_graph_walker': None})
if typing.TYPE_CHECKING:
    from jivas.agent.core.app import App
else:
    App, = jac_import('jivas.agent.core.app', items={'App': None})
if typing.TYPE_CHECKING:
    from jivas.agent.core.agents import Agents
else:
    Agents, = jac_import('jivas.agent.core.agents', items={'Agents': None})

class list_agents(agent_graph_walker, Walker):

    class __specs__(Obj):
        private: static[bool] = False
        excluded: static[list] = JacList(['agent_id'])

    @with_entry
    def on_agents(self, here: Agents) -> None:
        if (agents := here.get_all()):
            for agent in agents:
                Jac.report(agent.export())