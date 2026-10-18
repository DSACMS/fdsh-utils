Feature: NSC invalid middle name

  Scenario: Request contains an invalid middle name
    Given the NSC request contains an invalid personMiddleName
    When the client submits the request to the NSC retrieve endpoint
    Then the response code is "ME110050"
    And the response description is "personMiddleName is invalid"
