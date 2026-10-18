Feature: NSC invalid as-of date

  Scenario: Request contains an invalid as-of date
    Given the NSC request contains an invalid asOfDate
    When the client submits the request to the NSC retrieve endpoint
    Then the response code is "ME110075"
    And the response description is "asOfDate is invalid"
