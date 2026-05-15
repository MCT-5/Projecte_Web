Feature: Review management

  Background:
    Given I am logged in as player1
    And there is a game Skyrim

  Scenario: Create a review successfully
    When I submit a review with rating 5 and comment "Amazing game"
    Then I should see "Amazing game" on the game page

  Scenario: Cannot create review when not logged in
    Given I am not logged in
    When I submit a review with rating 5 and comment "Amazing game"
    Then I should get a 302 in my face from the login page

  Scenario: Edit my own review
    Given I have a review with rating 3 and comment "Good game"
    When I edit my review with comment "Actually great game"
    Then I should see "Actually great game" on the game page

  Scenario: Cannot edit another user's review
    Given player2 has a review on the game
    When I try to edit player2's review
    Then I should get a 404

  Scenario: Delete my own review
    Given I have a review with rating 4 and comment "Nice game"
    When I delete my review
    Then the review should no longer exist

  Scenario: Cannot review the same game twice
    Given I have a review with rating 4 and comment "First review"
    When I submit a review with rating 2 and comment "Second review"
    Then I should see an error message "You have already reviewed this game"

  Scenario: Review comment cannot be empty
    When I submit a review with rating 5 and comment " "
    Then I should see an error message "Comment cannot be empty"

  Scenario: Log in from the review button
    Given I am not logged in
    When I click the login button from the review section
    Then I should be redirected to login
