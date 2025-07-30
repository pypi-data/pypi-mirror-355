from collections import deque
from typing import Union, List, Deque

from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.services.youtube.search import SearchSong

logger = get_logger("aurras.core.player.online", log_to_console=False)


class SearchIntegration:
    """
    A class for integrating search functionality with the MPV player.

    Attributes:
        search: SearchSong instance with search queries
        player: The MPVPlayer instance
    """

    def __init__(self, song_input: Union[str, List[str]]):
        """
        Initialize the SearchIntegration class.

        Args:
            song_input: Either a single song as a string or a list of songs to play
        """
        # Normalize input to a list if it's a string
        self.search_queries = (
            [song_input] if isinstance(song_input, str) else song_input
        )
        
    def _prepare_batch(self, song_input: Union[str, List[str]], size: int = 4) -> Deque[str]:
        """
        Prepare a batch of songs for playback.

        Args:
            song_input: Either a single song as a string or a list of songs to play

        Returns:
            A deque containing the prepared batch of songs
        """
        song_batch: Deque[str] = deque(maxlen=size)

        if isinstance(song_input, str):
            song_batch.append(song_input)
