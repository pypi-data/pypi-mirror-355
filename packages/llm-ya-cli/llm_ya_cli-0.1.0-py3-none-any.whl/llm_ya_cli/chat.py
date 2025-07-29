# This file is part of the LLM CLI.
# The LLM CLI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# The LLM CLI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with the LLM CLI. If not, see <https://www.gnu.org/licenses/>.
import asyncio
import sys

import click
import prompt_toolkit

from .utils.config import Config


class ChatCommand(click.Command):
    def __init__(self, config: Config):
        self.config = config
        self._init_click_command()

    def chat(self, msg: str, model_name: str, markdown_output: bool, multi_turn: bool):
        from .utils.llm import AgentCreator, run_stream

        if model_name is None:
            print(
                "Model name is required. Use --model/-m to specify a model. Or edit the config to set the default model."
            )
            sys.exit(1)
        agent = AgentCreator.from_model_name(model_name, self.config)
        if not sys.stdin.isatty():
            msg += sys.stdin.read()
            multi_turn = False
        if multi_turn:
            self.chat_multi_turn(
                agent,
                first_msg=msg,
                markdown_output=markdown_output,
                prefix=self.config.default.assistant_output_prefix,
            )
            return
        if msg == "":
            msg = prompt_toolkit.prompt(self.config.default.user_prompt_prefix)
            if not msg:
                raise click.Abort()

        asyncio.run(
            run_stream(
                msg,
                agent,
                markdown=markdown_output,
                prefix=self.config.default.assistant_output_prefix,
            )
        )

    def _init_click_command(self):
        super().__init__(
            "chat",
            callback=self.chat,
            params=[
                click.Argument(["msg"], default="", required=False, type=click.STRING),
                click.Option(
                    ["--model", "-m", "model_name"],
                    type=click.Choice(self.config.models.keys()),
                    default=self.config.default.model,
                    show_choices=True,
                    show_default=True,
                    help="Specify the model.",
                ),
                click.Option(
                    ["--multi-turn/--no-multi-turn"],
                    type=click.BOOL,
                    default=self.config.default.multi_turn,
                    is_flag=True,
                    show_default=True,
                    help="Whether to multi-turn. If the standard input is not a TTY (e.g., piped input), this option will be set to no-multi-turn.",
                ),
                click.Option(
                    ["--markdown-output/--no-markdown-output"],
                    type=click.BOOL,
                    default=self.config.default.markdown_output,
                    is_flag=True,
                    show_default=True,
                    help="Whether to format the LLM's output as Markdown.",
                ),
            ],
        )

    def chat_multi_turn(
        self,
        agent,
        first_msg: str,
        markdown_output: bool,
        prefix: str,
    ):
        from .utils.llm import run_stream

        messages = []  # The message history. 消息记录。
        if first_msg:
            result = asyncio.run(
                run_stream(first_msg, agent, markdown=markdown_output, prefix=prefix)
            )
            messages = result.all_messages()
        prompt_session = prompt_toolkit.PromptSession()
        try:
            while True:
                msg = prompt_session.prompt(self.config.default.user_prompt_prefix)
                if not msg:
                    raise click.Abort()
                result = asyncio.run(
                    run_stream(
                        msg,
                        agent,
                        markdown=markdown_output,
                        prefix=prefix,
                        message_history=messages,
                    )
                )
                messages = result.all_messages()
        except KeyboardInterrupt:
            raise click.Abort()
