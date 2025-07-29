import os
import yaml
import matplotlib.pyplot as plt

class NarrativeVisualizer:
    def __init__(self, results_dir):
        self.results_dir = results_dir

    def load_narrative_elements(self):
        narrative_elements_file = os.path.join(self.results_dir, 'narrative_elements.yaml')
        if not os.path.exists(narrative_elements_file):
            raise FileNotFoundError(f"Narrative elements file not found: {narrative_elements_file}")
        with open(narrative_elements_file, 'r') as f:
            return yaml.safe_load(f)

    def visualize_narrative_elements(self, narrative_elements):
        patterns = [element['pattern'] for element in narrative_elements]
        transformations = [element['transformation'] for element in narrative_elements]

        plt.figure(figsize=(10, 6))
        plt.barh(patterns, range(len(patterns)), color='skyblue')
        plt.xlabel('Frequency')
        plt.ylabel('Narrative Patterns')
        plt.title('Narrative Transformation Visualization')
        plt.show()

        plt.figure(figsize=(10, 6))
        plt.hist(transformations, bins=len(set(transformations)), color='lightcoral', edgecolor='black')
        plt.xlabel('Transformations')
        plt.ylabel('Frequency')
        plt.title('Narrative Transformations Distribution')
        plt.show()

    def run(self):
        narrative_elements = self.load_narrative_elements()
        self.visualize_narrative_elements(narrative_elements)

if __name__ == "__main__":
    results_dir = 'LoreWeave/narrative_results'
    visualizer = NarrativeVisualizer(results_dir)
    visualizer.run()
