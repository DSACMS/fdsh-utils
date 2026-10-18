Feature: NSC invalid given name

  Scenario: Request has a missing or invalid given name
    Given the NSC request has a missing or invalid personGivenName
    When the client submits the request to the NSC retrieve endpoint
    Then the response code is "ME110040"
    And the response description is "personGivenName is required or invalid"
