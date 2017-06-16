#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

"""
HTML Forms
==========

Module provides classes that can be used to model HTML forms along with
server-side input validators. They are then rendered using macros from
Flask-sourced jinja2 templates.

Example:

.. code-block:: python

    from flask import request, flash, redirect, url_for
    from flask_babel import lazy_gettext as _
    from uspech.site.exceptions import InvalidUsage
    from uspech.site.forms import *

    class EditForm(Form):
        class Name(StringField):
            label = _('Clip Name')
            validators = [Required(), Length(1, 100)]

        class format(SelectField):
            label = _('Clip Format')
            choices = OrderedDict(
                fmt_16_9=_('16:9'),
                fmt_4_3=_('4:3'),
            )

    @app.route('/clip/<id:int>/edit/', methods=['GET', 'POST'])
    def clip_edit(id):
        form = EditForm()

        clip = db.clip.get(id)
        if clip is None:
            raise InvalidUsage(_('No such clip found.'), {'id': id})

        if form.validate_on_submit():
            form.fill(clip)
            db.commit()

            flash(_('Clip details have been updated.'), 'ok')
            return redirect(url_for('clip_edit', id=id))

        if request.method == 'GET':
            form.load(clip)

        return render_template('clip/edit.html', clip=clip, form=form)
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
    """
    Form for user input

    Makes use of a metaclass that helps to preserve class member ordering.
    You are expected to supply static members of type :class:`type` that
    subclass :class:`Field`, possibly overriding some static members.

    When the :class:`Form` is instantiated, all member field classes are
    instantiated as well and take their respective place among the instance
    attributes.

    Example of a custom form:

    .. code-block:: python

        from flask_babel import lazy_gettext as _
        from uspech.site.forms import *

        class SearchForm(Form):
            label = _('Search')
            action = '/search'
            method = 'GET'

            template = 'forms/search.html'
            mecro = 'render_search_form'

            class q(StringField):
                label = _('Query')
                validators = [Required(), Length(1, 100)]

            class ok(SubmitButton):
                label = _('OK')

        search = SearchForm()
        search.load({'q': 'Python'})
        assert search.q.value == 'Python'
    """

    template = 'forms.html'
    """
    Template from which the macro used to render the form should be sourced.
    """

    macro = 'render_form'
    """
    Name of the ``jinja2`` macro used to render the form and it's contents.
    """

    method = 'POST'
    """
    Form submission method. Best keep it set to ``POST``.
    """

    action = ''
    """
    Address of the input-processing endpoint. Keep empty to send the form to
    the same address it was loaded from. Use ``GET``/``POST`` to determine
    whether to render the form or process results. See the example above.
    """

    label = ''
    """
    Label to render as a form heading. Use this to separate subforms from
    contents of the parent forms when needed and render the main form
    heading separately for better control.
    """

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
        """
        Recursively dump contents of the form.

        Returns a :class:`~collections.Mapping` with form fields and their
        current values. Sub-forms will provide nested mappings.
        """

        result = OrderedDict()

        for name, field in self.fields.items():
            value = field.dump()
            if value is not None:
                result[name] = value

        return result

    def fill(self, target):
        """
        Set `target` object attributes to the respective field values.
        Ideal for SQLSoup's database-backed objects.
        """

        for name, field in self.fields.items():
            setattr(target, name, field.dump())

    def _load_field(self, name, values):
        if not isinstance(values, list):
            values = [values]

        try:
            if name in self.buttons:
                elem = self.buttons[name]
            else:
                elem = self.fields[name]

        except KeyError:
            msg = _('There is no field called %(name)r.', name=name)
            self.errors.append(msg)
            return

        try:
            if isinstance(elem, MultipleField):
                return elem.load(values)

            if len(values) > 0:
                return elem.load(values[0])

            return elem.load(None)

        except ValidationError as error:
            if hasattr(elem, 'errors'):
                elem.errors.append(str(error))

    def load(self, mapping):
        """
        Populate form fields from a :class:`~collections.Mapping`.

        There is a special provision for
        :class:`~werkzeug.datastructures.MultiDict` used by Flask to provide
        request parameters.

        .. admonition:: WARNING

            All values that are not instances of :class:`list` are wrapped in
            one during the input normalization process. Make sure that you do
            not use other kinds of sequence for multiple-value fields.
        """

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
        """
        Test whether is the form completely error-free.
        """

        if self.errors:
            return False

        for field in self.fields.values():
            if not field.is_valid():
                return False

        return True

    def validate_on_submit(self):
        """
        Shortcut to determine whether has the form been submitted,
        load it from the request and check it's validity. Use like this:

        .. code-block:: python

            if form.validate_on_submit():
                form.fill(user)
                db.commit()
        """

        if request.method == 'GET':
            return False

        self.load(request.form)
        return self.is_valid()

    def render(self, *args, **kwargs):
        """
        Render the form using :attr:`~Form.template` and :attr:`~Form.macro`.

        To be used from inside the template, like this:

        .. code-block:: jinja

            <div class="user-edit-form">
             <h2>Edit User</h2>
             {{form.render()}}
            </div>
        """

        assert self.template is not None, 'Form does not specify a template'
        assert self.macro is not None, 'Form does not specify a macro'

        macro = get_template_attribute(self.template, self.macro)
        return macro(self, *args, **self.options, **kwargs)


class Field:
    """
    Base input field used to create other, derived input fields.

    .. code-block:: python

        class UserForm(Form):
            class name(StringField):
                label = _('Name')
                validators = [Required(), Length(1, 100)]

                def validate(self):
                    super().validate()

                    # Deal with fake users.
                    if self.value == 'John Smith':
                        raise ValidationError(_('Nice try, "John".'))
    """

    template = 'forms.html'
    """
    Template from which the macro used to render the field should be sourced.
    """

    macro = None
    """
    Name of the ``jinja2`` macro used to render the field.
    """

    default = ''
    """
    Default value to use when no input was supplied.

    Use something that evaluates to ``False`` if you need to be able to
    determine whether was the field filled at all. Best not to touch it.
    """

    label = ''
    """
    Label to render along the field.
    """

    validators = []
    """
    List of callables that are used to check and possibly normalize the
    field value. Called on the :class:`Field`. Try to use the pre-defined
    :class:`Validator` child classes.
    """

    nullable = False
    """
    Controls whether to dump ``None`` value when the field value is falsy.
    Affects the :func:`~Field.fill` method in a way that is compatible with
    having the database column nullable.
    """

    def __init__(self, name, form, **options):
        self.name = name
        self.form = form
        self.errors = []
        self.options = options
        self.value = self.default

    @property
    def id(self):
        """
        Computed field identifier that combines names of all parent fields
        in the form hiararchy. Needed to identify values of nested form
        fields since there is no hierarchy in submitted HTML forms.
        """

        elem = self
        path = []

        while elem is not None:
            path.insert(0, elem.name)
            elem = elem.form.parent

        return '-'.join(path)

    def is_valid(self):
        """
        Test whether is the field completely error-free.
        """

        if self.errors:
            return False

        return True

    def load(self, value):
        """
        Populate form field from the supplied value.
        """

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
        """
        Dump form field value with respect to the :attr:`~Form.nullable`
        attribute.
        """

        if not self.value:
            if self.nullable:
                return None

        return self.value

    def validate(self):
        """
        Run field validators and possibly some additional field-type-specific
        checks. Feel free to override it, but do not forget to call the
        original method as well.
        """

        for validate in self.validators:
            validate(self)

    def render(self, *args, **kwargs):
        """
        Render the form using :attr:`~Form.template` and :attr:`~Form.macro`.
        """

        assert self.template is not None, 'Field does not specify a template'
        assert self.macro is not None, 'Field does not specify a macro'

        macro = get_template_attribute(self.template, self.macro)
        return macro(self, *args, **self.options, **kwargs)


class StringField(Field):
    """
    Field that contains a short textual value, usually without line breaks.
    """

    macro = 'render_string_field'

    def validate(self):
        if not isinstance(self.value, str):
            raise ValidationError(_('Expected a string.'))

        self.value = self.value.strip()
        super().validate()


class SelectField(Field):
    """
    Field that allows user to select one of many choices.
    """

    macro = 'render_select_field'

    choices = OrderedDict()
    """
    Ordered mapping of choice names to their respective labels.
    """


class MultipleField(Field):
    """
    Parent class for all field types that can contain multiple values.
    """

    default = []

    def validate(self):
        if not isinstance(self.value, list):
            raise ValidationError(_('Expected list of strings.'))

        for item in self.value:
            if not isinstance(item, str):
                raise ValidationError(_('Not all options are strings.'))

        self.value = [item.strip() for item in self.value]

        for value in self.value:
            if value not in self.choices:
                msg = _('One of the values not among the valid choices.')
                raise ValidationError(msg)

        super().validate()


class SelectMultipleField(MultipleField):
    """
    Field that allows user to select multiple options out of many choices.
    """

    macro = 'render_select_multiple_field'

    choices = OrderedDict()
    """
    Ordered mapping of choice names to their respective labels.
    """


class FormField(Field):
    """
    Special field that is actually another form to be rendered as the part
    of it's parent. Represents a nested :class:`~collections.Mapping` when
    loading or dumping the data.

    Ideal for situations such as JSON columns on database rows.
    """

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


class Button:
    """
    Base button used to create other, derived buttons.
    """

    template = 'forms.html'
    """
    Template from which the macro used to render the button should be sourced.
    """

    macro = None
    """
    Name of the ``jinja2`` macro used to render the button.
    """

    label = ''
    """
    Label on the button.
    """

    def __init__(self, name, form, **options):
        """
        :param name: Name of the button relative to the parent form.
        :param form: Reference to the parent form.
        :param options: Additional options passed to the rendering macro.
        """

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
    """
    The typical, inviting submit button.
    """

    macro = 'render_submit_button'


class DeleteButton(Button):
    """
    Delete button, rendered to appear dangerous.
    """

    macro = 'render_delete_button'


class Validator:
    """
    Parent class for all kinds of input validators.
    """

    def __init__(self, message):
        """
        :param message: Reason for failed validation intended for the user.
        """

        self.message = message

    def __call__(self, field):
        """
        Perform validation.

        :param field: Field to validate.
        """


class Required(Validator):
    """
    Require user to fill the field with anything.
    """

    def __init__(self, message=None):
        if message is None:
            message = _('Field must be filled in.')

        self.message = message

    def __call__(self, field):
        if not field.value:
            raise ValidationError(self.message)


class Email(Validator):
    """
    Require that field contains the ``@`` character.
    """

    def __init__(self, message=None):
        if message is None:
            message = _('Invalid email address format.')

        self.message = message

    def __call__(self, field):
        if field.value:
            if '@' not in field.value:
                raise ValidationError(self.message)


class Length(Validator):
    """
    Require that field length is in the specified range.
    """

    def __init__(self, min=None, max=None, message=None):
        self.min = min
        self.max = max

        if message is None:
            if self.min is not None and self.max is not None:
                message = _('Field length must be between %(min)i and %(max)i.', min=min, max=max)
            elif self.min is not None:
                message = _('Field length may not be lower than %(min)i.', min=min)
            elif self.max is not None:
                message = _('Field length must not exceed %(max)i.', max=max)
            else:
                # Won't ever raise this.
                message = 'BUG'

        super().__init__(message)

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
