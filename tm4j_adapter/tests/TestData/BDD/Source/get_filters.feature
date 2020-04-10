@gallery_api @get_gallery_filters
Feature: We should be able to get user filters

  @CST-1360 @P0 @get_filters_action_availability
  Scenario Outline: As a doctor I want to have "filters" action available for me

    Given I access "gallery" api as "<user>"
     When I am at "<home>" resource
     Then It has action "filters"
     And ---newline---
     And ---another newline---

    Examples: users
      | user         | home       |
      | default_user | DoctorHome |
      | go_doctor    | DoctorHome |


  @CST-1280 @P0 @anonimized_filters_info
  Scenario Outline: As doctor I want to to get the list of anonymized filters with assets
    Given I access "gallery" api as "default_user"
      And I save action_link to "filters" as "filters_link" with additional queryString "?anonymized=true" parameters
      And I access action "<{filters_link}>" by direct link with method "GET"
      And It has properties
 	     """
 	       anonymized: true
 	     """
    When I am at "Filters" resource
     And It has "1" entity "item" with property "name" equal to "<filter_name>"
    Then I go to entity "item" with property "name" equal to "<filter_name>"
    Then It has entities "value" with properties
              """
                - "value" : "INITIAL_PHOTOS"
                - "value" : "FINAL_PHOTOS"
                - "value" : "TREATMENT_FILE"
              """
    Examples:
      | filter_name |
      | assets      |

  @CST-1280 @P0 @non_anonimized_filters_info
  Scenario Outline: As doctor I want to to get the list of nonanonymized filters with assets
    Given I access "gallery" api as "default_user"
      And I save action_link to "filters" as "filters_link" with additional queryString "?anonymized=false" parameters
      And I access action "<{filters_link}>" by direct link with method "GET"
      And It has properties
 	     """
 	       anonymized: false
 	     """
    When I am at "Filters" resource
     And It has "1" entity "item" with property "name" equal to "<filter_name>"
    Then I go to entity "item" with property "name" equal to "<filter_name>"
    Then It has entities "value" with properties
              """
                - "value" : "INITIAL_SCAN"
                - "value" : "PROGRESS_SCAN"
                - "value" : "FINAL_SCAN"
                - "value" : "INITIAL_PHOTOS"
                - "value" : "PROGRESS_PHOTOS"
                - "value" : "FINAL_PHOTOS"
                - "value" : "X_RAYS"
                - "value" : "TREATMENT_FILE"
              """
    Examples:
      | filter_name |
      | assets      |
