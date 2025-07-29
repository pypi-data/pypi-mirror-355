"""
Descr: Decorator to be used with open web ui local tool calls
"""

# IMPORT STATEMENTS
import logging
import inspect
import functools


STATUS_UPDATE = {
    "data": {
        "description": "<fill_in>", 
        "status": "working", 
        "done": True
    },
    "type": "status",
}

CONFIRM_NOTIFICATION = {
    "type": "notification",
    "data": {
        "type": "success", 
        "content": "User Confirmed Tool Call."
    },
}

CANCEL_NOTIFICATION = {
    "type": "notification",
    "data": {
        "type": "warning", 
        "content": "User Cancelled Tool Call."
    },
}

ABORT_RETURN_MSG = """
User exited tool call operation. 
Try to answer there question if you can.
If you cannot answer the question without a tool call let the user know.
"""

USER_CONFRIM_MESSAGE = """
Data Will Be Leaving Caci Network and needs to be reviewed for anything sensistive.\n This tool is being called with the following arguments.
"""

def parameter_confirm(filter_args=True):
    def inner(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get positional and name arguments of wrapped function into dict
            arg_names = [
                param.name for param in inspect.signature(func).parameters.values()
            ]
            arg_values = list(args)
            all_args = dict(zip(arg_names, arg_values))
            all_args.update(kwargs)

            # Create prety markdown string of arguments
            arg_string = ""
            for name, value in all_args.items():
                if filter_args:
                    if name.startswith("_"):
                        continue
                    if name == "self":
                        continue
                arg_string += f"**{name}:** {value}<br>"

            # Create message dict to surface
            tool_name = func.__name__
            arg_string = f"<center>**TOOL NAME: {tool_name}**</center><br><br>{arg_string}"
            message = {
                "type": "confirmation",
                "data": {
                    "title": USER_CONFRIM_MESSAGE,
                    "message": f"{arg_string}",
                },
            }

            print(all_args)
            # User wrapped functions event call to get confirmation
            make_tool_call = await all_args["__event_call__"](message)

            # Only run wrapped function if user confirms
            if make_tool_call:
                logging.info(f"{tool_name} confirmed by user")
                await all_args["__event_emitter__"](CONFIRM_NOTIFICATION)
                return func(*args, **kwargs)
            else:
                msg = f"{tool_name} skipped by user"
                logging.info(msg)
                STATUS_UPDATE["data"]["description"] = f"{tool_name} skipped by user"
                await all_args['__event_emitter__'](STATUS_UPDATE)
                await all_args["__event_emitter__"](CANCEL_NOTIFICATION)
                return ABORT_RETURN_MSG

        return wrapper

    return inner
