#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

"""
Form Input Validation
=====================
"""

from collections import Mapping, OrderedDict

from werkzeug.datastructures import MultiDict

from flask import get_template_attribute, request
from flask_babel import lazy_gettext as _


__all__ = [
    'Form',
    'Field',
    'StringField',
    'MultipleField',
    'SelectField',
    'SelectMultipleField',
    'FormField',
    'InlineFormField',
    'Button',
    'SubmitButton',
    'DeleteButton',
    'Validator',
    'Required',
    'Email',
    'Length',
    'ValidationError',
]


class FormMeta(type):
    @classmethod
    def __prepare__(metacls, name, bases, **kwds):
        return OrderedDict()

    def __new__(cls, name, bases, namespace, **kwds):
        result = type.__new__(cls, name, bases, namespace, **kwds)
        result.field_types = OrderedDict()
        result.button_types = OrderedDict()

        for name, Elem in list(namespace.items()):
            if isinstance(Elem, type) and issubclass(Elem, Field):
                result.field_types[name] = Elem

            elif isinstance(Elem, type) and issubclass(Elem, Button):
                result.button_types[name] = Elem

        return result


class Form(metaclass=FormMeta):
    template = 'forms.html'
    macro = 'render_form'
    method = 'POST'
    action = ''
    label = ''
    validators = []

    def __init__(self, field_options={}, button_options={}, parent=None, **options):
        self.options = options
        self.parent = parent
        self.errors = []

        if parent is not None:
            assert isinstance(parent, FormField), \
                   'Form parent must be a FormField instance'

        self.fields = OrderedDict()
        self.buttons = OrderedDict()

        for orig_name, FieldType in self.field_types.items():
            name = orig_name
            if orig_name.endswith('_'):
                name = orig_name[:-1]

            self.fields[name] = FieldType(name, self, **field_options)
            setattr(self, orig_name, self.fields[name])

        for orig_name, ButtonType in self.button_types.items():
            name = orig_name
            if orig_name.endswith('_'):
                name = orig_name[:-1]

            self.buttons[name] = ButtonType(name, self, **button_options)
            setattr(self, orig_name, self.buttons[name])

    def dump(self):
        result = OrderedDict()

        for name, field in self.fields.items():
            value = field.dump()
            if value is not None:
                result[name] = value

        return result

    def fill(self, target):
        for name, field in self.fields.items():
            setattr(target, name, field.dump())

    def _load_field(self, name, values):
        if not isinstance(values, list):
            values = [values]

        if name in self.buttons:
            return self.buttons[name].load(values)

        try:
            field = self.fields[name]

        except KeyError:
            msg = _('There is no field called {!r}.')
            self.errors.append(msg.format(name))
            return

        try:
            if isinstance(field, MultipleField):
                return field.load(values)

            if len(values) > 0:
                return field.load(values[0])

            return field.load(None)

        except ValidationError as error:
            field.errors.append(str(error))

    def load(self, mapping):
        self.errors.clear()

        missing = set(self.fields).union(self.buttons)

        if isinstance(mapping, MultiDict):
            mapping = multidict_to_tree(mapping)

        if isinstance(mapping, Mapping):
            for name, values in mapping.items():
                self._load_field(name, values)
                missing.discard(name)

        else:
            for name in self.fields:
                if hasattr(mapping, name):
                    self._load_field(name, getattr(mapping, name))
                    missing.discard(name)

        for name in missing:
            if name in self.fields:
                self.fields[name].load(None)

            if name in self.buttons:
                self.buttons[name].load(None)

    def is_valid(self):
        if self.errors:
            return False

        for field in self.fields.values():
            if not field.is_valid():
                return False

        return True

    def validate_on_submit(self):
        if request.method == 'GET':
            return False

        self.load(request.form)
        return self.is_valid()

    def render(self, *args, **kwargs):
        assert self.template is not None, 'Form does not specify a template'
        assert self.macro is not None, 'Form does not specify a macro'

        macro = get_template_attribute(self.template, self.macro)
        return macro(self, *args, **self.options, **kwargs)


class Field:
    """
    Base input field used to create other, derived input fields.
    """

    template = 'forms.html'
    macro = None
    default = ''
    label = ''
    validators = []
    nullable = False

    def __init__(self, name, form, **options):
        self.name = name
        self.form = form
        self.errors = []
        self.options = options
        self.value = self.default

    @property
    def id(self):
        elem = self
        path = []

        while elem is not None:
            path.insert(0, elem.name)
            elem = elem.form.parent

        return '-'.join(path)

    def is_valid(self):
        if self.errors:
            return False

        return True

    def load(self, value):
        self.errors.clear()

        try:
            if value is None:
                self.value = self.default
            else:
                self.value = value

            if not self.options.get('disabled'):
                self.validate()

        except ValidationError as error:
            self.errors.append(str(error))

    def dump(self):
        if not self.value:
            if self.nullable:
                return None

        return self.value

    def validate(self):
        for validate in self.validators:
            validate(self)

    def render(self, *args, **kwargs):
        assert self.template is not None, 'Field does not specify a template'
        assert self.macro is not None, 'Field does not specify a macro'

        macro = get_template_attribute(self.template, self.macro)
        return macro(self, *args, **self.options, **kwargs)


class StringField(Field):
    macro = 'render_string_field'


class MultipleField(Field):
    default = []

    def validate(self):
        if not isinstance(self.value, list):
            msg = _('Expected list of values.')
            raise ValidationError(msg)

        for value in self.value:
            if value not in self.choices:
                msg = _('One of the values not among the valid choices.')
                raise ValidationError(msg)

        super().validate()


class SelectField(Field):
    macro = 'render_select_field'


class SelectMultipleField(MultipleField):
    macro = 'render_select_multiple_field'


class FormField(Field):
    macro = 'render_sub_form'
    subform = None
    field_options = {}
    button_options = {}

    def __init__(self, *args, **options):
        assert self.subform is not None, 'Member subform must be specified'
        assert isinstance(self.subform, type), 'Member subform must be a type'
        assert issubclass(self.subform, Form), 'Member subform must be a Form'

        self.subform = self.subform(parent=self,
                                    field_options=self.field_options,
                                    button_options=self.button_options)

        super().__init__(*args, **options)

    def load(self, value):
        self.subform.load(value)
        self.value = self.subform.dump()

    def is_valid(self):
        return super().is_valid() and self.subform.is_valid()


class InlineFormField(FormField):
    macro = 'render_inline_sub_form'


class Button:
    """
    Base button used to create other, derived buttons.
    """

    template = 'forms.html'
    macro = None
    label = ''

    def __init__(self, name, form, **options):
        self.name = name
        self.form = form
        self.options = options
        self.clicked = False

    def load(self, value):
        self.clicked = value and True

    def render(self, *args, **kwargs):
        assert self.template is not None, 'Button does not specify a template'
        assert self.macro is not None, 'Button does not specify a macro'

        macro = get_template_attribute(self.template, self.macro)
        return macro(self, *args, **self.options, **kwargs)


class SubmitButton(Button):
    macro = 'render_submit_button'


class DeleteButton(Button):
    macro = 'render_delete_button'


class Validator:
    """
    Parent class for all kinds of input validators.
    """

    def __init__(self, message):
        self.message = message

    def __call__(self, field):
        pass


class Required(Validator):
    def __init__(self, message=None):
        if message is None:
            message = _('Field must be filled in.')

        self.message = message

    def __call__(self, field):
        if not field.value:
            raise ValidationError(self.message)


class Email(Validator):
    def __init__(self, message=None):
        if message is None:
            message = _('Invalid email address format.')

        self.message = message

    def __call__(self, field):
        if field.value:
            if '@' not in field.value:
                raise ValidationError(self.message)


class Length(Validator):
    def __init__(self, min=None, max=None, message=None):
        self.min = min
        self.max = max

        if message is None:
            if self.min is not None and self.max is not None:
                message = _('Field length must be between {} and {}.') \
                          .format(self.min, self.max)
            elif self.min is not None:
                message = _('Field length may not be lower than {}.') \
                          .format(self.min)
            elif self.max is not None:
                message = _('Field length must not exceed {}.') \
                          .format(self.max)
            else:
                # Won't ever raise this.
                message = 'BUG'

        super().__init__(message)

        self.min = min
        self.max = max

    def __call__(self, field):
        if field.value:
            if self.min is not None:
                if len(field.value) < self.min:
                    raise ValidationError(self.message)

            if self.max is not None:
                if len(field.value) > self.max:
                    raise ValidationError(self.message)


class ValidationError(Exception):
    """Error signalizing that a form field validation has failed."""


def multidict_to_tree(multidict):
    result = {}

    for key, values in multidict.lists():
        path = key.split('-')
        target = result

        for name in path[:-1]:
            try:
                name = int(name)
            except ValueError:
                pass

            target.setdefault(name, {})
            target = target[name]

        target[path[-1]] = values

    return number_dict_to_list(result)


def number_dict_to_list(mapping):
    if not isinstance(mapping, Mapping):
        return mapping

    if all_int_keys(mapping):
        result = []
        for _key, value in sorted(mapping.items()):
            result.append(number_dict_to_list(value))

    else:
        result = {}
        for key, value in mapping.items():
            result[key] = number_dict_to_list(value)

    return result


def all_int_keys(m):
    for key in m:
        if not isinstance(key, int):
            return False

    return True


# vim:set sw=4 ts=4 et:
