from django.http import HttpResponseRedirect
from django.views.generic.edit import ModelFormMixin


class ExtraFormsMixin(object):
    extra_forms = None

    def get_extra_form_initial_default(self, form_name):
        return {}

    def get_extra_form_initial(self, form_name):
        method_name = "get_{}_form_initial".format(form_name)
        method = getattr(self, method_name, lambda: self.get_extra_form_initial_default(form_name))
        return method()

    def get_extra_form_kwargs_default(self, form_name):
        kwargs = {
            'initial': self.get_extra_form_initial(form_name),
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
                kwargs.setdefault('prefix', name)
                result[name] = form_factory(kwargs)
        return result

    def get_context_data(self, **kwargs):
        if 'formsets' not in kwargs:
            kwargs['formsets'] = self.get_formsets()
        return super(ExtraFormsMixin, self).get_context_data(**kwargs)


class FormsetsMixin(object):
    formsets = None

    def get_formset_initial_default(self, formset_name):
        return {}

    def get_formset_initial(self, formset_name):
        method_name = "get_{}_formset_initial".format(formset_name)
        method = getattr(self, method_name, lambda: self.get_formset_initial_default(formset_name))
        return method()

    def get_formset_kwargs_default(self, form_name):
        kwargs = {
            'initial': self.get_formset_initial(form_name),
            'prefix': form_name,
        }
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def get_formsets(self):
        result = {}
        if self.formsets:
            for name, formset_def_class in self.formsets.items():
                kwargs_method_name = "get_{}_formset_kwargs".format(name)
                kwargs_factory = getattr(self, kwargs_method_name, lambda: self.get_formset_kwargs_default(name))

                kwargs = kwargs_factory()
                kwargs.setdefault('prefix', name)
                result[name] = formset_def_class(**kwargs)
        return result

    def get_context_data(self, **kwargs):
        if 'extra_forms' not in kwargs:
            kwargs['extra_forms'] = self.get_extra_forms()
        return super(FormsetsMixin, self).get_context_data(**kwargs)


class InlinesMixin(object):
    inlines = None

    def get_inlines(self):
        result = {}
        return result

    def get_context_data(self, **kwargs):
        if 'inlines' not in kwargs:
            kwargs['inlines'] = self.get_inlines()
        return super(InlinesMixin, self).get_context_data(**kwargs)


class MultiFormMixin(ExtraFormsMixin,
                     FormsetsMixin,
                     InlinesMixin,
                     ModelFormMixin):
    """
    Mixing allows to save multiple forms, formsets and inlines in
    the same view
    """
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

    def form_invalid(self, form, extra_forms=None, formsets=None, inlines=None):
        return self.render_to_response(
            self.get_context_data(
                form=form, extra_forms=extra_forms,
                formsets=formsets, inlines=inlines))

    def form_valid(self, form, extra_forms=None, formsets=None, inlines=None):
        self.save_form(form, extra_forms=extra_forms, formsets=formsets, inlines=inlines)
        self.save_model(form, extra_forms=extra_forms, formsets=formsets, inlines=inlines)
        self.save_related(form, extra_forms=extra_forms, formsets=formsets, inlines=inlines)
        return HttpResponseRedirect(self.get_success_url())
