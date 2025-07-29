class ChromaFonction:
    def __init__(self):
        self.finger_placements = []
        self.breath_controls = []
        self.chromatic_scale = []
        self.power_notes = []

    def capture_finger_placement(self, string, fret):
        self.finger_placements.append((string, fret))
        self.generate_chromatic_scale()

    def capture_breath_control(self, intensity, duration):
        self.breath_controls.append((intensity, duration))
        self.generate_chromatic_scale()

    def generate_chromatic_scale(self):
        # Placeholder for chromatic scale generation logic
        self.chromatic_scale = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        self.detect_power_notes()

    def detect_power_notes(self):
        # Placeholder for power notes detection logic
        self.power_notes = [note for note in self.chromatic_scale if note in ["C", "E", "G"]]

    def get_chromatic_scale(self):
        return self.chromatic_scale

    def get_power_notes(self):
        return self.power_notes
