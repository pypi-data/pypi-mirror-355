from django import forms
from .widgets import AutocompleteWidget


class AutocompleteField(forms.CharField):
    """Form field that uses the AutocompleteWidget by default."""
    
    def __init__(self, *args, url=None, min_length=2, debounce_delay=300, **kwargs):
        self.url = url
        self.min_length = min_length
        self.debounce_delay = debounce_delay
        
        # Set the widget if not already specified
        if 'widget' not in kwargs:
            kwargs['widget'] = AutocompleteWidget(
                url=url,
                min_length=min_length,
                debounce_delay=debounce_delay
            )
        
        super().__init__(*args, **kwargs)


class ModelAutocompleteField(forms.ModelChoiceField):
    """Model choice field that uses the AutocompleteWidget."""
    
    def __init__(self, queryset, *args, url=None, min_length=2, debounce_delay=300, **kwargs):
        self.url = url
        self.min_length = min_length
        self.debounce_delay = debounce_delay
        
        # Set the widget if not already specified
        if 'widget' not in kwargs:
            kwargs['widget'] = AutocompleteWidget(
                url=url,
                min_length=min_length,
                debounce_delay=debounce_delay
            )
        
        super().__init__(queryset, *args, **kwargs)
    
    def to_python(self, value):
        """Convert the autocomplete value to a model instance."""
        if value in self.empty_values:
            return None
        try:
            # Try to get by primary key first
            key = self.to_field_name or 'pk'
            value = self.queryset.get(**{key: value})
        except (ValueError, TypeError, self.queryset.model.DoesNotExist):
            # If that fails, try to get by string representation
            # This allows for more flexible autocomplete implementations
            try:
                for obj in self.queryset:
                    if str(obj) == value:
                        return obj
            except:
                pass
            raise forms.ValidationError(
                self.error_messages['invalid_choice'],
                code='invalid_choice',
                params={'value': value},
            )
        return value