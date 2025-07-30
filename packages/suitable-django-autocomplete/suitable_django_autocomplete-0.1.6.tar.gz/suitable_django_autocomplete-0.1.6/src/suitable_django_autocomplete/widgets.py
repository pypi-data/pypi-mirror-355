from django import forms
from django.urls import reverse_lazy


class AutocompleteWidget(forms.TextInput):
    """Modern autocomplete widget for Django forms using web components."""
    
    template_name = 'suitable_django_autocomplete/autocomplete.html'
    
    def __init__(self, url=None, attrs=None, min_length=2, debounce_delay=300):
        self.url = url
        self.min_length = min_length
        self.debounce_delay = debounce_delay
        super().__init__(attrs)
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget'].update({
            'url': self.url or reverse_lazy('autocomplete'),
            'min_length': self.min_length,
            'debounce_delay': self.debounce_delay,
        })
        return context
    
    class Media:
        js = ('suitable_django_autocomplete/autocomplete.js',)