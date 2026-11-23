Feature: NSC trusted data source exception

  Scenario: Trusted data source raises an unexpected exception
    Given the trusted data source raises an unexpected exception while retrieving data
    When the client submits the request to the NSC retrieve endpoint
    Then the response code is "MX005001"
    And the response description is "Unexpected Exception Occurred at Trusted Data Source"
