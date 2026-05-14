Feature: Wishlist CRUD operations

  Background:
    Given a registered user "wishuser" with password "wishpass123"
    And a game "Wishlist Game" on "PC" with genre "Action"
    And I am logged in as "wishuser" with password "wishpass123"

  Scenario: User can add a game to wishlist
    When I visit the game detail for "Wishlist Game"
    And I fill in the target price "15.99"
    And I submit the wishlist form
    Then I should have a wishlist item for "Wishlist Game" with target price 15.99

  Scenario: User can remove a game from wishlist
    Given I have "Wishlist Game" in my wishlist with target price 15.99
    When I click "Remove" for "Wishlist Game"
    And I confirm deletion
    Then I should not have a wishlist item for "Wishlist Game"
