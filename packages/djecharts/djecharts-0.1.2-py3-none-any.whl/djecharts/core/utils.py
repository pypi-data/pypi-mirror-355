from functools import lru_cache
import logging

from django.conf import settings


TOOLTIPS_DIR = getattr(settings, "ECHARTS_TOOLTIPS_DIR")
TOOLTIPS_CACHE_SIZE = 100

log = logging.getLogger("djecharts")


class class_property:
    def __init__(self, func):
        self.func = func

    def __get__(self, _, owner):
        return self.func(owner)


@lru_cache(maxsize=TOOLTIPS_CACHE_SIZE)
def get_tooltip(tooltip_name):
    try:
        with open(TOOLTIPS_DIR / f"{tooltip_name}.js") as f:
            # Remove the ';' at the end of the file to avoid
            # error when creating the function in the frontend.
            return f.read().strip("; \n")

    except FileNotFoundError:
        log.exception(f"tooltip file not found: {tooltip_name}.js")
        raise
