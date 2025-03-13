from drf_spectacular.utils import extend_schema


def add_description_to_test_view(cls):
    get_list = cls.list
    cls.get = extend_schema(description="endpoint for getting a list of objects")(
        get_list
    )

    create_object = cls.create
    cls.post = extend_schema(description="endpoint for creating a new object")(
        create_object
    )

    return cls


def add_description_to_test_view2(cls):

    update_object = cls.update
    cls.put = extend_schema(description="endpoint for updating an object")(
        update_object
    )

    return cls
