import unittest
from gupshup.client import Client

class TestClient(unittest.TestCase):
    def test_instancia(self):
        client = Client("App", "token", "5561...", "id")
        self.assertIsNotNone(client)

if __name__ == "__main__":
    unittest.main()