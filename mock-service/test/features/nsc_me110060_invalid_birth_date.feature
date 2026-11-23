Feature: NSC invalid birth date

  Scenario: Request contains an invalid birth date
    Given the NSC request contains an invalid personBirthDate
    When the client submits the request to the NSC retrieve endpoint
    Then the response code is "ME110060"
    And the response description is "personBirthDate is invalid"
