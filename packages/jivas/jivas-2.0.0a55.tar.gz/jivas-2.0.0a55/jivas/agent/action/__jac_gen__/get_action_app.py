from __future__ import annotations
from jaclang import *
import typing
from enum import Enum, auto
if typing.TYPE_CHECKING:
    import os
else:
    os, = jac_import('os', 'py')
if typing.TYPE_CHECKING:
    import yaml
else:
    yaml, = jac_import('yaml', 'py')
if typing.TYPE_CHECKING:
    import logging
else:
    logging, = jac_import('logging', 'py')
if typing.TYPE_CHECKING:
    import traceback
else:
    traceback, = jac_import('traceback', 'py')
if typing.TYPE_CHECKING:
    from logging import Logger
else:
    Logger, = jac_import('logging', 'py', items={'Logger': None})
if typing.TYPE_CHECKING:
    from jivas.agent.core.agent import Agent
else:
    Agent, = jac_import('jivas.agent.core.agent', items={'Agent': None})
if typing.TYPE_CHECKING:
    from jivas.agent.action.action import Action
else:
    Action, = jac_import('jivas.agent.action.action', items={'Action': None})
if typing.TYPE_CHECKING:
    from jivas.agent.action.actions import Actions
else:
    Actions, = jac_import('jivas.agent.action.actions', items={'Actions': None})
if typing.TYPE_CHECKING:
    from interact_graph_walker import interact_graph_walker
else:
    interact_graph_walker, = jac_import('interact_graph_walker', items={'interact_graph_walker': None})

class get_action_app(interact_graph_walker, Walker):
    agent_id: str = field('')
    action: str = field('')
    action_app: str = field('')
    logger: static[Logger] = logging.getLogger(__name__)

    class __specs__(Obj):
        private: static[bool] = False
        excluded: static[list] = JacList(['action_app'])

    @with_entry
    def on_agent(self, here: Agent) -> None:
        self.visit(here.refs().filter(Actions, None))

    @with_entry
    def on_actions(self, here: Actions) -> None:
        if not self.visit(here.refs().filter(Action, None).filter(None, lambda item: item.label == self.action)):
            message = f'Action not found: {self.action}'
            self.logger.error(message)
            Jac.get_context().status = 404
            Jac.report(message)

    @with_entry
    def on_action(self, here: Action) -> None:
        action_path = f"{here._package.get('config', {}).get('path', '')}/app/app.py"
        try:
            if os.path.exists(action_path):
                with open(action_path, 'r') as file:
                    self.action_app = file.read()
            else:
                message = f'Action app file not found: {action_path}'
                self.logger.warning(message)
                Jac.get_context().status = 404
                Jac.report(message)
                return
        except Exception as e:
            message = f'Error reading action app file: {str(e)}'
            self.logger.error(message)
            self.logger.error(traceback.format_exc())
            Jac.get_context().status = 500
            Jac.report(message)
            return
        if self.reporting:
            Jac.report(self.action_app)