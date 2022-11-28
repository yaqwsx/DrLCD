import click
from typing import Optional, Tuple

class Resolution(click.ParamType):
    """
    A CLI argument type for overriding section parameters. Basically a semicolon
    separated list of `key: value` pairs. The first word might omit the key; in
    that case "type" key is used.
    """
    name = "resolution"

    def convert(self, value: str, param: Optional[click.Parameter], ctx: click.Context) -> Tuple[int, int]:
        if len(value.strip()) == 0:
            self.fail(f"{value} is not a valid argument specification",
                param, ctx)
        splitted = value.split("x")
        if len(splitted) != 2:
            self.fail("Resolution needs to have two parts separated by 'x'")
        try:
            return tuple([int(x) for x in splitted])
        except ValueError as e:
            self.fail("Invalid number specified")
