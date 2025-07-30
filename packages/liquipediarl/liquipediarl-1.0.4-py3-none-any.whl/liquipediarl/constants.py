
TOS: str = 'https://liquipedia.net/api-terms-of-use'
RATE_SECONDS: dict = {
    'default': 2, 
    'parse': 30
}

BASE_API_URL: str = 'https://liquipedia.net/rocketleague/api.php?'
BASE_PAGE_URL: str = 'https://liquipedia.net/rocketleague/'
BASE_IMAGE_URL: str = 'https://liquipedia.net'

DEFAULT_PARAMS: dict = {
    'action': 'query',
    'format': 'json',
    'curtimestamp': 1
}

REGIONS_PLAYERPAGES: dict = {
    'Africa': 'Portal:Players/Africa',
    'Americas': 'Portal:Players/Americas',
    'Asia': 'Portal:Players/Asia',
    'Europe': 'Portal:Players/Europe',
    'Oceania': 'Portal:Players/Oceania'
}