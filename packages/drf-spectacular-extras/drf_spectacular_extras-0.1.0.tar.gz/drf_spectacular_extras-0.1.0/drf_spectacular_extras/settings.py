from contextlib import contextmanager
from typing import Any

from django.conf import settings
from rest_framework.settings import APISettings, perform_import

SPECTACULAR_EXTRAS_DEFAULTS: dict[str, Any] = {
    # Dictionary of general configuration to pass to the Scalar.createApiReference('#dom', { ... })
    # https://github.com/scalar/scalar/blob/main/documentation/configuration.md
    # The settings are serialized with json.dumps(). If you need customized JS, use a
    # string instead. The string must then contain valid JS and is passed unchanged.
    "SCALAR_UI_SETTINGS": {},
    # CDNs for scalar dist.
    "SCALAR_DIST": "https://cdn.jsdelivr.net/npm/@scalar/api-reference@latest",
}

IMPORT_STRINGS = []


class SpectacularExtrasSettings(APISettings):
    _original_settings: dict[str, Any] = {}

    def apply_patches(self, patches):
        for attr, val in patches.items():
            if attr.startswith("SERVE_") or attr == "DEFAULT_GENERATOR_CLASS":
                raise AttributeError(
                    f"{attr} not allowed in custom_settings. use dedicated parameter instead."
                )
            if attr in self.import_strings:
                val = perform_import(val, attr)  # noqa
            # load and store original value, then override __dict__ entry
            self._original_settings[attr] = getattr(self, attr)
            setattr(self, attr, val)

    def clear_patches(self):
        for attr, orig_val in self._original_settings.items():
            setattr(self, attr, orig_val)
        self._original_settings = {}


spectacular_extras_settings = SpectacularExtrasSettings(
    user_settings=getattr(settings, "SPECTACULAR_EXTRAS_SETTINGS", {}),  # type: ignore
    defaults=SPECTACULAR_EXTRAS_DEFAULTS,  # type: ignore
    import_strings=IMPORT_STRINGS,
)


@contextmanager
def patched_settings(patches):
    """temporarily patch the global spectacular settings (or do nothing)"""
    if not patches:
        yield
    else:
        try:
            spectacular_extras_settings.apply_patches(patches)
            yield
        finally:
            spectacular_extras_settings.clear_patches()
