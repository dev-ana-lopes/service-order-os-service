Feature: Service order saga happy path
  Scenario: Complete a service order after quote, payment, and execution events
    Given a service order was opened
    When the quote is approved
    And the payment preference is created
    And the payment is confirmed
    And the execution starts
    And the execution completes
    Then the service order status is completed
    And the saga publishes the expected events
