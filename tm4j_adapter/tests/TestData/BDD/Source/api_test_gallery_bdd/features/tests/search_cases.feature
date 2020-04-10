@gallery_api @search_gallery_cases
Feature: We should be able to search gallery cases

  @CST-1283 @P0 @search_cases_action_availability
  Scenario Outline: CST-T135_As a doctor I want to have "search-cases" action available for me

    Given I access "gallery" api as "<user>"
     Then I am at "<home>" resource
      And It has action "search-cases"

    Examples: users
      | user         | home       |
      | default_user | DoctorHome |
      | go_doctor    | DoctorHome |


  @CST-1283 @P0 @search_cases_action_availability
  Scenario: CST-T136_As an admin I want to have "search-cases" action NOT available for me

    Given I access "gallery" api as "default_user"
     Then I am at "DoctorHome" resource
      And I bookmark it as "DoctorHome"

    When I access "gallery" api as "admin"
    Then I am at "AdminHome" resource
     And It does not have action "search-cases"
    When I return to "DoctorHome"
    Then I set client for bookmark "DoctorHome"
    Then I expect response "403" after step
      """
          When I use action "search-cases"
      """


  @CST-1283 @P1 @search_not_incorrect_param
  Scenario Outline: CST-T137_As a doctor I want anonymized to have only boolean values in "search-cases" action

    Given I access "gallery" api as "default_user"
     Then I am at "DoctorHome" resource
     Then I expect response "400" after step
        '''
          When I use action "search-cases"
            """
              anonymized: <anonymized>
            """
        '''

    Examples: values
      | anonymized  |
      | 123         |
      | random_text |


  @CST-1283 @P1 @search_not_anonym_cases_by_default
  Scenario: CST-T138_As a doctor I want "search-cases" action to find notanonymized cases by default

    Given I access "gallery" api as "default_user"
     Then I am at "DoctorHome" resource
      And I use action "search-cases"
      And I am at "CaseNotAnonymizedCollection" resource


  @CST-1283 @P1 @check_gallery_case_collections_type
  Scenario Outline: CST-T139_As a doctor I want "search-cases" action to find correct case collection depending on anonymized flag

    Given I access "gallery" api as "default_user"
     Then I search <search> gallery cases
      And I am at "<collection>" resource
      And Class of all entities is "<entity>"
      And Its link "self" has substring "/cases?anonymized=<anonymized>&size=10&page=0" in url

    Examples: collections
      | anonymized | search        | collection                  | entity            |
      | true       | anonymized    | CaseAnonymizedCollection    | CaseAnonymized    |
      | false      | notanonymized | CaseNotAnonymizedCollection | CaseNotAnonymized |


  @CST-1283 @P1 @check_anonymized_cases
  Scenario Outline: CST-T140_As a doctor I want cases to have required properties and actions depending on anonymized flag

    Given I access "gallery" api as "default_user"
     Then I search <anonymized> gallery cases
      And It has at least "1" entities
     Then I go to first entity "item"
      And It has actions [<actions>]
      And It has following properties <properties>

    Examples: collection_properties
      | anonymized    | actions                                                                                      | properties                                         |
      | anonymized    | "get-case-info", "download-assets"                                                           | "anonymizedStatus"                                 |
      | notanonymized | "get-case-info", "download-assets", "remove-case-from-gallery", "add-case-to-global_gallery" | "globalGalleryStatus", "inShowCase", "patientName" |
