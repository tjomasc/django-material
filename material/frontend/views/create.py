from itertools import chain

from django.core.urlresolvers import reverse
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin

from .mixins import MultiFormMixin


class CreateModelView(MultiFormMixin, TemplateResponseMixin, View):
    viewset = None
    template_name_suffix = '_create'

    def __init__(self, *args, **kwargs):
        super(CreateModelView, self).__init__(*args, **kwargs)
        if self.form_class is None and self.fields is None:
            self.fields = '__all__'

    @classmethod
    def has_perm(cls, user):
        return True

    def get_success_url(self):
        if self.success_url is None:
            opts = self.model._meta
            return reverse('{}:{}_list'.format(opts.app_label, opts.model_name))

        return super(CreateModelView, self).get_success_url()

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
