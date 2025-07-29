# This file is part of the LLM CLI.
# The LLM CLI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# The LLM CLI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with the LLM CLI. If not, see <https://www.gnu.org/licenses/>.
import click

from .chat import ChatCommand
from .utils.config import load_config

config = load_config()

cli = click.Group()
cli.add_command(ChatCommand(config))

if __name__ == "__main__":
    cli()
