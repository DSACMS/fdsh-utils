Feature: NSC successful response

  Scenario: Request is processed successfully
    Given the NSC request is valid and a matching record exists
    When the client submits the request to the NSC retrieve endpoint
    Then the successful response matches the NSC response schema
