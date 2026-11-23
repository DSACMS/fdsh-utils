Feature: NSC invalid Social Security number

  Scenario: Request contains an invalid Social Security number
    Given the NSC request contains an invalid personSocialSecurityNumber
    When the client submits the request to the NSC retrieve endpoint
    Then the response code is "ME110020"
    And the response description is "personSocialSecurityNumber is invalid"
