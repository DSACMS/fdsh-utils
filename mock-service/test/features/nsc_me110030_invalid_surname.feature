Feature: NSC invalid surname

  Scenario: Request has a missing or invalid surname
    Given the NSC request has a missing or invalid personSurName
    When the client submits the request to the NSC retrieve endpoint
    Then the response code is "ME110030"
    And the response description is "personSurName is required or invalid"
