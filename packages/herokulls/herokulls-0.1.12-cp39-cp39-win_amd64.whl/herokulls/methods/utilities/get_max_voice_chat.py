import psutil

from ...scaffold import Scaffold


class GetMaxVoiceChat(Scaffold):
    @staticmethod
    def get_max_voice_chat(consumption=5):
        """Get the max number of group calls that can be started

        This method get an estimated number of max group calls

        Parameters:
            consumption (``int``, **optional**):
                Estimated herokulls consumption of Core x Single Group Call

        Returns:
            ``int`` - Max number of group calls can be started

        Example:
            .. code-block:: python
                :emphasize-lines: 5

                from herokulls import Client
                from herokulls import idle
                ...
                app = Client(client)
                app.get_max_voice_chat()
                app.run()

        """
        core_count = psutil.cpu_count()
        return int((100 / consumption) * core_count)
