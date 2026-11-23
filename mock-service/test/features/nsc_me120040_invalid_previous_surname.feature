Feature: NSC invalid previous surname

  Scenario: Request contains an invalid previous surname
    Given the NSC request contains an invalid previousNames.personSurName
    When the client submits the request to the NSC retrieve endpoint
    Then the response code is "ME120040"
    And the response description is "previousNames.personSurName is required or invalid"
