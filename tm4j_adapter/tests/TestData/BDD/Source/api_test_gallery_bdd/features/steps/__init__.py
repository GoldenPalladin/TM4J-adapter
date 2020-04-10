import common_api_tests
from api_test_gallery_bdd.features.steps import (gallery)

from common_api_tests.lib.custom_matchers import *
matchers.register_type(wait=parse_wait,
                       sd=parse_strint,
                       to=parse_to_resource,
                       property=parse_with_property,
                       or_value=parse_or_value,
                       havent=parse_if_i_havent,
                       pre_saved_params=parse_with_pre_saved_params,
                       list=TypeBuilder.with_many(parse_strint, listsep=','))
