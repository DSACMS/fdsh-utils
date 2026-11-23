Feature: NSC unexpected response code

  Scenario: Trusted service returns an unsupported response code
    Given the trusted service returns an unknown or unsupported response code
    When the client submits the request to the NSC retrieve endpoint
    Then the response code is "MX009999"
    And the response description is "Unexpected Response Code"
