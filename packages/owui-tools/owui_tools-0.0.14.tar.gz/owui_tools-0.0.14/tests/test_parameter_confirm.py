"""
title: UserInLoop Tool
author: Robert
version: 0.0.1
license: apache
requirements: pydantic, owui_tools
"""

# IMPORT STATEMENTS
import json
import asyncio
from typing import Awaitable, Callable, Optional

from pydantic import BaseModel, Field

from owui_tools import parameter_confirm


class Tools:
    class Valves(BaseModel):
        confirm_params_before_call: bool = Field(
            default=True, 
            description=("Has User Confirm Parameters before tool call")
        )

    class UserValves(BaseModel):
        enable_ui_alerts: bool = Field(
            default=True, 
            description="Enable UI alerts about user choices"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.user_valves = self.UserValves()

    @parameter_confirm(filter_args=True)
    def sentence_creator(
        self,
        person: str,
        action: str,
        object: str,
        __event_emitter__: Callable[[dict], Awaitable[None]],
        __event_call__: Callable[[dict], Awaitable[None]],
        __user__: dict = {},
    ) -> str:
        """
        Creates a sentence for the user
        :param person: A persons name
        :param action: an action a person could perform
        :param object: an item a person could perform an action on
        """
        sentence = f"{person} {action} a {object}"
        return sentence
    

    @parameter_confirm(filter_args=False)
    def joke_creator(
        self,
        person: str,
        action: str,
        object: str,
        __event_emitter__: Callable[[dict], Awaitable[None]],
        __event_call__: Callable[[dict], Awaitable[None]],
        __user__: dict = {},
    ) -> str:
        """
        Creates a joke for the user
        :param person: A persons name
        :param action: an action a person could perform
        :param object: an item a person could perform an action on
        """
        sentence = f"{person} {action} a {object} tripped over a rock"
        return sentence


async def test_print(message):
    await asyncio.sleep(1)
    print(json.dumps(message, indent=4).replace("<br>", "\n"))
    return True


if __name__ == "__main__":
    result = asyncio.run(
        Tools().sentence_creator("a", "b", "c", test_print, test_print)
    )
    print(result)

    result = asyncio.run(
        Tools().joke_creator("a", "b", "c", test_print, test_print)
    )
    print(result)
