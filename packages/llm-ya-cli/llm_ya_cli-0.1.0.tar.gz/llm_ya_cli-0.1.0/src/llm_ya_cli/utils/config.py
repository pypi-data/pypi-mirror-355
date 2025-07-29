# This file is part of the LLM CLI.
# The LLM CLI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# The LLM CLI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with the LLM CLI. If not, see <https://www.gnu.org/licenses/>.
import os
import sys
from typing import Dict, Literal, Optional

import platformdirs
from pydantic import BaseModel, ValidationError, model_validator


class DefaultConfig(BaseModel):
    model: Optional[str] = None
    markdown_output: bool = True
    multi_turn: bool = True
    user_prompt_prefix: str = "User: "
    assistant_output_prefix: str = "Assistant: "


class Provider(BaseModel):
    type: Literal["openai"] = "openai"
    base_url: str
    api_key_type: Literal["key", "env"] = "key"
    api_key: str


class Model(BaseModel):
    provider: str
    model_name: str


class Config(BaseModel):
    default: DefaultConfig = DefaultConfig()
    providers: Dict[str, Provider]
    models: Dict[str, Model]

    @model_validator(mode="after")
    def check_default_model_exists(self) -> "Config":
        if self.default.model is None:
            return self
        if self.default.model not in self.models.keys():
            raise ValueError(
                "default model {model} is not defined".format(model=self.default.model)
            )
        return self

    @model_validator(mode="after")
    def check_models_providers_exists(self) -> "Config":
        providers = self.providers.keys()
        for model, conf in self.models.items():
            if conf.provider not in providers:
                raise ValueError(
                    "the provider {provider} of model {model} is not defined".format(
                        provider=conf.provider, model=model
                    )
                )
        return self


def load_config() -> Config:
    dirs = platformdirs.PlatformDirs(appname="llm-cli", appauthor=False)
    config_path = os.path.join(dirs.user_config_dir, "config.toml")

    if not os.path.exists(config_path):
        print("No config file {fp}".format(fp=config_path))
        sys.exit(1)

    if not os.access(config_path, os.R_OK):
        print("Cannot read config file {fp}".format(fp=config_path))
        sys.exit(1)

    with open(config_path, "rb") as f:
        try:
            if (
                sys.version_info.minor < 11
            ):  # tomllib is added in version 3.11. tomllib 在版本 3.11 加入。
                import tomli  # type: ignore

                try:
                    p = tomli.load(f)
                except tomli.TOMLDecodeError as e:
                    print(
                        "Invalid config TOML: {fp}\nError: {e}".format(
                            fp=config_path, e=e
                        )
                    )
                    sys.exit(1)
            else:
                import tomllib

                try:
                    p = tomllib.load(f)
                except tomllib.TOMLDecodeError as e:
                    print(
                        "Invalid config TOML: {fp}\nError: {e}".format(
                            fp=config_path, e=e
                        )
                    )
                    sys.exit(1)
            return Config(**p)
        except ValidationError as e:
            print("Invalid config file {fp}.\nError: {e}".format(fp=config_path, e=e))
            sys.exit(1)
