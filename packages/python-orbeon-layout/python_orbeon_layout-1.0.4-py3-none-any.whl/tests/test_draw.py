
import unittest

from pathlib import Path
from python_orbeon_layout.main import layout_draw
from python_orbeon_layout.example_data import get_example_data

BASE_DIR = Path(__file__).resolve().parent.parent


class TestDraw(unittest.TestCase):

    def test_data(self):
        data = get_example_data()
        self.assertIn('sales_order_id', data)
        self.assertIn('layout_id', data)
        self.assertIn('responsavel_nome', data)
        self.assertIn('responsavel_contato', data)
        self.assertIn('data_inicio', data)
        self.assertIn('data_conclusao', data)

    def test_layout_draw(self):
        result = layout_draw(get_example_data())
        self.assertEqual(result['success'], True)
        self.assertGreater(len(result['filename']), 10)
        self.assertEqual(result['error'], None)
        self.assertIsNot(None, result['data'])

    def test_layout_draw_save_file(self):
        result = layout_draw(get_example_data(), True)
        generated_files_saved_path = BASE_DIR / 'generated_files_saved' / result['filename']
        empty = True
        if generated_files_saved_path.exists():
            if generated_files_saved_path.stat().st_size > 500:
                empty = False
        self.assertFalse(empty)

if __name__ == "__main__":
    unittest.main()
