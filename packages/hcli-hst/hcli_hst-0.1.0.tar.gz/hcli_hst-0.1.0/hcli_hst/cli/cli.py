import json
import io
import service
import logger

from typing import Optional, Dict, Callable, List

logging = logger.Logger()
logging.setLevel(logger.INFO)


class CLI:
    def __init__(self, commands: List[str], inputstream: Optional[io.BytesIO] = None):
        self.commands = commands
        self.inputstream = inputstream
        self.service = service.Service()
        self.handlers: Dict[str, Callable] = {
            'agent': self._handle_agent,
            'agents': self._handle_agents,
            'ships': self._handle_ships,
            'systems': self._handle_systems,
            'server': self._handle_server,
            'contracts': self._handle_contracts
        }

    def execute(self) -> Optional[io.BytesIO]:
        if len(self.commands) == 1 and self.inputstream:
            response = self.service.chat(self.inputstream)
            return io.BytesIO(response.encode('utf-8'))

        if len(self.commands) > 1 and self.commands[1] in self.handlers:
            return self.handlers[self.commands[1]]()

        return None

    def _handle_agent(self) -> None:
        if len(self.commands) == 2:
            return io.BytesIO(self.service.agent())
        if len(self.commands) == 3:
            return io.BytesIO(self.service.agent(self.commands[2]))

    def _handle_agents(self) -> None:
        return io.BytesIO(self.service.agents())

    def _handle_ships(self) -> None:
        if len(self.commands) == 2:
            return io.BytesIO(self.service.ships())
        if len(self.commands) == 3:
                return io.BytesIO(self.service.ships(self.commands[2]))

    def _handle_systems(self) -> None:
        if len(self.commands) == 2:
            return io.BytesIO(self.service.systems())
        if len(self.commands) == 3:
                return io.BytesIO(self.service.systems(self.commands[2]))

    def _handle_server(self) -> None:
        return io.BytesIO(self.service.server())

    def _handle_contracts(self) -> None:
        if len(self.commands) == 2:
            return io.BytesIO(self.service.contracts())
        if len(self.commands) == 3:
            return io.BytesIO(self.service.contracts(self.commands[2]))
        if len(self.commands) == 4:
            if self.commands[2] == 'accept':
                return io.BytesIO(self.service.contracts_accept(self.commands[3]))
