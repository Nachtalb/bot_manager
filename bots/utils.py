import inspect


def get_arg_value(arg_name, func, args, kwargs):
    if arg_name in kwargs:
        return kwargs[arg_name]

    # Get the argument index from the function signature
    signature = inspect.signature(func)
    index = list(signature.parameters.keys()).index(arg_name)

    if index < len(args):
        return args[index]
    else:
        return None  # The argument was not provided
