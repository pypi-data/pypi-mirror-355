# Suitable Django Autocomplete

A modern autocomplete widget for Django 4.2+ using web components.

## Quick Start

### 1. Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    ...
    'suitable_django_autocomplete',
]
```

### 2. Create an autocomplete view

```python
from suitable_django_autocomplete import SimpleAutocompleteView

class FruitAutocompleteView(SimpleAutocompleteView):
    choices = ['Apple', 'Banana', 'Cherry', 'Date', 'Elderberry']
```

### 3. Add URL pattern

```python
from django.urls import path
from .views import FruitAutocompleteView

urlpatterns = [
    path('autocomplete/fruits/', FruitAutocompleteView.as_view(), name='autocomplete-fruits'),
]
```

### 4. Use in a form

```python
from django import forms
from suitable_django_autocomplete import AutocompleteField

class MyForm(forms.Form):
    fruit = AutocompleteField(url='/autocomplete/fruits/')
```

### 5. Include static files in your template

```django
{{ form.media }}
```

## Model-based Autocomplete

```python
from django.contrib.auth.models import User
from suitable_django_autocomplete import ModelAutocompleteView, ModelAutocompleteField

class UserAutocompleteView(ModelAutocompleteView):
    model = User
    search_fields = ['username', 'email', 'first_name', 'last_name']

class AssignmentForm(forms.Form):
    user = ModelAutocompleteField(
        queryset=User.objects.all(),
        url='/autocomplete/users/'
    )
```

## Features

- Web component-based (works without framework dependencies)
- Full accessibility support (ARIA compliant)
- Keyboard navigation
- Debounced search
- Loading states
- Error handling
- Django form integration
- Model support