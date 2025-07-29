import asyncio

from ...exceptions import HerokullsAlreadyRunning
from ...scaffold import Scaffold


class Start(Scaffold):
    async def start(self):
        """Start the client.

        This method start and then connects to the NodeJS core.

        Raises:
            herkullsAlreadyRunning: In case you try
                to start an already started client.

        Example:
            .. code-block:: python
                :emphasize-lines: 5

                from herokulls import Client
                from herokulls import idle
                ...
                app = Client(client)
                app.start()

                ...  # Call API methods

                idle()
        """
        if not self._is_running:
            self._is_running = True
            loop = asyncio.get_running_loop()
            self._wait_until_run = loop.create_future()
            self._env_checker.check_environment()
            await self._init_mtproto()
            self._handle_mtproto()
            await self._start_binding()
        else:
            raise HerokullsAlreadyRunning()
