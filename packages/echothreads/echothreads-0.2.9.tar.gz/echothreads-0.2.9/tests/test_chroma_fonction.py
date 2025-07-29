import unittest
try:
    from chroma_fonction import ChromaFonction
except ModuleNotFoundError:  # optional dependency
    ChromaFonction = None

@unittest.skipUnless(ChromaFonction, "chroma_fonction module not installed")
class TestChromaFonction(unittest.TestCase):

    def setUp(self):
        self.chroma_fonction = ChromaFonction()

    def test_capture_finger_placement(self):
        self.chroma_fonction.capture_finger_placement("E", 3)
        self.assertIn(("E", 3), self.chroma_fonction.finger_placements)
        self.assertEqual(self.chroma_fonction.get_chromatic_scale(), ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])
        self.assertEqual(self.chroma_fonction.get_power_notes(), ["C", "E", "G"])

    def test_capture_breath_control(self):
        self.chroma_fonction.capture_breath_control(5, 2)
        self.assertIn((5, 2), self.chroma_fonction.breath_controls)
        self.assertEqual(self.chroma_fonction.get_chromatic_scale(), ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])
        self.assertEqual(self.chroma_fonction.get_power_notes(), ["C", "E", "G"])

    def test_chromatic_scale_generation(self):
        self.chroma_fonction.capture_finger_placement("A", 5)
        self.chroma_fonction.capture_breath_control(3, 1)
        self.assertEqual(self.chroma_fonction.get_chromatic_scale(), ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])

    def test_power_notes_detection(self):
        self.chroma_fonction.capture_finger_placement("D", 7)
        self.chroma_fonction.capture_breath_control(4, 3)
        self.assertEqual(self.chroma_fonction.get_power_notes(), ["C", "E", "G"])

if __name__ == "__main__":
    unittest.main()
