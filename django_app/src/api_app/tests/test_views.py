# from api_app.models import ApiModel
# from django.test import TestCase
# from rest_framework import status
# from rest_framework.test import APIClient
#
#
# class ApiModelEndpointTests(TestCase):
#
#     def setUp(self) -> None:
#         self.client = APIClient()
#         self.model_instance = ApiModel.objects.create(name="test")
#         self.url = "/api/tests/"
#
#     def test_get_list_of_objects(self) -> None:
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 1)
#
#     def test_create_test_object(self) -> None:
#         data = {"name": "new_obj"}
#         response = self.client.post(self.url, data, format="json")
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(ApiModel.objects.count(), 2)
#
#
# class ApiModelEndpointTests2(TestCase):
#
#     def setUp(self) -> None:
#         self.client = APIClient()
#         self.model_instance = ApiModel.objects.create(name="object")
#         self.url = f"/api/test/{self.model_instance.id}/"
#
#     def test_get_object_by_id(self) -> None:
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     def test_update_test_object(self) -> None:
#         data = {"name": "upd_obj"}
#         response = self.client.put(self.url, data, format="json")
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.model_instance.refresh_from_db()
#         self.assertEqual(self.model_instance.name, "upd_obj")
#
#     def test_delete_object(self) -> None:
#         response = self.client.delete(self.url)
#         self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
#         self.assertEqual(ApiModel.objects.count(), 0)
#
#     def test_patch_object(self) -> None:
#         data = {"name": "patch"}
#         response = self.client.put(self.url, data, format="json")
#         self.model_instance.refresh_from_db()
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(self.model_instance.name, "patch")
