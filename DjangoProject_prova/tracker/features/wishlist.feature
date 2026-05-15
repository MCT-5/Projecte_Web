Feature: Wishlist management

  Background:
    Given I am logged in as player1
    And there is a game Skyrim

  Scenario: Add a game to wishlist
    When I add the game to my wishlist with target price 20.00
    Then the game should be in my wishlist

  Scenario: Cannot add to wishlist when not logged in
    Given I am not logged in
    When I add the game to my wishlist with target price 20.00
    Then I should get a 302 in my face from the login page

  Scenario: Edit a wishlist item
    Given the game is in my wishlist with target price 20.00
    When I edit the wishlist item with target price 15.00
    Then the wishlist item should have target price 15.00

  Scenario: Delete a wishlist item
    Given the game is in my wishlist with target price 20.00
    When I delete the wishlist item
    Then the game should not be in my wishlist

  Scenario: Target price cannot be negative
    When I add the game to my wishlist with target price -10.00
    Then I should see an error message "Price must be positive"