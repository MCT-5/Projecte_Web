Feature: Game CRUD operations

  Background:
    Given a registered user "testuser" with password "testpass123"
    And I am logged in as "testuser" with password "testpass123"

  Scenario: Authenticated user can add a new game
    When I go to add a new game
    And I fill in the game title "Test Game" platform "PC" genre "Action"
    And I submit the game form
    Then I should see "Game added successfully"
    And the game "Test Game" should exist in the database

  Scenario: Unauthenticated user is redirected from add game
    Given I am not logged in
    When I visit "/game/add/"
    Then I should see "login"

  Scenario: User can edit an existing game
    Given a game "Editable Game" on "PC" with genre "RPG"
    When I visit the game detail for "Editable Game"
    And I click "Edit Game"
    And I clear the title and type "Edited Game"
    And I submit the game form
    Then the game "Edited Game" should exist in the database

  Scenario: User can delete a game
    Given a game "DeleteMe" on "PC" with genre "Puzzle"
    When I visit the game detail for "DeleteMe"
    And I click "Delete Game"
    And I confirm deletion
    Then the game "DeleteMe" should not exist in the database
