"""Application specfic constants."""

from enum import StrEnum

BASE_PATH = '/api/v1'


class ApiPaths(StrEnum):
    """Enum for the paths of the API."""

    BOXES = f'{BASE_PATH}/box/'
    BLENDS = f'{BASE_PATH}/blend/'
    SEQUINS = f'{BASE_PATH}/sequin/'
    VARIANTS = f'{BASE_PATH}/variant/'
    GROUPS = f'{BASE_PATH}/group/'
    GROUP_LISTS = f'{BASE_PATH}/group_list/'
    LOCATIONS = f'{BASE_PATH}/location/'
    PART_DEFINITIONS = f'{BASE_PATH}/part_definition/'
    TILES = f'{BASE_PATH}/tile/'
    POOLS = f'{BASE_PATH}/pool/'
    PARTS = f'{BASE_PATH}/part/'
    ORDERS = f'{BASE_PATH}/order/'
    USERS = f'{BASE_PATH}/user/'


# The name of our API key header.
API_KEY_NAME = 'X-API-Key'
