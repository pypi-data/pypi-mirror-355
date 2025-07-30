"""CLI to interact with the box endpoint of the inventory API."""

from __future__ import annotations

import requests
import typer

from app.console import console
from app.constants import API_KEY_NAME, ApiPaths
from app.utils.datetime_utils import format_utc_to_local
from app.utils.checks import require_api_endpoint_and_key
from rich.table import Table
from typing import Optional, List
from typing_extensions import Annotated


box_commands = typer.Typer()

content_commands = typer.Typer()
box_commands.add_typer(content_commands, name='content')


@box_commands.command(name='display', help='Display all boxes in a location')
@require_api_endpoint_and_key()
def display_boxes(
    ctx: typer.Context,
    location_key: Annotated[
        str, typer.Option(help='Location key to filter boxes')
    ] = None,
):
    """Display boxes in a specific location."""

    api_endpoint = ctx.obj['api_endpoint']
    api_key = ctx.obj['api_key']

    box_url = f'{api_endpoint}{ApiPaths.BOXES}'
    headers = {API_KEY_NAME: api_key}
    params = {'location_key': location_key} if location_key else {}

    page = 1
    size = 50
    items = []
    while True:
        response = requests.get(
            box_url,
            headers=headers,
            params={'page': page, 'size': size} | params,
        )
        response.raise_for_status()

        boxes_data = response.json()
        items.extend(boxes_data.get('items', []))
        pages = boxes_data.get('pages', 1)
        if page >= pages:
            break
        page += 1

    if not items:
        console.print('No boxes found for the specified location.')
        raise typer.Exit(code=0)

    table = Table(title='Boxes in Location')
    table.add_column('Name', justify='left')
    table.add_column('ID', justify='left')
    table.add_column('Location Key', justify='left')
    table.add_column('Created At', justify='left')
    table.add_column('Updated At', justify='left')

    for item in items:
        table.add_row(
            item['name'],
            item['_id'],
            item['location_key'],
            format_utc_to_local(item['created_at_utc']),
            format_utc_to_local(item['updated_at_utc']),
        )

    console.print(table)


@box_commands.command(name='create', help='Create a new box')
@require_api_endpoint_and_key()
def create_box(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help='Name of the new box')],
    location_key: Annotated[
        str, typer.Option(help='Location key for the new box')
    ] = None,
):
    """Create a new box."""

    api_endpoint = ctx.obj['api_endpoint']
    api_key = ctx.obj['api_key']

    box_url = f'{api_endpoint}{ApiPaths.BOXES}'
    headers = {API_KEY_NAME: api_key}
    data = {
        'location_key': location_key,
        'name': name,
    }

    response = requests.post(box_url, headers=headers, json=data)
    response.raise_for_status()

    box_data = response.json()
    console.print(f'Created box: {box_data["name"]} (ID: {box_data["_id"]})')


@box_commands.command(name='delete', help='Delete a box by ID')
@require_api_endpoint_and_key()
def delete_box(
    ctx: typer.Context,
    box_id: Annotated[str, typer.Argument(help='ID of the box to delete')],
):
    """Delete a box by its ID."""

    api_endpoint = ctx.obj['api_endpoint']
    api_key = ctx.obj['api_key']

    box_url = f'{api_endpoint}{ApiPaths.BOXES}{box_id}'
    headers = {API_KEY_NAME: api_key}
    response = requests.delete(box_url, headers=headers)
    if response.status_code == 204:
        console.print(f'Successfully deleted box with ID: {box_id}')
    else:
        response.raise_for_status()


@box_commands.command(name='update', help='Update a box by ID')
@require_api_endpoint_and_key()
def update_box(
    ctx: typer.Context,
    box_id: Annotated[str, typer.Argument(help='ID of the box to update')],
    name: Annotated[
        Optional[str], typer.Option(help='New name for the box')
    ] = None,
    location_key: Annotated[
        Optional[str], typer.Option(help='New location key for the box')
    ] = None,
):
    """Update a box by its ID."""

    api_endpoint = ctx.obj['api_endpoint']
    api_key = ctx.obj['api_key']

    box_url = f'{api_endpoint}{ApiPaths.BOXES}{box_id}'
    headers = {API_KEY_NAME: api_key}
    data = {
        'name': name,
        'location_key': location_key,
    }

    response = requests.patch(box_url, headers=headers, json=data)
    response.raise_for_status()

    box_data = response.json()
    console.print(f'Updated box: {box_data["name"]} (ID: {box_data["_id"]})')


@content_commands.command(name='display', help='Display all content in a box')
@require_api_endpoint_and_key()
def display_box_content(
    ctx: typer.Context,
    box_id: Annotated[
        str, typer.Argument(help='ID of the box to display content')
    ],
):
    """Display all content in a specific box."""

    api_endpoint = ctx.obj['api_endpoint']
    api_key = ctx.obj['api_key']

    content_url = f'{api_endpoint}{ApiPaths.BOXES}{box_id}/contents'
    headers = {API_KEY_NAME: api_key}

    response = requests.get(content_url, headers=headers)
    response.raise_for_status()

    content_data = response.json()
    if not content_data:
        console.print('No content found in the specified box.')
        raise typer.Exit(code=0)

    table = Table(title=f'Content in Box {box_id}')
    table.add_column('Part Number', justify='left')
    table.add_column('Lot Number', justify='left')
    table.add_column('Part Key', justify='left')
    table.add_column('Count', justify='left')

    # content_data is a list of dictionaries with keys 'item_key' and 'quantity'
    part_details_url = f'{api_endpoint}{ApiPaths.PARTS}'
    for item in content_data:
        # We need to lookup the part details from the item key
        part_details = requests.get(
            f'{part_details_url}{item["item_key"]}',
            headers=headers,
        )
        part_details.raise_for_status()
        part = part_details.json()
        table.add_row(
            part['part_number'],
            part['lot_number'],
            item['item_key'],
            str(item['quantity']),
        )

    console.print(table)


@content_commands.command(name='set', help='Set the content of a box')
@require_api_endpoint_and_key()
def set_box_content(
    ctx: typer.Context,
    box_id: Annotated[str, typer.Argument(help='ID of the box to set content')],
    content: Annotated[
        List[str],
        typer.Option(
            help='Content to set in the box in the format part_number=count'
        ),
    ],
):
    """Set the content of a specific box."""

    api_endpoint = ctx.obj['api_endpoint']
    api_key = ctx.obj['api_key']

    try:
        parsed_content = dict(item.split('=', 1) for item in content)
    except ValueError:
        console.print('Content must be in the format part_number=count')
        raise typer.Exit(code=1)

    content_data = []
    for part_number, count in parsed_content.items():
        try:
            content_data.append(
                {
                    'item_key': part_number,
                    'quantity': int(count),
                }
            )
        except ValueError:
            console.print(f'Invalid count for part {part_number}: {count}')
            raise typer.Exit(code=1)

    if not content_data:
        console.print('No content provided to set in the box.')
        raise typer.Exit(code=1)

    content_url = f'{api_endpoint}{ApiPaths.BOXES}{box_id}/contents'
    headers = {API_KEY_NAME: api_key}

    response = requests.post(
        content_url, headers=headers, json={'contents': content_data}
    )
    response.raise_for_status()

    console.print(f'Successfully set content for box ID: {box_id}')


@content_commands.command(name='update', help='Update the content of a box')
@require_api_endpoint_and_key()
def update_box_content(
    ctx: typer.Context,
    box_id: Annotated[
        str, typer.Argument(help='ID of the box to update content')
    ],
    content: Annotated[
        List[str],
        typer.Option(
            help='Content to update in the box in the format part_number=count'
        ),
    ],
):
    """Update the content of a specific box."""

    api_endpoint = ctx.obj['api_endpoint']
    api_key = ctx.obj['api_key']

    try:
        parsed_content = dict(item.split('=', 1) for item in content)
    except ValueError:
        console.print('Content must be in the format part_number=count')
        raise typer.Exit(code=1)

    content_data = []
    for part_number, count in parsed_content.items():
        content_data.append(
            {
                'item_key': part_number,
                'quantity': int(count),
            }
        )

    if not content_data:
        console.print('No content provided to update in the box.')
        raise typer.Exit(code=1)

    content_url = f'{api_endpoint}{ApiPaths.BOXES}{box_id}/contents'
    headers = {API_KEY_NAME: api_key}

    response = requests.patch(
        content_url, headers=headers, json={'contents': content_data}
    )
    response.raise_for_status()

    table = Table(title=f'Updated content for box {box_id}')
    table.add_column('Part Key', justify='left')
    table.add_column('Count', justify='left')

    for item in response.json():
        table.add_row(
            item['item_key'],
            str(item['quantity']),
        )

    console.print(table)
