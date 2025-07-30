"""Inventory tool CLI entry point."""

import logging
import os
import typer

from app.ops.azenta import azenta_app
from app.ops.box import box_commands
from app.ops.database import app as database_app
from app.ops.location import location_commands
from app.ops.parts import parts_app
from app.ops.product_numbering import product_naming_app
from app.ops.users import user_commands

from dotenv import load_dotenv


logger = logging.getLogger(__name__)

load_dotenv('.env')

app = typer.Typer()
app.add_typer(azenta_app, name='azenta')
app.add_typer(box_commands, name='box')
app.add_typer(database_app, name='database')
app.add_typer(location_commands, name='location')
app.add_typer(parts_app, name='part')
app.add_typer(product_naming_app, name='product-numbering')
app.add_typer(user_commands, name='user')


# Callback is called before executing every command, to allow us to set global
# state.
@app.callback()
def global_callback(
    ctx: typer.Context,
    debug: bool = typer.Option(False, '--debug', help='Enable debug logging'),
    api_endpoint=typer.Option(
        os.getenv('API_ENDPOINT', 'https://inventory-api.corp.sequins.bio'),
        '--api-endpoint',
        help='Address of API endpoint.',
    ),
    api_key=typer.Option(
        os.getenv('API_KEY'), '--api-key', help='API key for authentication.'
    ),
    database_server_name=typer.Option(
        os.getenv('DATABASE_SERVER_NAME', ''),
        '--database-server-name',
        help='MongoDB server name',
    ),
    database_name=typer.Option(
        os.getenv('DATABASE_NAME', ''),
        '--database-name',
        help='MongoDB database name.',
    ),
):
    """Global callback to set the logging level."""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    logger.debug(f'API endpoint: {api_endpoint}')
    logger.debug(f'API key: {api_key}')

    ctx.obj = {
        'api_endpoint': api_endpoint,
        'api_key': api_key,
        'database_server_name': database_server_name,
        'database_name': database_name,
    }


if __name__ == '__main__':
    app()
