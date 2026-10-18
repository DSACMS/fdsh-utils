Feature: NSC unexpected system exception

  Scenario: An unexpected system exception occurs
    Given the mock service encounters an unexpected system exception
    When the client submits the request to the NSC retrieve endpoint
    Then the response code is "MX009000"
    And the response description is "Unexpected System Exception"
