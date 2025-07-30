"""

Liquipedia (MediaWiki) API Wrapper for Rocket League stats

"""

import requests
import time

from typing import Iterator

from .player import Player
from . import constants


class LiquipediaRL:
    """
    A class for interacting with the Liquipedia Rocket League MediaWiki API.

    Handles rate limiting, API requests, and HTML parsing to extract player
    information from region-specific Liquipedia pages.
    """
    
    def __init__(self, app_name: str, app_version: str, 
                 website: str, email: str) -> None:
        """
        Set up the API client with a user-agent required by Liquipedia.

        @params:
        - app_name: str -> Name of your application.
        - app_version: str -> Version of your application.
        - website: str -> Website or homepage of your application.
        - email: str -> Contact email address.

        @returns: 
        - None
        """
        # User agent format is Liquipedia TOS requirement
        user_agent = f'{app_name}/{app_version} ({website}; {email})'
        self._headers = {
            'User-Agent': user_agent, 
            'Accept-Encoding': 'gzip'  # Liquipedia TOS asks for this
        }
        self._last_request_times = {}

    def _get(self, params: dict) -> dict:
        """
        Send a GET request to the Liquipedia API with rate limiting.

        @params:
        - params: dict -> API parameters to include in the request.

        @returns: 
        - dict: JSON response from the API.
        """
        # Add the custom parameters to the default parameters
        params = constants.DEFAULT_PARAMS | params

        # Determine action type and rate limit
        action = params['action']
        if action not in constants.RATE_SECONDS:
            action = 'default'
        # 30 seconds if action is 'parse' else 2 seconds
        wait_time = constants.RATE_SECONDS[action]
        now = time.time()

        # Check last request time for this action
        last_time = self._last_request_times.get(action)
        if last_time is not None:  # Check it's not the first call
            elapsed = now - last_time  # Time since last call
            remaining = wait_time - elapsed  # Remaining wait time
            if remaining > 0:  # Is there remaining wait time?
                time.sleep(remaining)

        # Update the last request time
        self._last_request_times[action] = time.time()

        # Make the API request
        response = requests.get(
            constants.BASE_API_URL, 
            params=params, 
            headers=self._headers
        )
        # Raise an HTTPError for bad responses
        response.raise_for_status()
        return response.json()
    
    def get_all_players(self, region: str = 'Oceania', 
                        all: bool = False) -> Iterator[dict]:
        """
        Get player data from Liquipedia for one or all regions.

        @params:
        - region: str -> Region to fetch players from (default is 'Oceania').
            Options: 'Africa', 'Americas', 'Asia', 'Europe', 'Oceania'
        - all: bool -> If True, fetch players from all available regions.

        @yields: 
        - dict: All player records from the respective page
        returning an Iterator[dict] object overall
        """
        if region not in constants.REGIONS_PLAYERPAGES: 
            region = 'Oceania'
        regions = [region.title().strip()]
        if all: 
            regions = [k for k in constants.REGIONS_PLAYERPAGES]
        for region in regions:
            # Make the API call
            _json = self._get({
                'action': 'parse',
                'page': constants.REGIONS_PLAYERPAGES[region]
            })
            records = Player.get_all_players(region, _json)
            yield records
    
    def get_player(self, player: str) -> dict:
        """
        Parses a Liquipedia player page and extracts detailed information.

        @params:
        - player: str -> Name of the player (e.g., 'SquishyMuffinz')

        @returns:
        - dict: Extracted player data
        """
        _json = self._get({'action': 'parse', 'page': player})
        player = Player(_json)
        return player.get_player_data()

        
        
