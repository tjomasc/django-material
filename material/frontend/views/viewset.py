from django.conf.urls import url

from .create import CreateModelView
from .list import ListModelView
from .update import UpdateModelView
from .delete import DeleteModelView


DEFAULT = object()


class ModelViewSet(object):
    model = None

    create_view_class = CreateModelView
    list_view_class = ListModelView
    update_view_class = UpdateModelView
    delete_view_class = DeleteModelView

    list_display = DEFAULT
    list_display_links = DEFAULT

    def _add_option(self, view_class, target, option_name):
        if hasattr(view_class, option_name):
            option = getattr(self, option_name)
            if option is not DEFAULT:
                target[option_name] = option

    def has_perm(self, user):
        return True

    def get_common_kwargs(self):
        return {'model': self.model,
                'viewset': self}

    def get_create_view_kwargs(self):
        return self.get_common_kwargs()

    def get_list_view_kwargs(self):
        kwargs = self.get_common_kwargs()
        self._add_option(self.list_view_class, kwargs, 'list_display')
        self._add_option(self.list_view_class, kwargs, 'list_display_links')
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
        model_name = self.model._meta.model_name

        return [
            url('^$', self.list_view, name='{}_list'.format(model_name)),
            url('^add/$', self.create_view, name='{}_add'.format(model_name)),
            url(r'^(.+)/change/$', self.update_view, name='{}_change'.format(model_name)),
            url(r'^(.+)/delete/$', self.delete_view, name='{}_delete'.format(model_name)),
        ]
