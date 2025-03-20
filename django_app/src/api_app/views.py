from django.db import connections
from django.http import HttpResponse, JsonResponse
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin, RetrieveModelMixin,
                                   UpdateModelMixin)
from swagger.decorator import (add_description_to_test_view,
                               add_description_to_test_view2)

from .models import ApiModel
from .serializers import TestSerializer


def health_check(request):
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"message": "ok"}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_test_image(request):

    filename = "previewfile_3029449878.jpg"

    response = HttpResponse()
    response["X-Accel-Redirect"] = f"/images/{filename}"

    return response


@add_description_to_test_view
class PostListCreateView(ListModelMixin, CreateModelMixin, GenericAPIView):
    queryset = ApiModel.objects.all()
    serializer_class = TestSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


@add_description_to_test_view2
class PostRetrieveUpdateDeleteView(
    RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericAPIView
):
    queryset = ApiModel.objects.all()
    serializer_class = TestSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
