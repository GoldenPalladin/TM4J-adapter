from behave import *

from common_api_tests.steps import (commons, actions)

use_step_matcher('re')


@step('I search\s?(?P<case_type>anonymized|notanonymized)? gallery cases')
def search_gallery_case_paging_as_doctor(context, case_type):
    commons.check_resource_class(context, 'DoctorHome')
    context.pre_saved = {'anonymized': True if case_type == 'anonymized' else False}
    actions.use_action(context, 'search-cases', pre_saved=True)