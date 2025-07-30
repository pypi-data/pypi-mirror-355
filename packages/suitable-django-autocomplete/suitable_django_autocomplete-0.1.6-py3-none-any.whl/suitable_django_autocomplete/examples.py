"""
Example implementations of autocomplete views and forms.
These can be used as references or directly in your project.
"""

from django import forms
from django.contrib.auth.models import User
from .views import ModelAutocompleteView, SimpleAutocompleteView
from .fields import AutocompleteField, ModelAutocompleteField
from .widgets import AutocompleteWidget


# Example Views

class UserAutocompleteView(ModelAutocompleteView):
    """Example autocomplete view for Django User model."""
    model = User
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def format_result(self, obj):
        """Return user display format."""
        if obj.get_full_name():
            return f"{obj.username} ({obj.get_full_name()})"
        return obj.username


class FruitAutocompleteView(SimpleAutocompleteView):
    """Example static autocomplete view."""
    choices = [
        'Apple', 'Banana', 'Cherry', 'Date', 'Elderberry',
        'Fig', 'Grape', 'Honeydew', 'Indian Fig', 'Jackfruit',
        'Kiwi', 'Lemon', 'Mango', 'Nectarine', 'Orange',
        'Papaya', 'Quince', 'Raspberry', 'Strawberry', 'Tangerine',
        'Ugli Fruit', 'Valencia Orange', 'Watermelon', 'Xigua', 'Yellow Passion Fruit', 'Zucchini'
    ]


class CountryAutocompleteView(SimpleAutocompleteView):
    """Example autocomplete with more complex data."""
    
    def get_choices(self):
        # In a real app, this might come from a database or API
        return [
            {'code': 'US', 'name': 'United States'},
            {'code': 'CA', 'name': 'Canada'},
            {'code': 'MX', 'name': 'Mexico'},
            {'code': 'GB', 'name': 'United Kingdom'},
            {'code': 'FR', 'name': 'France'},
            {'code': 'DE', 'name': 'Germany'},
            {'code': 'IT', 'name': 'Italy'},
            {'code': 'ES', 'name': 'Spain'},
            {'code': 'JP', 'name': 'Japan'},
            {'code': 'CN', 'name': 'China'},
            {'code': 'IN', 'name': 'India'},
            {'code': 'BR', 'name': 'Brazil'},
            {'code': 'AU', 'name': 'Australia'},
        ]
    
    def get_results(self, query):
        """Search in both code and name."""
        choices = self.get_choices()
        query_lower = query.lower()
        
        results = []
        for country in choices:
            if (query_lower in country['code'].lower() or 
                query_lower in country['name'].lower()):
                results.append(country)
        
        return results[:10]


# Example Forms

class ExampleForm(forms.Form):
    """Example form using different autocomplete fields."""
    
    # Simple text autocomplete
    fruit = AutocompleteField(
        url='/autocomplete/fruits/',
        help_text='Start typing to search for fruits'
    )
    
    # Model-based autocomplete
    user = ModelAutocompleteField(
        queryset=User.objects.all(),
        url='/autocomplete/users/',
        required=False,
        help_text='Search for users by username, email, or name'
    )
    
    # Custom widget on a regular field
    country = forms.CharField(
        widget=AutocompleteWidget(url='/autocomplete/countries/'),
        help_text='Search for countries'
    )


class UserSelectionForm(forms.Form):
    """Example form for user selection with autocomplete."""
    
    assigned_to = ModelAutocompleteField(
        queryset=User.objects.filter(is_active=True),
        url='/autocomplete/active-users/',
        label='Assign to User',
        help_text='Search by username, email, or name'
    )
    
    reviewers = forms.CharField(
        widget=AutocompleteWidget(url='/autocomplete/users/'),
        help_text='Enter multiple reviewers separated by commas',
        required=False
    )


# Example URLs configuration
"""
# In your urls.py:

from django.urls import path
from suitable_django_autocomplete.examples import (
    UserAutocompleteView,
    FruitAutocompleteView,
    CountryAutocompleteView
)

urlpatterns = [
    path('autocomplete/users/', UserAutocompleteView.as_view(), name='autocomplete-users'),
    path('autocomplete/fruits/', FruitAutocompleteView.as_view(), name='autocomplete-fruits'),
    path('autocomplete/countries/', CountryAutocompleteView.as_view(), name='autocomplete-countries'),
]
"""