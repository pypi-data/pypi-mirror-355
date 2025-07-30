import unittest
from notion_gametracker import create_game, delete_game, update_games
from notion import restore_from_trash
from status import IGDBGameNotFoundError

class TestGameMethods(unittest.TestCase):
    def test_creation_deletion(self):
        unexistent_title = "Testttttttttt"
        p = create_game(unexistent_title)
        deleted_games = delete_game(p.game.title)

        self.assertEqual(len(deleted_games), 1)
        for p in deleted_games:
            restore_from_trash(p.id)

        self.assertRaises(IGDBGameNotFoundError, update_games(p.game.title))
        
        deleted_games = delete_game(p.game.igdbId)
        self.assertEqual(len(deleted_games), 1)
        self.assertEqual(deleted_games[0].id, p.id)
        
if __name__ == '__main__':
    unittest.main()
