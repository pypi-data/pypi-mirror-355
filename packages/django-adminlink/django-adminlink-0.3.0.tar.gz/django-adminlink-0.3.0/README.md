# Django-adminlink

[![PyPi version](https://badgen.net/pypi/v/django-adminlink/)](https://pypi.python.org/pypi/django-adminlink/)
[![Documentation Status](https://readthedocs.org/projects/django-adminlink/badge/?version=latest)](http://django-adminlink.readthedocs.io/?badge=latest)
[![PyPi license](https://badgen.net/pypi/license/django-adminlink/)](https://pypi.python.org/pypi/django-adminlink/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

The Django admin allows to list rows in an easy way. Some feature that seems to be "missing" is to jump in an efficient way to the detail view of a *related* object. For example if a model `A` has a `ForeignKey` to `B`, then the `ModelAdmin` of `A` can show the `__str__` of `B`, but without a link.

Django's admin actions are also very useful, but what seems to be missing is an easy way to just run the action on a single row without too much "hassle".

This package provides a mixin to effectively add such links.

## Installation

You can install the package with:

```
pip install django-adminlink
```

You do *not* need to add `'django_adminlink'` to the `INSTALLED_APPS` settings *unless* you use the `SingleItemActionMixin` or a derived product from it. In that case,
you need to make use of the `static/js/single_admin_action.js` file that ships with it. Then the `INSTALLED_APPS` looks like:


```python3
# settings.py

# …

INSTALLED_APPS = [
    # …,
    'django_adminlink'
]
```

## Usage

Once the package is installed, we can work with the mixins provided by the package.

### Adding links to `ForeignKey` fields

you can use the `LinkFieldAdminMixin` mixin in the admins where you want `ForeignKey`s and `OneToOneField`s to be linked to the corresponding admin detail view of that object:

```python3
from django.contrib import admin
from django_adminlink.admin import LinkFieldAdminMixin


@admin.register(Movie)
class MovieAdmin(LinkFieldAdminMixin, admin.ModelAdmin):
    list_display = ['__str__', 'genre']
```

If `genre` is a `ForeignKey` to a `Genre` model for example, and `Genre` has its own `ModelAdmin`, it will automatically convert `genre` into a column that adds a link to the admin detail view of the corresponding genre.

### Single row actions

The package also provides a `SingleItemActionMixin`, this enables to add a column at the right end of the admin that contains (one or more) buttons. These buttons then run a Django admin action on a *single* record.

One can specify which actions to run by listing these, for example:

```python3
from django.contrib import admin
from django_adminlink.admin import SingleItemActionMixin

@admin.register(Movie)
class MovieAdmin(SingleItemActionMixin, admin.ModelAdmin):
    action_buttons = {'delete': 'delete_selected'}
```

One can work with a dictionary that has as key the "label" of the button, and as value the name (key) of the action to work with. This will add a button with the label "delete" as last column. When clicked, that row, and only that row is then removed.

The package does not perform the action itself: it works with a small amount of *JavaScript* that just disables all checkboxes, enables only the checkbox of the selected row, and finally submits the action form, letting Django handle the rest of the logic.

If the label(s) and action(s) are the same, one can also work with a list of the names of the actions, like:

```python3
from django.contrib import admin
from django_adminlink.admin import SingleItemActionMixin

@admin.register(Movie)
class MovieAdmin(SingleItemActionMixin, admin.ModelAdmin):
    action_buttons = ['delete_selected']
```

## Grouping actions

The list of actions is "flat". We can add item groups, just like in other Django `ChoiceField`s. For this, we introduced the `GroupedActionAdminMixin`.

This mixin looks at the actions. We also defined a `@grouped_action` decorator, which does approximately the same as the `@admin.action` decorator, except with an extra parameter `action_group=…`.

We can register actions like:

```python3
from django.contrib import admin
from django_adminlink.admin import GroupedActionAdminMixin, grouped_action

@admin.register(Movie)
class MovieAdmin(GroupedActionAdminMixin, admin.ModelAdmin):
    action_buttons = ['star', 'unstar', 'clear_comments']
    
    @grouped_action(description='star item', action_group='stars')
    def star(self, request, queryset):
      # …
    
    @grouped_action(description='unstar item', action_group='stars')
    def unstar(self, request, queryset):
      # …
    
    @grouped_action(description='clear comments', action_group='comments')
    def clear_comments(self, request, queryset):
      # …
```

The order of the groups is determined by the order of the individual actions: the first action for that group for each group determines how the groups are listed.