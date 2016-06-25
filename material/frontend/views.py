from __future__ import unicode_literals

import json

from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db.models.query import QuerySet
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.generic.base import ContextMixin, TemplateResponseMixin


from . import forms
from .datalist import DataList


class CreateModelView(View):
    model = None
    viewset = None

    def has_perm(self, user):
        return True


class ListModelView(ContextMixin, TemplateResponseMixin, View):
    model = None
    viewset = None
    queryset = None
    paginate_by = 15
    datatable_config = None
    template_name_suffix = '_list'

    datalist_class = DataList
    list_display = ('__str__', )
    list_display_links = ()

    datatable_default_config = {
        'processing': False,
        'serverSide': True,
        'ajax': '.',
        'ordering': False,
        'info': False,
        'bFilter': False,
        'bAutoWidth': False,
        'bLengthChange': False,
        "oLanguage": {
            'oPaginate': {
                'sFirst': "",
                'sLast': "",
                'sNext': "&rang;",
                'sPrevious': "&lang;",
            }
        },
        'responsive': {
            'details': False
        }
    }

    def has_perm(self, user):
        return True

    def get_template_names(self):
        if self.template_name is None:
            opts = self.object_list.model._meta
            return [
                'material/frontend/views/list.html',
                '{}/{}{}.html'.format(opts.app_label, opts.model_name, self.template_name_suffix)
            ]
        return [self.template_name]

    def get_list_display(self):
        return self.list_display

    def get_list_display_links(self, list_display):
        if self.list_display_links or self.list_display_links is None or not list_display:
            return self.list_display_links
        else:
            # Use only the first item in list_display as link
            return list(list_display)[:1]

    def create_datalist(self):
        list_display = self.get_list_display()
        list_display_links = self.get_list_display_links(list_display)
        return self.datalist_class(
            self.model,
            self.object_list,
            data_sources=[self, self.viewset] if self.viewset else [self],
            list_display=list_display,
            list_display_links=list_display_links
        )

    def get_queryset(self):
        if self.queryset is not None:
            queryset = self.queryset
            if isinstance(queryset, QuerySet):
                queryset = queryset.all()
        elif self.model is not None:
            queryset = self.model._default_manager.all()
        else:
            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. Define "
                "%(cls)s.model, %(cls)s.queryset, or override "
                "%(cls)s.get_queryset()." % {
                    'cls': self.__class__.__name__
                })
        return queryset

    def get_datatable_config(self):
        config = self.datatable_default_config.copy()
        config['iDisplayLength'] = self.paginate_by
        if self.datatable_config is not None:
            config.update(self.datatable_config)
        return config

    def get_context_data(self, **kwargs):
        context = super(ListModelView, self).get_context_data(**kwargs)
        context.update({
            'datatable_config': json.dumps(self.get_datatable_config()),
            'headers': self.datalist.get_headers_data(),
            'data': self.datalist.get_data(0, self.paginate_by),
        })

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_json_data(self, request, *args, **kwargs):
        form = forms.DatatableRequestForm(request.GET)
        if not form.is_valid():
            return {'error': form.errors}

        draw = form.cleaned_data['draw']
        start = form.cleaned_data['start']
        length = form.cleaned_data['length']

        data = {
            "draw": draw,
            "recordsTotal": self.datalist.total(),
            "recordsFiltered": self.datalist.total_filtered(),
            "data": list(self.datalist.get_data(start, length))
        }

        return JsonResponse(data)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.has_perm(request.user):
            raise PermissionDenied

        self.object_list = self.get_queryset()
        self.datalist = self.create_datalist()

        if request.is_ajax() and not request.META.get("PJAX", False):
            handler = self.get_json_data
        elif request.method.lower() in self.http_method_names:
            handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        return handler(request, *args, **kwargs)


class UpdateModelView(View):
    model = None
    viewset = None

    def has_perm(self, user, obj):
        return True


class DeleteModelView(View):
    model = None
    viewset = None

    def has_perm(self, user, obj):
        return True


class DetailsModelView(View):
    model = None
    viewset = None

    def has_perm(self, user, obj):
        return True


class ModelViewSet(object):
    model = None

    create_view_class = CreateModelView
    list_view_class = ListModelView
    update_view_class = UpdateModelView
    delete_view_class = DeleteModelView

    list_display = ('__str__', )

    def has_perm(self, user):
        return True

    def get_common_kwargs(self):
        return {'model': self.model,
                'viewset': self}

    def get_create_view_kwargs(self):
        return self.get_common_kwargs()

    def get_list_view_kwargs(self):
        kwargs = self.get_common_kwargs()
        kwargs.update({
            'list_display': self.list_display
        })
        return kwargs

    def get_update_view_kwargs(self):
        return self.get_common_kwargs()

    def get_delete_view_kwargs(self):
        return self.get_common_kwargs()

    @property
    def create_view(self):
        return self.create_view_class.as_view(**self.get_create_view_kwargs())

    @property
    def list_view(self):
        return self.list_view_class.as_view(**self.get_list_view_kwargs())

    @property
    def update_view(self):
        return self.update_view_class.as_view(**self.get_update_view_kwargs())

    @property
    def delete_view(self):
        return self.update_view_class.as_view(**self.get_delete_view_kwargs())

    @property
    def urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        return [
            url('^$', self.list_view, name='{}_{}_list'.format(*info)),
            url('^add/$', self.create_view, name='{}_{}_add'.format(*info)),
            url(r'^(.+)/change/$', self.update_view, name='{}_{}_change'.format(*info)),
            url(r'^(.+)/delete/$', self.delete_view, name='{}_{}_delete'.format(*info)),
        ]
