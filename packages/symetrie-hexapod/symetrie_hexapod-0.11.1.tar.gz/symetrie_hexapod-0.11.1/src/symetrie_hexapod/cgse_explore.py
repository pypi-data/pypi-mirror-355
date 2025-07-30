__all__ = [
    "show_processes",
]

from egse.process import ps_egrep


def show_processes():
    """Show the lines from the `ps -ef` command that match processes from this package."""
    return ps_egrep("(joran|puna|zonda)_(ui|cs|sim)")
