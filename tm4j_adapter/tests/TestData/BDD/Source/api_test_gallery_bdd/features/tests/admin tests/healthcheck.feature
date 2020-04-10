@gallery_api
Feature: As admin I have healthcheck link which i can follow and check current state

  @CST-1053 @P0 @pr @smoke @galley_api_healthcheck
  Scenario: As admin I want to access Gallery API healthcheck and check it's property and health is OK

    Given I use "default" client for "admin" for "gallery" api
     When I get to healthcheck info
     Then Its property "systemName" is equal to "gallery"
      And Its property "health" is equal to "OK"
      And Its property "buildInfo" is not empty
      And Its property "buildInfo.buildDate" is not empty
      And Its property "buildInfo.appVersion" is not empty
      And Its property "buildInfo.revision" is not empty
      And Its property "buildInfo.branch" is not empty
