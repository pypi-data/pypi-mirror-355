"""Modern Django autocomplete widget using web components."""

__version__ = "0.1.0"

from .widgets import AutocompleteWidget
from .fields import AutocompleteField, ModelAutocompleteField
from .views import AutocompleteView, ModelAutocompleteView, SimpleAutocompleteView

__all__ = [
    "AutocompleteWidget",
    "AutocompleteField", 
    "ModelAutocompleteField",
    "AutocompleteView",
    "ModelAutocompleteView",
    "SimpleAutocompleteView",
]