Feature: NSC invalid previous given name

  Scenario: Request contains an invalid previous given name
    Given the NSC request contains an invalid previousNames.personGivenName
    When the client submits the request to the NSC retrieve endpoint
    Then the response code is "ME120030"
    And the response description is "previousNames.personGivenName is required or invalid"
