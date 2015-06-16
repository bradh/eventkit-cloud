import logging
import os
import shutil
import pdb
from datetime import datetime
from collections import OrderedDict
from django.http import HttpResponse
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from django.db.models import FileField
from django.db import Error, transaction

from rest_framework import views
from rest_framework import viewsets
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import mixins
from rest_framework import status
from rest_framework import renderers
from rest_framework import generics
from rest_framework import filters
from rest_framework.reverse import reverse
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.serializers import ValidationError
from rest_framework.pagination import PageNumberPagination

from .renderers import HOTExportApiRenderer
from .validators import validate_bbox_params, validate_search_bbox
from .pagination import JobLinkHeaderPagination
from jobs import presets
from jobs.models import Job, ExportFormat, Region, RegionMask, ExportConfig, Tag
from tasks.models import ExportRun, ExportTask, ExportTaskResult
from serializers import (JobSerializer, ExportFormatSerializer,
                         RegionSerializer, RegionMaskSerializer,
                         ExportRunSerializer, ExportConfigSerializer, TagSerializer)

from tasks.task_runners import ExportTaskRunner

from hot_exports import settings

# Get an instance of a logger
logger = logging.getLogger(__name__)

renderer_classes = (JSONRenderer, HOTExportApiRenderer)


class JobViewSet(viewsets.ModelViewSet):
    """
    ## Job API Endpoint.
    Endpoint for job creation and managment.
    
    More docs here...
    """
    from serializers import JobSerializer
    
    serializer_class = JobSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    parser_classes = (FormParser, MultiPartParser, JSONParser)
    lookup_field = 'uid'
    pagination_class = JobLinkHeaderPagination

    def get_queryset(self):
        return Job.objects.all()
    
    def list(self, request, uid=None, *args, **kwargs):
        params = self.request.QUERY_PARAMS.get('bbox', None)
        logger.debug(params)
        if params == None:
            queryset = Job.objects.all()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)
            else:
                serializer = JobSerializer(queryset,  many=True, context={'request': request})
                return Response(serializer.data)
        if (len(params.split(',')) < 4):
            errors = OrderedDict()
            errors['id'] = 'missing_bbox_parameter'
            errors['message'] = 'Missing bounding box parameter'
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            extents = params.split(',')   
            data = {'xmin': extents[0],
                    'ymin': extents[1],
                    'xmax': extents[2],
                    'ymax': extents[3]
            }
            try:
                bbox_extents = validate_bbox_params(data)
                bbox = validate_search_bbox(bbox_extents)
                queryset = Job.objects.filter(the_geom__intersects=bbox)
                page = self.paginate_queryset(queryset)
                if page is not None:
                    serializer = self.get_serializer(page, many=True, context={'request': request})
                    return self.get_paginated_response(serializer.data)
                else:
                    serializer = JobSerializer(queryset,  many=True, context={'request': request})
                    return Response(serializer.data)
            except ValidationError as e:
                logger.debug(e.detail)
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
                
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if (serializer.is_valid()):
            # add the export formats
            formats = request.data.getlist('formats')
            preset = request.data.get('preset')
            translation = request.data.get('translation')
            transform = request.data.get('transform')
            export_formats = []
            job = None
            for slug in formats:
                try:
                    export_format = ExportFormat.objects.get(slug=slug)
                    export_formats.append(export_format)
                except ExportFormat.DoesNotExist as e:
                    logger.warn('Export format with uid: {0} does not exist'.format(slug))
            if len(export_formats) > 0:
                # save the job
                try:
                    with transaction.atomic():
                        job = serializer.save()
                        job.formats = export_formats
                        # add the configurations
                        if preset:
                            config = ExportConfig.objects.get(uid=preset)
                            job.configs.add(config)
                            preset_path = settings.BASE_DIR + config.upload.url
                            # TODO: check if user tags to be merged with defaults
                            parser = presets.PresetParser(preset=preset_path)
                            tags = parser.parse(merge_with_defaults=False)
                            for key in tags:
                                tag = Tag.objects.create(
                                    name = key,
                                    geom_types = tags[key]
                                )
                                job.tags.add(tag)
                        else:
                            # use default tags
                            tags = presets.DEFAULT_TAGS
                            for key in tags:
                                tag = Tag.objects.create(
                                    name = key,
                                    geom_types = tags[key]
                                )
                                job.tags.add(tag)   
                        if translation:
                            config = ExportConfig.objects.get(uid=translation)
                            job.configs.add(config)
                        if transform:
                            config = ExportConfig.objects.get(uid=transform)
                            job.configs.add(config)
                except Error as e:
                    error_data = OrderedDict()
                    error_data['id'] = 'server_error'
                    error_data['message'] = 'Error creating export job: {0}'.format(e)
                    return Response(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                error_data = OrderedDict()
                error_data['formats'] = ['Invalid format uid(s).']
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
            
            # run the tasks
            # catch exceptions here..
            task_runner = ExportTaskRunner()
            job_uid = str(job.uid)
            task_runner.run_task(job_uid=job_uid)
            running = JobSerializer(job, context={'request': request})
            return Response(running.data, status=status.HTTP_202_ACCEPTED)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class ExportFormatViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ### ExportFormat API endpoint.
    Endpoint exposing the supported export formats.
    
    """
    serializer_class = ExportFormatSerializer
    permission_classes = (permissions.AllowAny,)
    queryset = ExportFormat.objects.all()
    lookup_field = 'slug'
    

class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ### Region API endpoint.
    Endpoint exposing the supported regions.
    """
    serializer_class = RegionSerializer
    permission_classes = (permissions.AllowAny,)
    queryset = Region.objects.all()
    lookup_field = 'uid'
    

class RegionMaskViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View set to return a mask of the export regions.
    """
    serializer_class = RegionMaskSerializer
    permission_classes = (permissions.AllowAny,)
    queryset = RegionMask.objects.all()


class ExportRunViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View to return serialized Run data.
    """
    serializer_class = ExportRunSerializer
    permission_classes = (permissions.AllowAny,)
    lookup_field = 'uid'
    
    def get_queryset(self):
         return ExportRun.objects.all()
        
    def retrieve(self, request, uid=None, *args, **kwargs):
        queryset = ExportRun.objects.filter(uid=uid)
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExportConfigViewSet(viewsets.ModelViewSet):
    """
    Endpoint for operations on export configurations.
    Lists all available configuration files.
    """
    serializer_class = ExportConfigSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = ExportConfig.objects.all()
    lookup_field = 'uid'
    

class PresetViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Returns the list of PRESET configuration files.
    """
    CONFIG_TYPE = 'PRESET'
    serializer_class = ExportConfigSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = ExportConfig.objects.filter(config_type=CONFIG_TYPE)
    lookup_field = 'uid'


class TranslationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Returns the list of TRANSLATION configuration files.
    """
    CONFIG_TYPE = 'TRANSLATION'
    serializer_class = ExportConfigSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = ExportConfig.objects.filter(config_type=CONFIG_TYPE)
    lookup_field = 'uid'


class TransformViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Returns the list of TRANSFORM configuration files.
    """
    CONFIG_TYPE = 'TRANSFORM'
    serializer_class = ExportConfigSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = ExportConfig.objects.filter(config_type=CONFIG_TYPE)
    lookup_field = 'uid'
        