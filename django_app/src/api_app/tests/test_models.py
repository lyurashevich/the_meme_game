# from api_app.models import ApiModel
# from django.test import TestCase
#
#
# class TestModelTestCase(TestCase):
#     def setUp(self) -> None:
#         self.test_object = ApiModel.objects.create(name="Object")
#
#     def test_get_test_object(self) -> None:
#         test_object = ApiModel.objects.get(name="Object")
#         self.assertEqual(test_object.name, "Object")
#
#     def test_get_str_test_object(self) -> None:
#         test_object = self.test_object
#         self.assertEqual(str(test_object.name), "Object")
#
#     def test_update_test_object(self) -> None:
#         test_object = self.test_object
#         test_object.name = "Object1"
#         test_object.save()
#         self.assertEqual(test_object.name, "Object1")
#
#     def test_delete_test_object(self) -> None:
#         test_object = self.test_object
#         test_object.delete()
#         with self.assertRaises(ApiModel.DoesNotExist):
#             ApiModel.objects.get(id=test_object.id)
