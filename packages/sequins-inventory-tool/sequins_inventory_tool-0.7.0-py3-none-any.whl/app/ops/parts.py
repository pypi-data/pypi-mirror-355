"""CLI for interacting with the parts database."""

import logging
import requests
import typer

from app.console import console
from app.constants import ApiPaths, API_KEY_NAME
from app.utils.checks import require_api_endpoint_and_key
from app.utils.datetime_utils import format_utc_to_local
from rich.table import Table
from typing_extensions import Annotated

logger = logging.getLogger(__name__)

parts_app = typer.Typer()


def create_table() -> Table:
    """Create a table for displaying part information."""
    table = Table(title='Parts')
    table.add_column('Part Number', justify='left')
    table.add_column('Lot Number')
    table.add_column('Constituent Lot Numbers')
    table.add_column('Created At')
    return table


def parse_constituent_lot_numbers(value: str) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(',')]


@parts_app.command(name='display')
@require_api_endpoint_and_key()
def display_parts(ctx: typer.Context):
    """Display a table of parts in the database."""

    api_endpoint = ctx.obj['api_endpoint']
    api_key = ctx.obj['api_key']

    parts_url = f'{api_endpoint}{ApiPaths.PARTS}'
    headers = {API_KEY_NAME: api_key}

    page = 1
    size = 50
    parts = []
    while True:
        result = requests.get(
            parts_url,
            headers=headers,
            params={'page': page, 'size': size},
        )
        result.raise_for_status()
        data = result.json()
        items = data.get('items', [])
        parts.extend(items)
        if len(items) < size:
            break
        page += 1

    if not parts:
        console.print('No parts found.')
        raise typer.Exit()

    table = create_table()
    for part in parts:
        table.add_row(
            part['part_number'],
            part['lot_number'],
            ','.join(sorted(part['constituent_lot_numbers'])),
            format_utc_to_local(part['created_at_utc']),
        )
    console.print(table)


@parts_app.command(name='create')
@require_api_endpoint_and_key()
def create_part(
    part_number: Annotated[str, typer.Option(help='Part number')],
    constituent_lot_numbers: Annotated[
        str,
        typer.Option(help='Comma separated list of constituent lot numbers'),
    ],
    ctx: typer.Context,
):
    """Create a part in the database."""
    api_endpoint = ctx.obj['api_endpoint']
    api_key = ctx.obj['api_key']

    if not part_number:
        console.print('Part number is required.')
        raise typer.Exit(code=1)

    if not constituent_lot_numbers:
        console.print('Constituent lot numbers are required.')
        raise typer.Exit(code=1)

    parts_url = f'{api_endpoint}{ApiPaths.PARTS}'
    headers = {API_KEY_NAME: api_key}

    data = {
        'part_number': part_number,
        'constituent_lot_numbers': parse_constituent_lot_numbers(
            constituent_lot_numbers
        ),
    }

    result = requests.post(parts_url, headers=headers, json=data)
    result.raise_for_status()
    part = result.json()

    console.log('Part created successfully.')

    table = create_table()
    table.add_row(
        part['part_number'],
        part['lot_number'],
        ','.join(sorted(part['constituent_lot_numbers'])),
        format_utc_to_local(part['created_at_utc']),
    )
    console.print(table)
