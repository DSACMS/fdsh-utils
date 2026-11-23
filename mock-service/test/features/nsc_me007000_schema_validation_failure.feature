Feature: NSC schema validation failure

  Scenario: Request has an invalid structure or format
    Given the NSC request fails schema validation
    When the client submits the request to the NSC retrieve endpoint
    Then the response code is "ME007000"
    And the response description is "Schema Validation Failure"
