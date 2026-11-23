Feature: NSC authentication or authorization failure

  Scenario: Request authentication or authorization fails
    Given the request has an authentication or authorization failure
    When the client submits the request to the NSC retrieve endpoint
    Then the response code is "ME110010"
    And the response description is "Authentication or authorization failure"
