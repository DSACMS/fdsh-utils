Feature: NSC search privilege failure

  Scenario: User cannot conduct a search
    Given the authenticated user does not have privileges to conduct a search
    When the client submits the request to the NSC retrieve endpoint
    Then the response code is "ME100005"
    And the response description is "This user does not have the privileges to conduct a search."
