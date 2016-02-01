#!/usr/bin/python
# ex:set fileencoding=utf-8:

from __future__ import unicode_literals

from django.core.servers.basehttp import FileWrapper
from django.http import Http404
from django.http import HttpResponse

# from rest_framework.mixins import CreateModelMixin
# from rest_framework.mixins import RetrieveModelMixin
# from rest_framework.mixins import UpdateModelMixin
# from rest_framework.mixins import DestroyModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from djangobmf.core.pagination import DocumentsPagination
from djangobmf.core.serializers import DocumentsSerializer
from djangobmf.core.views.mixins import BaseMixin
from djangobmf.models import Document
from djangobmf.conf import settings

import os


class View(BaseMixin, ViewSet):
    """
    List, upload, update and delete documents
    """
    # permission_classes = [ActivityPermission]
    serializer_class = DocumentsSerializer
    pagination_class = DocumentsPagination

    def get_view_name(self):
        return 'Documents'

    def get_queryset(self):
        return Document.objects.all()

    def filter_queryset(self, queryset):
        return queryset

    def get_object(self, pk):
        if hasattr(self, "object"):
            return self.object

        try:
            self.object = self.filter_queryset(self.get_queryset()).get(pk=pk)
        except self.get_queryset().model.DoesNotExist:
            raise Http404

        # using the content_object indirectly ensures the filter-option
        # used to embed permissions for objects
        if self.object.content_object:
            self.related_object = self.get_bmfobject(self.object.content_object.pk)
        else:
            self.related_object = None

        # self.check_object_permissions(self.request, self.object, self.related_object)

        return self.object

    def list(self, request, app=None, model=None, pk=None):
        """
        list either unattached files or files attached to another model
        (depending if ``app`` and ``model`` is set by the request uri)
        """
        if app and model and pk:
            self.related_object = self.get_bmfobject(pk)
            queryset = self.get_queryset().filter(
                is_static=False,
                content_type=self.get_bmfcontenttype(),
                content_id=self.related_object.pk
            )
        else:
            self.related_object = None
            queryset = self.get_queryset().filter(
                is_static=True,
            )
        return Response(queryset.objects.values_list('pk', flat=True))

    def list_customer(self, request):
        """
        """
        pass

    def list_project(self, request):
        """
        """
        pass

    def create(self, request, app=None, model=None, pk=None):
        """
        create a new file - attached to a document, if ``model`` and ``app``
        is set by the request uri
        """
        return Response('Not implemented')

    def detail(self, request, pk):
        """
        get the details of a document
        """
        instance = self.get_object(pk)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, pk):
        """
        delete a document
        """
        obj = self.get_object(pk)
        return Response('Not implemented %s' % obj.pk)

    def update(self, request, pk):
        """
        update the document
        """
        obj = self.get_object(pk)
        return Response('Not implemented %s' % obj.pk)

    def update_file(self, request, pk):
        """
        update only the file of the document
        """
        obj = self.get_object(pk)
        return Response('Not implemented %s' % obj.pk)

    def download(self, request, pk):
        """
        download the document (filestream-response)
        """
        obj = self.get_object(pk)

        sendtype = settings.DOCUMENT_SENDTYPE
        filename = os.path.basename(obj.file.name)
        filepath = obj.file.path
        fileuri = obj.file.url

        if not os.path.exists(filepath):
            raise Http404

        # Nginx (untested)
        if sendtype == "xaccel" and not settings.DEBUG:
            response = HttpResponse()
            response['Content-Type'] = 'application/force-download'
            response['Content-Disposition'] = 'attachment; filename=%s' % filename
            response['X-Accel-Redirect'] = fileuri
            return response

        # Lighthttpd or Apache with mod_xsendfile (untested)
        if sendtype == "xsendfile" and not settings.DEBUG:
            response = HttpResponse()
            response['Content-Type'] = 'application/force-download'
            response['Content-Disposition'] = 'attachment; filename=%s' % filename
            response['X-Sendfile'] = filepath
            return response

        # Serve file with django
        wrapper = FileWrapper(obj.file)
        response = HttpResponse(wrapper)
        response['Content-Type'] = obj.mimetype
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        response['Content-Length'] = obj.file.size
        return response