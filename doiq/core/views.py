import pytz
import json
import os
import uuid
from django.conf import settings
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import permission_classes, authentication_classes, api_view
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)
def get_timezones(request):
    return HttpResponse(
        content=json.dumps(pytz.common_timezones),
        content_type="application/json"
    )


@api_view(['POST'])
@authentication_classes((JSONWebTokenAuthentication,))
@permission_classes((IsAuthenticated,))
def upload(request):
    """
    uploads image from computer and save it to user storage. Using plupload front-end plugin (chunk upload)
    using ImageCanvas model to save any user images.
    :param request: HttpRequestContext
    :return:
    """
    f = request.FILES.get('file', False)
    if f:
        name = request.GET.get('name', '')
        if not name:
            name = f.name

        origin, ext = os.path.splitext(name)
        ext = ext.strip(".").lower()
        image_ext = ['png', 'jpg', 'jpeg', 'gif', 'ico', 'svg']

        if ext not in image_ext:
            return HttpResponse(
                content=json.dumps({'error': "Bad File Type"}),
                content_type='application/json',
                status=400
            )

        filename = "{0}.{1}".format(uuid.uuid4().hex[:8], ext)
        path = 'user/images/{0}/'.format(request.user.id)
        directory = os.path.join(settings.MEDIA_ROOT, path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        outfile = os.path.join(directory, filename)
        file_io = open(outfile, 'wb')
        for chunk in f.chunks():
            file_io.write(chunk)
        file_io.close()
        return Response({'file': os.path.join(path, filename)}, status=status.HTTP_201_CREATED)
    else:
        return Response({'error': "Can't upload file. Try again."}, status.HTTP_400_BAD_REQUEST)
