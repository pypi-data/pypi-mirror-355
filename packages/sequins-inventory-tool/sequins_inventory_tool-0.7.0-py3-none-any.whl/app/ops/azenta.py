"""CLI to interact with Azenta parts and shipment data."""

import logging
import pandas
import requests
import typer

from app.console import console
from app.constants import ApiPaths, API_KEY_NAME
from app.utils.checks import require_api_endpoint_and_key
from typing_extensions import Annotated

logger = logging.getLogger(__name__)

azenta_app = typer.Typer()


@azenta_app.command(name='upload-stock')
@require_api_endpoint_and_key()
def upload_stock(
    sample_search_csv: Annotated[
        str, typer.Argument(help='Path to the sample search CSV file')
    ],
    ctx: typer.Context,
):
    """Upload a sample search csv of stock data to the database."""
    logger.info(f'Uploading stock data from {sample_search_csv}...')

    columns = {
        'Originating ID - UDF': 'Originating_ID',
        'Sample Status - UDF': 'status',
        'Division - UDF': 'location',
        'Received Date - UDF': 'received_date',
    }
    # Load the file
    data = pandas.read_csv(sample_search_csv, usecols=columns.keys())
    data.rename(columns=columns, inplace=True)
    data.columns = data.columns.str.replace(' ', '_').str.lower()
    logger.debug(f'Columns: {data.columns}')

    # Get a list of all the parts, the lot number and the counts for each.
    # We need to check if parts exist in the database.
    location_part_and_lot_counts = {}
    for row in data.itertuples():
        parts_and_lot = row.originating_id.split()
        part_number = parts_and_lot[0].upper().strip()
        lot_number = parts_and_lot[1].upper().strip()
        if row.location not in location_part_and_lot_counts:
            location_part_and_lot_counts[row.location] = {}
        if part_number not in location_part_and_lot_counts[row.location]:
            location_part_and_lot_counts[row.location][part_number] = {}
        if (
            lot_number
            not in location_part_and_lot_counts[row.location][part_number]
        ):
            location_part_and_lot_counts[row.location][part_number][
                lot_number
            ] = {'count': 0}
        location_part_and_lot_counts[row.location][part_number][lot_number][
            'count'
        ] += 1

    logger.debug(f'Part and lot counts: {location_part_and_lot_counts}')

    api_endpoint = ctx.obj['api_endpoint']
    api_key = ctx.obj['api_key']

    # For each location, check if the box exists in the database.
    for location in location_part_and_lot_counts.keys():
        result = requests.get(
            f'{api_endpoint}{ApiPaths.BOXES}',
            headers={API_KEY_NAME: api_key},
            params={'box_name': location},
        )
        result.raise_for_status()
        items = result.json()['items']

        if not items:
            console.log(f'Box {location} not found')
            raise typer.Exit(code=1)

        if len(items) > 1:
            console.log(f'Box {location} found more than one box')
            raise typer.Exit(code=1)

        location_part_and_lot_counts[location]['box_id'] = items[0]['_id']

    # For each part and lot, check if the part exists in the database.
    for location, parts in location_part_and_lot_counts.items():
        for part, lots in parts.items():
            # Don't forget we've saved the box_id in the location so we can
            # update the box later.
            if part == 'box_id':
                continue

            for lot_number in lots.keys():
                result = requests.get(
                    f'{api_endpoint}{ApiPaths.PARTS}',
                    headers={API_KEY_NAME: api_key},
                    params={'part_number': part},
                )
                result.raise_for_status()
                items = result.json()['items']

                if not items:
                    console.log(f'Part {part} not found')
                    raise typer.Exit(code=1)

                part_item = next(
                    (
                        item
                        for item in items
                        if item['lot_number'] == lot_number
                    ),
                    None,
                )

                # Otherwise might be in the lot constituents.
                if not part_item:
                    for item in items:
                        if (
                            'constituent_lot_numbers' in item
                            and lot_number in item['constituent_lot_numbers']
                        ):
                            part_item = item
                            break

                if not part_item:
                    console.log(f'Part {part} with lot {lot_number} not found')
                    raise typer.Exit(code=1)

                location_part_and_lot_counts[location][part][lot_number][
                    '_id'
                ] = part_item['_id']

    # For each location, set the box count with the parts and counts.
    for location, parts in location_part_and_lot_counts.items():
        box_id = parts.pop('box_id')
        contents = []
        for lots in parts.values():
            for count in lots.values():
                contents.append(
                    {
                        'item_key': count['_id'],
                        'quantity': count['count'],
                    }
                )

        # Posting the contents overwrites the existing contents.
        requests.post(
            f'{api_endpoint}{ApiPaths.BOXES}{box_id}/contents',
            headers={API_KEY_NAME: api_key},
            json={'contents': contents},
        )

    console.log(f'Uploaded stock data from {sample_search_csv} to {location}')
    console.log(f'Contents: {contents}')
