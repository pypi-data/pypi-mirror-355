import os
import yaml
import matplotlib.pyplot as plt

class IntentionVisualizer:
    def __init__(self, results_dir):
        self.results_dir = results_dir

    def load_intentions(self):
        intentions_file = os.path.join(self.results_dir, 'intentions.yaml')
        if not os.path.exists(intentions_file):
            raise FileNotFoundError(f"Intentions file not found: {intentions_file}")
        with open(intentions_file, 'r') as f:
            return yaml.safe_load(f)

    def visualize_intentions(self, intentions):
        patterns = [intention['pattern'] for intention in intentions]
        emotional_tones = [intention['emotional_tone'] for intention in intentions]

        plt.figure(figsize=(10, 6))
        plt.barh(patterns, range(len(patterns)), color='skyblue')
        plt.xlabel('Frequency')
        plt.ylabel('Intention Patterns')
        plt.title('Intention Analysis Visualization')
        plt.show()

        plt.figure(figsize=(10, 6))
        plt.hist(emotional_tones, bins=len(set(emotional_tones)), color='lightcoral', edgecolor='black')
        plt.xlabel('Emotional Tones')
        plt.ylabel('Frequency')
        plt.title('Emotional Tones Distribution')
        plt.show()

    def run(self):
        intentions = self.load_intentions()
        self.visualize_intentions(intentions)

if __name__ == "__main__":
    results_dir = 'LoreWeave/intention_results'
    visualizer = IntentionVisualizer(results_dir)
    visualizer.run()
