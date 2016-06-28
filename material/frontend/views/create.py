from itertools import chain

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import ModelFormMixin


class CreateModelView(ModelFormMixin, TemplateResponseMixin, View):
    model = None
    viewset = None
    template_name_suffix = '_create'
    extra_forms = None
    formsets = None
    inlines = None

    def __init__(self, *args, **kwargs):
        super(CreateModelView, self).__init__(*args, **kwargs)
        if self.form_class is None and self.fields is None:
            self.fields = '__all__'

    def get_extra_form_initial_default(self, form_name):
        return {}

    def get_extra_form_kwargs_default(self, form_name):
        kwargs = {
            'initial': self.get_initial(),
            'prefix': form_name,
        }
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def get_extra_forms(self):
        result = {}
        if self.extra_forms:
            for name, form_class in self.extra_forms.items:
                factory_method_name = "get_{}_form".format(name)
                form_factory = getattr(factory_method_name, lambda **kwargs: form_class(**kwargs))

                kwargs_method_name = "get_{}_form_kwargs".format(name)
                kwargs_factory = getattr(kwargs_method_name, lambda: {'prefix': name})

                kwargs = kwargs_factory()
                kwargs.set_default('prefix', name)
                result[name] = form_factory(kwargs)
        return result

    def get_formsets(self):
        result = {}
        return result

    def get_inlines(self):
        result = {}
        return result

    @classmethod
    def has_perm(cls, user):
        return True

    def form_invalid(self, form, extra_forms=None, formsets=None, inlines=None):
        return self.render_to_response(
            self.get_context_data(
                form=form, extra_forms=extra_forms,
                formsets=formsets, inlines=inlines))

    def save_form(self, form, extra_forms=None, formsets=None, inlines=None):
        self.object = form.save(commit=False)

    def save_model(self, form, extra_forms=None, formsets=None, inlines=None):
        self.object.save()

    def save_related(self, form, extra_forms=None, formsets=None, inlines=None):
        for form in extra_forms.values():
            if hasattr(form, 'save'):
                form.save()
        for formset in formsets.values():
            if hasattr(formset, 'save'):
                formset.save()
        for inlines in inlines.values():
            inlines.save()

    def get_success_url(self):
        if self.success_url is None:
            opts = self.model._meta
            return reverse('{}:{}_list'.format(opts.app_label, opts.model_name))

        return super(CreateModelView, self).get_success_url()

    def form_valid(self, form, extra_forms=None, formsets=None, inlines=None):
        self.save_form(form, extra_forms=extra_forms, formsets=formsets, inlines=inlines)
        self.save_model(form, extra_forms=extra_forms, formsets=formsets, inlines=inlines)
        self.save_related(form, extra_forms=extra_forms, formsets=formsets, inlines=inlines)
        return HttpResponseRedirect(self.get_success_url())

    def get_template_names(self):
        if self.template_name is None:
            opts = self.model._meta
            return [
                '{}/{}{}.html'.format(opts.app_label, opts.model_name, self.template_name_suffix),
                '{}/{}_form.html'.format(opts.app_label, opts.model_name, self.template_name_suffix),
                'material/frontend/views/create.html',
            ]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        if 'form' not in kwargs:
            kwargs['form'] = self.get_form()
        if 'extra_forms' not in kwargs:
            kwargs['extra_forms'] = self.get_extra_forms()
        if 'formsets' not in kwargs:
            kwargs['formsets'] = self.get_formsets()
        if 'inlines' not in kwargs:
            kwargs['inlines'] = self.get_inlines()

        return super(CreateModelView, self).get_context_data(**kwargs)

    def get(self, request, *args, **kwargs):
        self.object = None
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        extra_forms = self.get_extra_forms()
        formsets = self.get_formsets()
        inlines = self.get_inlines()

        is_valid = all([item.is_valid() for item in chain(
            [form], extra_forms.values(), formsets.values(), inlines.values())])

        if is_valid:
            return self.form_valid(form, extra_forms=extra_forms, formsets=formsets, inlines=inlines)
        else:
            return self.form_invalid(form, extra_forms=extra_forms, formsets=formsets, inlines=inlines)

    def put(self, *args, **kwargs):
        return self.post(*args, **kwargs)
