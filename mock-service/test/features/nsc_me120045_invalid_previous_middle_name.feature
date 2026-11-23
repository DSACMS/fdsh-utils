Feature: NSC invalid previous middle name

  Scenario: Request contains an invalid previous middle name
    Given the NSC request contains an invalid previousNames.personMiddleName
    When the client submits the request to the NSC retrieve endpoint
    Then the response code is "ME120045"
    And the response description is "previousNames.personMiddleName is invalid"
