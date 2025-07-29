# LoreWeave

Narrative tools and scaffolds for story weaving, ritual documentation, and echo tracing.

## Usage

Initialise the required directories:

```bash
loreweaver init
```

Run the parser and sync tools. Use `--verbose` to print each phase and `--issue-limit` to control how many GitHub issues are fetched:

```bash
loreweaver run --verbose --issue-limit 20
```
For a full list of options and command details (including where each output file is saved):
```bash
loreweaver run --help
```

Initialize a brand new EchoThreads repository using the scaffold command:

```bash
loreweaver scaffold --path /tmp/newrepo
```

`echo-scaffold` ships with EchoThreads, so the command above works even when the
package is installed via `pip`.

Run the recursive DevOps tests:

```bash
loreweaver devops-test --verbose
```

The `run` command performs post‑commit and post‑push parsing, synchronises GitHub issues and updates the RedStone registry. Parsed fragments are stored in Redis for later retrieval.

### Generated Folders

Running `init` creates a `LoreWeave` directory containing:

* `commit_results/` – files such as `plot_points.txt`, `white_feather_moments.txt`, `echoform1_data.txt` and `weekly_report.txt`.
* `intention_results/` – `intentions.yaml` storing detected commit intentions based on `intention_patterns.yaml`.
* `narrative_results/` – `narrative_elements.yaml` storing narrative elements based on `narrative_patterns.yaml`.
* `github_issues/` – GitHub issue sync logs saved as `github_issues_sync_<timestamp>.yaml`.

These result files help trace story structure and developer intent throughout the repository.

### Patterns

`intention_patterns.yaml` and `narrative_patterns.yaml` define regular expressions used to extract intentions and narrative fragments from commit messages. Editing these files allows custom detection rules.

### Intention and Narrative Extraction

Commit messages are scanned using the patterns above. Matches are written to `intention_results/intentions.yaml` and `narrative_results/narrative_elements.yaml`. These YAML files allow you to track developer intent and story beats over time.

Each entry in `intentions.yaml` lists the pattern that matched, the text snippet found and an emotional tone. You can expand `intention_patterns.yaml` with your own regex rules to capture custom signals from commit messages.

`narrative_elements.yaml` records story-related fragments like conflicts, resolutions or plot twists detected in commits. Modify `narrative_patterns.yaml` to tailor these story hooks to your workflow.

### GitHub Issue Sync and RedStone Registry

During `loreweaver run`, issues from the connected GitHub repository are fetched and transformed into memory entries. A short summary of this sync is saved under `LoreWeave/github_issues/github_issues_sync_<timestamp>.yaml` while a detailed ledger is placed under `book/_/ledgers/` for historical reference.

After syncing issues, LoreWeave refreshes its RedStone registry. The messages `Updating RedStone registry...` and `RedStone registry updated` indicate this refresh cycle and confirm that local RedStone data is current.
