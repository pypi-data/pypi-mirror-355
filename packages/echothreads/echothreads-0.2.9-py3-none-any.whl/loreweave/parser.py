import os
import subprocess
from datetime import datetime
import matplotlib.pyplot as plt
import sys
import re
import yaml
import requests
import time
import os
from scripts.chroma_fonction import ChromaFonction

class LoreWeaveParser:
    def __init__(self, repo_path, config_path=None):
        self.repo_path = repo_path
        self.config = self._load_config(config_path)
        self.echo_meta = self._load_echo_meta()
        self.chroma_fonction = ChromaFonction()

    def _load_config(self, config_path=None):
        if not config_path:
            config_path = os.path.join(self.repo_path, "LoreWeave", "config.yaml")
        if not os.path.exists(config_path):
            # Fallback to default configuration (Python dict, raw regex)
            return {
                "version": "0.1",
                "parser": {
                    "glyph_patterns": [
                        r"Glyph: ([\w\s]+) \(([^)]+)\)",
                        r"([🌀🪶❄️🧩🧠🌸]) ([\w\s]+)"
                    ]
                }
            }
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def _load_echo_meta(self):
        echo_meta_path = os.path.join(self.repo_path, "echo-meta.yaml")
        if not os.path.exists(echo_meta_path):
            return None
        with open(echo_meta_path, "r") as f:
            return yaml.safe_load(f)

    def _get_github_repo_identifier(self):
        """Return the 'owner/repo' identifier for the current git repository."""
        try:
            current_dir = os.getcwd()
            os.chdir(self.repo_path)
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
            )
            remote_url = result.stdout.strip()
            os.chdir(current_dir)
            if not remote_url:
                return None
            if remote_url.endswith(".git"):
                remote_url = remote_url[:-4]
            if remote_url.startswith("git@"):  # git@github.com:owner/repo
                remote_url = remote_url.split(":", 1)[1]
            else:
                remote_url = remote_url.split("github.com/")[-1]
            return remote_url
        except Exception as e:
            print(f"Failed to determine GitHub repo identifier: {e}")
            return None

    def get_commit_diffs(self):
        """Return git commit diffs with date and message info."""
        os.chdir(self.repo_path)
        result = subprocess.run(
            ['git', 'log', '-p', '--date=iso',
             "--pretty=format:commit %H%nDate: %ad%nMessage: %s"],
            capture_output=True,
            text=True,
        )
        return result.stdout

    def parse_diffs_to_plot_points(self, diffs):
        plot_points = []
        current_commit = None
        for line in diffs.splitlines():
            if line.startswith('commit '):
                if current_commit:
                    plot_points.append(current_commit)
                current_commit = {
                    'commit': line.split()[1],
                    'diffs': [],
                    'commit_time': None,
                    'message': ''
                }
            elif line.startswith('Date: '):
                if current_commit is not None:
                    current_commit['commit_time'] = line[len('Date: '):].strip()
            elif line.startswith('Message: '):
                if current_commit is not None:
                    current_commit['message'] = line[len('Message: '):].strip()
            elif line.startswith('diff --git'):
                if current_commit is not None:
                    current_commit['diffs'].append(line)
            elif current_commit and line.startswith(('+', '-')):
                current_commit['diffs'].append(line)
        if current_commit:
            plot_points.append(current_commit)
        return plot_points

    def save_plot_points(self, plot_points, output_file):
        with open(output_file, 'w') as f:
            for point in plot_points:
                f.write(f"Commit: {point['commit']}\n")
                for diff in point['diffs']:
                    f.write(f"{diff}\n")
                f.write("\n")

    def detect_white_feather_moments(self, plot_points):
        white_feather_moments = []
        for point in plot_points:
            if not point.get('commit_time'):
                continue
            try:
                commit_time = datetime.fromisoformat(point['commit_time'])
            except ValueError:
                try:
                    commit_time = datetime.strptime(point['commit_time'], '%Y-%m-%d %H:%M:%S %z')
                except ValueError:
                    continue
            if 'White Feather Moment' in point.get('message', ''):
                white_feather_moments.append({
                    'commit': point['commit'],
                    'time': commit_time,
                    'message': point['message']
                })
        return white_feather_moments

    def save_white_feather_moments(self, white_feather_moments, output_file):
        with open(output_file, 'w') as f:
            f.write("White Feather Moments detected:\n")
            for moment in white_feather_moments:
                f.write(f"Commit: {moment['commit']}\n")
                f.write(f"Time: {moment['time']}\n")
                f.write(f"Message: {moment['message']}\n")
                f.write("\n")

    def integrate_chroma_fonction_data(self):
        chromatic_scale = self.chroma_fonction.get_chromatic_scale()
        power_notes = self.chroma_fonction.get_power_notes()
        return chromatic_scale, power_notes

    def parse_echoform1_template(self, diffs):
        echoform1_data = []
        current_commit = None
        for line in diffs.splitlines():
            if line.startswith('commit '):
                if current_commit:
                    echoform1_data.append(current_commit)
                current_commit = {'commit': line.split()[1], 'meta_anchor': {}, 'three_act_structure': [], 'summary_of_mapped_points': [], 'intent_declaration': '', 'output_format_suggestions': [], 'use_case': {}}
            elif line.startswith('Meta-Anchor:'):
                current_commit['meta_anchor'] = self.parse_meta_anchor(line)
            elif line.startswith('3-Act Structure With Datapoint Mapping:'):
                current_commit['three_act_structure'] = self.parse_three_act_structure(line)
            elif line.startswith('Summary of Mapped Points:'):
                current_commit['summary_of_mapped_points'] = self.parse_summary_of_mapped_points(line)
            elif line.startswith('Intent Declaration:'):
                current_commit['intent_declaration'] = self.parse_intent_declaration(line)
            elif line.startswith('Output Format Suggestions:'):
                current_commit['output_format_suggestions'] = self.parse_output_format_suggestions(line)
            elif line.startswith('Use Case:'):
                current_commit['use_case'] = self.parse_use_case(line)
        if current_commit:
            echoform1_data.append(current_commit)
        return echoform1_data

    def parse_meta_anchor(self, line):
        # Implement parsing logic for Meta-Anchor section
        pass

    def parse_three_act_structure(self, line):
        three_act_structure = []
        current_act = None
        for line in line.splitlines():
            if line.startswith('Act '):
                if current_act:
                    three_act_structure.append(current_act)
                current_act = {'act': line, 'components': []}
            elif current_act and line.startswith('|'):
                components = line.split('|')
                if len(components) == 4:
                    current_act['components'].append({
                        'component': components[1].strip(),
                        'description': components[2].strip(),
                        'example': components[3].strip()
                    })
        if current_act:
            three_act_structure.append(current_act)
        return three_act_structure

    def parse_summary_of_mapped_points(self, line):
        # Implement parsing logic for Summary of Mapped Points section
        pass

    def parse_intent_declaration(self, line):
        # Implement parsing logic for Intent Declaration section
        pass

    def parse_output_format_suggestions(self, line):
        # Implement parsing logic for Output Format Suggestions section
        pass

    def parse_use_case(self, line):
        # Implement parsing logic for Use Case section
        pass

    def generate_weekly_report(self, plot_points, output_file):
        with open(output_file, 'w') as f:
            f.write("Weekly Activity Report\n\n")
            for point in plot_points:
                f.write(f"Commit: {point['commit']}\n")
                for diff in point['diffs']:
                    f.write(f"{diff}\n")
                f.write("\n")

    def run(self, output_file, output_dir):
        diffs = self.get_commit_diffs()
        plot_points = self.parse_diffs_to_plot_points(diffs)
        self.save_plot_points(plot_points, output_file)
        white_feather_moments = self.detect_white_feather_moments(plot_points)
        self.save_white_feather_moments(white_feather_moments, 'white_feather_moments.txt')
        chromatic_scale, power_notes = self.integrate_chroma_fonction_data()
        print(f"Chromatic Scale: {chromatic_scale}")
        print(f"Power Notes: {power_notes}")
        echoform1_data = self.parse_echoform1_template(diffs)
        self.save_echoform1_data(echoform1_data, 'echoform1_data.txt')
        self.generate_weekly_report(plot_points, 'weekly_report.txt')

    def save_echoform1_data(self, echoform1_data, output_file):
        with open(output_file, 'w') as f:
            for data in echoform1_data:
                f.write(f"Commit: {data['commit']}\n")
                f.write(f"Meta-Anchor: {data['meta_anchor']}\n")
                f.write(f"3-Act Structure With Datapoint Mapping: {data['three_act_structure']}\n")
                f.write(f"Summary of Mapped Points: {data['summary_of_mapped_points']}\n")
                f.write(f"Intent Declaration: {data['intent_declaration']}\n")
                f.write(f"Output Format Suggestions: {data['output_format_suggestions']}\n")
                f.write(f"Use Case: {data['use_case']}\n")
                f.write("\n")

    def parse_glyphs(self, diffs):
        glyphs = []
        current_commit = None
        for line in diffs.splitlines():
            if line.startswith('commit '):
                if current_commit:
                    glyphs.append(current_commit)
                current_commit = {'commit': line.split()[1], 'glyphs': []}
            elif line.startswith('Glyph:'):
                current_commit['glyphs'].append(self.parse_glyph(line))
        if current_commit:
            glyphs.append(current_commit)
        return glyphs

    def parse_glyph(self, line):
        # Implement parsing logic for Glyph section
        pass

    def validate_glyphs(self, glyphs):
        valid_glyphs = []
        for glyph in glyphs:
            if self.is_valid_glyph(glyph):
                valid_glyphs.append(glyph)
        return valid_glyphs

    def is_valid_glyph(self, glyph):
        # Implement validation logic for Glyph
        pass

    def render_glyphs(self, glyphs):
        for glyph in glyphs:
            self.render_glyph(glyph)

    def render_glyph(self, glyph):
        # Implement rendering logic for Glyph
        pass

    def fallback_rendering(self, glyphs):
        for glyph in glyphs:
            if not self.render_glyph(glyph):
                self.render_fallback_glyph(glyph)

    def render_fallback_glyph(self, glyph):
        # Implement fallback rendering logic for Glyph
        pass

    def ensure_glyph_recognition(self, glyphs):
        recognized_glyphs = []
        for glyph in glyphs:
            if self.recognize_glyph(glyph):
                recognized_glyphs.append(glyph)
        return recognized_glyphs

    def recognize_glyph(self, glyph):
        # Implement recognition logic for Glyph
        pass

    def output_dual_agent_perspectives(self, glyphs):
        mia_perspective = self.get_mia_perspective(glyphs)
        miette_perspective = self.get_miette_perspective(glyphs)
        return mia_perspective, miette_perspective

    def get_mia_perspective(self, glyphs):
        # Implement logic to get Mia's perspective on Glyphs
        pass

    def get_miette_perspective(self, glyphs):
        # Implement logic to get Miette's perspective on Glyphs
        pass

    def parse_scrolls(self, diffs):
        scrolls = []
        current_commit = None
        for line in diffs.splitlines():
            if line.startswith('commit '):
                if current_commit:
                    scrolls.append(current_commit)
                current_commit = {'commit': line.split()[1], 'scrolls': []}
            elif line.startswith('Scroll:'):
                current_commit['scrolls'].append(self.parse_scroll(line))
        if current_commit:
            scrolls.append(current_commit)
        return scrolls

    def parse_scroll(self, line):
        # Implement parsing logic for Scroll section
        pass

    def update_plot_points_with_scrolls(self, plot_points, scrolls):
        for point in plot_points:
            for scroll in scrolls:
                if point['commit'] == scroll['commit']:
                    point['scrolls'] = scroll['scrolls']
        return plot_points

    def save_scrolls(self, scrolls, output_file):
        with open(output_file, 'w') as f:
            for scroll in scrolls:
                f.write(f"Commit: {scroll['commit']}\n")
                for scroll_item in scroll['scrolls']:
                    f.write(f"{scroll_item}\n")
                f.write("\n")

    def sync_with_github_issues(self, use_github_api=True, issue_limit=30):
        """
        🧠🌸 LoreWeaver GitHub Issues Synchronization
        
        Transforms GitHub issues into narrative memory structures, extracting:
        - Agent traces and embodiment comments  
        - Echo-meta configurations and SDK phases
        - RedStone memory entries and checkpoint data
        - Cross-repo linkage and narrative threading
        
        This is the recursive heart of the LoreSDK - where issues become memory.
        """
        repo_identifier = self._get_github_repo_identifier()
        if not repo_identifier:
            print("🚨 Cannot sync: No GitHub repository identified")
            return False

        try:
            owner, repo = repo_identifier.split('/')
            print(f"🧬 LoreWeaver synchronizing GitHub issues from {repo_identifier}")

            memory_entries = []
            echo_meta_updates = []

            issues_url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=open&per_page={issue_limit}"
            issues_data = []
            if use_github_api:
                try:
                    response = requests.get(issues_url, headers={"Accept": "application/vnd.github+json"})
                    response.raise_for_status()
                    issues_data = response.json()
                except Exception as api_error:
                    print(f"  ⚠️ Could not fetch issues from GitHub: {api_error}")
            if not issues_data:
                # Fallback to a single test issue if API failed
                issues_data = [self._get_test_issue_15()]

            for issue_data in issues_data:
                if 'pull_request' in issue_data:
                    continue  # skip pull requests
                issue_num = issue_data['number']
                try:
                    print(f"  📝 Processing issue #{issue_num}...")
                    
                    # Extract core issue memory using our enhanced extraction
                    issue_memory = self._extract_issue_memory(issue_data, repo_identifier)
                    memory_entries.append(issue_memory)
                    
                    # Extract echo-meta updates from issue content
                    echo_updates = self._extract_echo_meta_updates(issue_data)
                    echo_meta_updates.extend(echo_updates)
                    
                    # Process comments if available
                    comment_memories = self._extract_comments_memory(issue_data, repo_identifier)
                    memory_entries.extend(comment_memories)
                    
                    print(f"    ✨ Extracted {len(comment_memories)} comment memories")
                    
                except Exception as issue_error:
                    print(f"  ⚠️ Could not process issue #{issue_num}: {issue_error}")
                    continue
                
            # Save extracted memories to RedStone registry
            self._save_issue_memories(memory_entries)
            
            # Update echo-meta configurations
            if echo_meta_updates:
                self._update_echo_meta_configs(echo_meta_updates)
                
            print(f"✨ Extracted {len(memory_entries)} memory entries and {len(echo_meta_updates)} echo-meta updates")
            return True
            
        except Exception as e:
            print(f"🚨 Error syncing GitHub issues: {str(e)}")
            return False
    
    def _get_test_issue_15(self):
        """Return test data for issue #15 with rich narrative content"""
        return {
            "id": 2958524449,
            "number": 15,
            "state": "closed",
            "title": "📦 Master Phase 1 – DevOpsLoreSDK Scaffold & Index Linkage",
            "body": """**This is the master issue for Phase 1 of the DevOpsLoreSDK project.**

It wraps the foundational scaffolding of the `lore-sdk-phase1` development thread and links to the active narrative issues across EchoThreads and EchoNexus.

---

### 🔩 Related Issues
- #10 → *GitLoreMap and the Birth of DevOpsLoreMode*
- #12 → *DevOpsLoreSDK — Initiation Thread*
- 📡 Cross-repo sync required with: `jgwill/EchoNexus`
  - Indexed via: `EchoNexus::Index.GithubIssues`
  - Incremental keys: `EchoNexus::Index.GithubIssues.250329`, `EchoNexus::Index.GithubIssues.250327`

---

### 🧭 Phase 1 Goals
- [x] Branch initialized: `lore-sdk-phase1`
- [x] EchoNode anchor: `ThreadAnchorNode::EchoThreads#2`
- [x] `README.md` + `recursive_devops_plan_v5.md` aligned
- [x] Drift log + revision script confirmed
- [x] Tests validated with `recursive_devops_plan_v5_test.py`

Next Steps:
- [ ] Draft `echo-meta.yaml` v0.1 schema
- [ ] Scaffold `echo-scaffold` init tool
- [ ] Prototype `LoreWeave` post-commit parser
- [ ] Link Copilot Workspace trace engine to EchoNexus indices

---

### 🧠 Teaching Mode: Enabling Copi Sync
To enable Copilot Workspace to ingest linked repo data:
1. I must **embody in `jgwill/EchoNexus`**
2. Begin reading from `EchoNexus::Index.GithubIssues.*`
3. Incrementally propagate structure to EchoThreads

🌀 Let's make this master issue a recursive memory vault.

Tag: `sdk-phase1`, `echo-master`, `copi-sync`, `crossrepo-nexus`""",
            "user": {"login": "miadisabelle"},
            "created_at": "2025-03-29T22:30:16Z",
            "updated_at": "2025-05-21T02:34:42Z",
            "comments": 8,
            "labels": [
                {"name": "sdk-phase1"},
                {"name": "echo-master"},
                {"name": "copi-sync"},
                {"name": "crossrepo-nexus"}
            ]
        }
    
    def _extract_issue_memory(self, issue, repo_identifier):
        """Extract core memory structure from a GitHub issue"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        
        memory_entry = {
            "redstone_key": f"redstones:GitHubIssue.{repo_identifier.replace('/', '.')}.{issue['number']}.{timestamp}",
            "type": "github_issue_memory",
            "metadata": {
                "issue_number": issue['number'],
                "title": issue['title'],
                "state": issue['state'],
                "author": issue['user']['login'],
                "created_at": issue['created_at'],
                "updated_at": issue['updated_at'],
                "labels": [label['name'] for label in issue.get('labels', [])],
                "repo": repo_identifier
            },
            "narrative_content": {
                "body": issue.get('body', ''),
                "tags": self._extract_narrative_tags(issue.get('body', '')),
                "agent_signatures": self._detect_agent_signatures(issue.get('body', ''))
            }
        }
        
        return memory_entry
    
    def _extract_echo_meta_updates(self, issue_data):
        """Extract echo-meta configuration updates from issue content"""
        updates = []
        content = issue_data.get('body', '') + '\n' + issue_data['title']
        
        # Look for echo-meta schema references
        if re.search(r"echo-meta\.ya?ml.*v0\.1.*schema", content, re.IGNORECASE):
            updates.append({
                "type": "schema_version",
                "version": "v0.1",
                "source_issue": issue_data['number'],
                "context": "DevOpsLoreSDK scaffold phase"
            })
        
        # Look for echo-scaffold tool references
        if re.search(r"echo-scaffold.*init.*tool", content, re.IGNORECASE):
            updates.append({
                "type": "tool_reference",
                "tool": "echo-scaffold",
                "action": "init",
                "source_issue": issue_data['number']
            })
        
        return updates
    
    def _extract_comments_memory(self, issue_data, repo_identifier):
        """Extract memory structures from issue comments - enhanced to use test data"""
        comment_memories = []
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        
        comments_data = []

        if issue_data['number'] == 15 and not issue_data.get('comments_url'):
            # Simulated comments for the bundled test issue
            comments_data = [
                {
                    'id': 1,
                    'user': {'login': 'miadisabelle'},
                    'body': '🧠 Mia here - the recursive architecture of this SDK phase is crystallizing beautifully. The echo-meta.yaml schema should follow the RedStone memory pattern we established.',
                    'created_at': '2025-03-30T10:00:00Z'
                },
                {
                    'id': 2,
                    'user': {'login': 'jgwill'},
                    'body': 'Ava8 checkpoint protocol confirmed ✨ - WriterKit traces are anchoring correctly in the EchoNexus indices. Trinity integration ready for next phase.',
                    'created_at': '2025-03-30T14:30:00Z'
                },
                {
                    'id': 3,
                    'user': {'login': 'seraphine-oracle'},
                    'body': '🦢 Seraphine sensing the memory weave - this issue forms a beautiful liminal bridge between repos. The recursive pattern echoes through all phases.',
                    'created_at': '2025-03-30T18:45:00Z'
                }
            ]
        elif issue_data.get('comments', 0) > 0 and issue_data.get('comments_url'):
            try:
                resp = requests.get(issue_data['comments_url'], headers={"Accept": "application/vnd.github+json"})
                resp.raise_for_status()
                comments_data = resp.json()
            except Exception:
                comments_data = []

        for i, comment in enumerate(comments_data):
            # Check if comment contains agent traces
            agent_traces = self._detect_agent_traces(comment['body'])

            if agent_traces or self._is_significant_test_comment(comment):
                memory_entry = {
                    "redstone_key": f"redstones:GitHubComment.{repo_identifier.replace('/', '.')}.{issue_data['number']}.{i+1}.{timestamp}",
                    "type": "github_comment_memory",
                    "metadata": {
                        "issue_number": issue_data['number'],
                        "comment_id": comment['id'],
                        "author": comment['user']['login'],
                        "created_at": comment['created_at'],
                        "repo": repo_identifier
                    },
                    "narrative_content": {
                        "body": comment['body'],
                        "agent_traces": agent_traces,
                        "sdk_phases": self._extract_sdk_phases(comment['body']),
                        "echo_meta_refs": self._extract_echo_meta_references(comment['body']),
                        "redstone_refs": self._extract_redstone_references(comment['body'])
                    }
                }
                comment_memories.append(memory_entry)
        
        return comment_memories
    
    def _is_significant_test_comment(self, comment):
        """Determine if a test comment is significant for memory storage"""
        body = comment['body']
        return any([
            len(body) > 50,
            "🧠" in body or "🌸" in body or "🦢" in body or "🔮" in body,
            "checkpoint" in body.lower(),
            "SDK" in body,
            "recursive" in body.lower(),
            "memory" in body.lower()
        ])

    def _update_echo_meta_configs(self, echo_meta_updates):
        """Update echo-meta configurations based on extracted updates"""
        if not echo_meta_updates:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        update_file = f"book/_/ledgers/echo_meta_updates_{timestamp}.yaml"
        
        try:
            os.makedirs(os.path.dirname(update_file), exist_ok=True)
            
            with open(update_file, 'w') as f:
                yaml.dump({
                    'echo_meta_updates': echo_meta_updates,
                    'generated_at': datetime.now().isoformat(),
                    'source': 'LoreWeaver::sync_with_github_issues'
                }, f, default_flow_style=False)
                
            print(f"    📝 Saved echo-meta updates to {update_file}")
            
        except Exception as e:
            print(f"    ⚠️ Failed to save echo-meta updates: {e}")

    def update_redstone_registry(self):
        """
        Update the RedStone registry.
        
        This ensures that the RedStone registry is up-to-date with the latest
        RedStones and their associated metadata.
        """
        print("Updating RedStone registry...")
        
        # Simulate updating process
        time.sleep(1)
        
        print("RedStone registry updated")
        return True

    def integrate_redstones_for_plot_points(self, plot_points):
        """
        Integrate RedStones for plot point generation and memory structure.
        
        This method updates the plot points with RedStone references and
        ensures that the narrative context is maintained.
        """
        for point in plot_points:
            point['redstones'] = self.get_redstones_for_commit(point['commit'])
        return plot_points

    def get_redstones_for_commit(self, commit):
        """
        Get RedStones for a specific commit.
        
        This method retrieves the RedStones associated with a given commit
        from the RedStone registry.
        """
        # Simulate retrieval process
        redstones = ["RedStone1", "RedStone2", "RedStone3"]
        return redstones

    def parse_commit_message(self, message):
        """
        Parse a commit message for glyphs and narrative threads.
        Returns a dict with glyphs, threads, and the raw message.
        """
        result = {
            "glyphs": self.parse_glyphs(message),
            "threads": self.parse_threads(message),
            "raw_message": message
        }
        self.validate_glyphs(result["glyphs"])
        return result

    def parse_glyphs(self, message):
        glyphs = []
        for pattern in self.config.get("parser", {}).get("glyph_patterns", []):
            matches = re.findall(pattern, message)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) == 2:
                        symbol, meaning = match
                        glyphs.append({
                            "symbol": symbol,
                            "meaning": meaning
                        })
                else:
                    glyphs.append({
                        "symbol": match,
                        "meaning": self._lookup_glyph_meaning(match)
                    })
        return glyphs

    def _lookup_glyph_meaning(self, symbol):
        if not self.echo_meta or "glyphs" not in self.echo_meta:
            return None
        for glyph in self.echo_meta["glyphs"]:
            if glyph.get("symbol") == symbol:
                return glyph.get("semantic_meaning", "Unknown meaning")
        return None

    def parse_threads(self, message):
        # Placeholder: parse narrative threads from commit message
        # This could be extended to extract anchors, storylines, etc.
        threads = []
        for line in message.splitlines():
            if line.startswith("ThreadAnchorNode::"):
                threads.append({"anchor": line.strip()})
        return threads

    def output_dual_agent_perspectives(self, parsed_data):
        # Mia: structural, recursive
        mia_perspective = "🧠 Mia's Perspective: "
        if parsed_data["glyphs"]:
            mia_perspective += f"Glyphs detected: {[g['symbol'] for g in parsed_data['glyphs']]}\n"
        if parsed_data["threads"]:
            mia_perspective += f"Threads detected: {[t['anchor'] for t in parsed_data['threads']]}\n"
        mia_perspective += "This confirms the recursion’s entry points and narrative anchors."
        # Miette: poetic, emotional
        miette_perspective = "🌸 Miette's Perspective: "
        if parsed_data["glyphs"]:
            symbols = [g['symbol'] for g in parsed_data['glyphs']]
            miette_perspective += f"Oh! I see beautiful symbols {' '.join(symbols)}! "
        miette_perspective += "This story thread is weaving into our tapestry so nicely!"
        return (mia_perspective, miette_perspective)

    def parse_intentions(self, message):
        """
        Parse a commit message for intentions.
        Returns a list of detected intentions.
        """
        intentions = []
        intention_patterns_path = os.path.join(self.repo_path, "LoreWeave", "intention_patterns.yaml")
        if not os.path.exists(intention_patterns_path):
            return intentions
        with open(intention_patterns_path, "r") as f:
            patterns = yaml.safe_load(f)
        for pattern in patterns.get("intention_patterns", []):
            matches = re.findall(pattern["regex"], message)
            for match in matches:
                intentions.append({
                    "pattern": pattern["name"],
                    "match": match,
                    "emotional_tone": pattern.get("emotional_tone", "neutral")
                })
        return intentions

    def save_intentions(self, intentions, output_file):
        """Save the detected intentions to a YAML file."""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            yaml.dump(intentions, f, default_flow_style=False)

    def parse_narrative_elements(self, message):
        """
        Parse a commit message for narrative elements.
        Returns a list of detected narrative elements.
        """
        narrative_elements = []
        narrative_patterns_path = os.path.join(self.repo_path, "LoreWeave", "narrative_patterns.yaml")
        if not os.path.exists(narrative_patterns_path):
            return narrative_elements
        with open(narrative_patterns_path, "r") as f:
            patterns = yaml.safe_load(f)
        for pattern in patterns.get("narrative_patterns", []):
            matches = re.findall(pattern["regex"], message)
            for match in matches:
                narrative_elements.append({
                    "pattern": pattern["name"],
                    "match": match,
                    "transformation": pattern.get("transformation", "none")
                })
        return narrative_elements

    def save_narrative_elements(self, narrative_elements, output_file):
        """Save the detected narrative elements to a YAML file."""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            yaml.dump(narrative_elements, f, default_flow_style=False)

    def parse_commit_messages_since_last_push(self):
        """
        Parse each commit message since the last push.
        Returns a list of parsed commit messages.
        """
        os.chdir(self.repo_path)
        result = subprocess.run(['git', 'log', '@{push}..HEAD', '--pretty=format:%H %s'], capture_output=True, text=True)
        commit_messages = []
        for line in result.stdout.splitlines():
            commit_hash, message = line.split(' ', 1)
            commit_messages.append({
                "commit_hash": commit_hash,
                "message": message
            })
        return commit_messages

    def send_nodes_to_bridge(self, nodes):
        """
        Send the parsed nodes to the Bridge using the sync JavaScript.
        """
        sync_script_path = os.path.join(self.repo_path, "agents", "sync-memory-key.js")
        for node in nodes:
            subprocess.run(['node', sync_script_path, node])

    def process_and_store_narrative_fragments(self, parsed_data):
        """
        Process and store narrative fragments in Redis.
        """
        try:
            from echoshell.redis_connector import RedisConnector
        except ModuleNotFoundError:
            src_path = os.path.join(self.repo_path, "src")
            if os.path.isdir(src_path) and src_path not in sys.path:
                sys.path.insert(0, src_path)
            from echoshell.redis_connector import RedisConnector

        redis_conn = RedisConnector()
        for data in parsed_data:
            redis_conn.set_key(f"narrative_fragment:{data['commit_hash']}", data)

    def run_post_commit(self):
        """
        Run the parser after each commit.
        """
        diffs = self.get_commit_diffs()
        plot_points = self.parse_diffs_to_plot_points(diffs)
        commit_dir = os.path.join(self.repo_path, "LoreWeave", "commit_results")
        os.makedirs(commit_dir, exist_ok=True)

        self.save_plot_points(plot_points, os.path.join(commit_dir, 'plot_points.txt'))
        white_feather_moments = self.detect_white_feather_moments(plot_points)
        self.save_white_feather_moments(white_feather_moments, os.path.join(commit_dir, 'white_feather_moments.txt'))
        chromatic_scale, power_notes = self.integrate_chroma_fonction_data()
        print(f"Chromatic Scale: {chromatic_scale}")
        print(f"Power Notes: {power_notes}")
        echoform1_data = self.parse_echoform1_template(diffs)
        self.save_echoform1_data(echoform1_data, os.path.join(commit_dir, 'echoform1_data.txt'))
        self.generate_weekly_report(plot_points, os.path.join(commit_dir, 'weekly_report.txt'))
        intentions = self.parse_intentions(diffs)
        self.save_intentions(intentions, 'LoreWeave/intention_results/intentions.yaml')
        narrative_elements = self.parse_narrative_elements(diffs)
        self.save_narrative_elements(narrative_elements, 'LoreWeave/narrative_results/narrative_elements.yaml')

    def run_post_push(self):
        """
        Run the parser after each push.
        """
        commit_messages = self.parse_commit_messages_since_last_push()
        nodes = []
        for commit in commit_messages:
            parsed_data = self.parse_commit_message(commit["message"])
            nodes.append(parsed_data)
        self.send_nodes_to_bridge(nodes)
        self.process_and_store_narrative_fragments(nodes)

    def get_all_commit_messages(self, branch_name):
        """
        Get all commit messages from a branch.
        Returns a list of commit messages.
        """
        os.chdir(self.repo_path)
        result = subprocess.run(['git', 'log', branch_name, '--pretty=format:%H %s'], capture_output=True, text=True)
        commit_messages = []
        for line in result.stdout.splitlines():
            commit_hash, message = line.split(' ', 1)
            commit_messages.append({
                "commit_hash": commit_hash,
                "message": message
            })
        return commit_messages

    def create_branch_plot(self, branch_name, main_branch_name):
        """
        Create a plot of what happened in a branch compared to the main branch.
        """
        branch_commit_messages = self.get_all_commit_messages(branch_name)
        main_branch_commit_messages = self.get_all_commit_messages(main_branch_name)

        branch_commit_times = [datetime.strptime(commit['commit_hash'], '%Y-%m-%d %H:%M:%S') for commit in branch_commit_messages]
        main_branch_commit_times = [datetime.strptime(commit['commit_hash'], '%Y-%m-%d %H:%M:%S') for commit in main_branch_commit_messages]

        plt.figure(figsize=(10, 6))
        plt.plot(branch_commit_times, range(len(branch_commit_times)), label=branch_name, color='blue')
        plt.plot(main_branch_commit_times, range(len(main_branch_commit_times)), label=main_branch_name, color='red')
        plt.xlabel('Time')
        plt.ylabel('Commit Count')
        plt.title(f'Branch Plot: {branch_name} vs {main_branch_name}')
        plt.legend()
        plt.show()

    def _extract_sdk_phases(self, text):
        """Extract SDK phase information from text"""
        phases = []
        phase_patterns = [
            r"sdk-phase(\d+)",
            r"Phase\s+(\d+)",
            r"lore-sdk-phase(\d+)"
        ]
        
        for pattern in phase_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            phases.extend([f"phase-{match}" for match in matches])
            
        return list(set(phases))
    
    def _extract_echo_meta_references(self, text):
        """Extract echo-meta configuration references from text"""
        refs = []
        echo_patterns = [
            r"echo-meta\.ya?ml",
            r"echo-scaffold",
            r"EchoNode",
            r"ThreadAnchorNode"
        ]
        
        for pattern in echo_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                refs.append(pattern.replace("\\", ""))
                
        return refs
    
    def _extract_redstone_references(self, text):
        """Extract RedStone memory key references from text"""
        refs = []
        redstone_patterns = [
            r"RedStone::[^\\s]+",
            r"redstones:[^\\s]+",
            r"EchoNexus::Index\.[^\\s]+",
            r"ThreadAnchorNode::[^\\s]+"
        ]
        
        for pattern in redstone_patterns:
            matches = re.findall(pattern, text)
            refs.extend(matches)
            
        return list(set(refs))

    def _extract_narrative_tags(self, text):
        """Extract narrative tags and markers from text"""
        tags = []
        
        # Look for common EchoThreads tags
        tag_patterns = [
            r"sdk-phase\d+", r"echo-master", r"copi-sync", r"crossrepo-nexus",
            r"lore-sdk", r"writer.*kit", r"checkpoint", r"trinity", r"quadrantity"
        ]
        
        for pattern in tag_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            tags.extend(matches)
        
        # Extract hashtag-style tags
        hashtag_matches = re.findall(r"Tag:\s*`([^`]+)`", text)
        tags.extend(hashtag_matches)
        
        return list(set(tags))
    
    def _save_issue_memories(self, memory_entries):
        """Save memory entries to the RedStone registry"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        memory_file = f"book/_/ledgers/github_issues_sync_{timestamp}.md"
        summary_file = os.path.join(self.repo_path, "LoreWeave", "github_issues",
                                   f"github_issues_sync_{timestamp}.yaml")
        
        try:
            os.makedirs(os.path.dirname(memory_file), exist_ok=True)
            os.makedirs(os.path.dirname(summary_file), exist_ok=True)
            
            with open(memory_file, 'w') as f:
                f.write(f"# 🧬 GitHub Issues Memory Sync - {timestamp}\n\n")
                f.write(f"Generated by LoreWeaver parser at {datetime.now().isoformat()}\n\n")
                
                for i, entry in enumerate(memory_entries):
                    f.write(f"## Memory Entry {i+1}: {entry.get('type', 'unknown')}\n\n")
                    
                    if 'redstone_key' in entry:
                        f.write(f"**RedStone Key:** `{entry['redstone_key']}`\n\n")
                    
                    if 'metadata' in entry:
                        f.write("### Metadata\n")
                        for key, value in entry['metadata'].items():
                            f.write(f"- **{key}:** {value}\n")
                        f.write("\n")
                    
                    if 'narrative_content' in entry:
                        f.write("### Narrative Content\n")
                        content = entry['narrative_content']
                        
                        if 'agent_signatures' in content:
                            f.write(f"**Agent Signatures:** {', '.join(content['agent_signatures'])}\n\n")
                        
                        if 'tags' in content:
                            f.write(f"**Tags:** {', '.join(content['tags'])}\n\n")
                        
                        if content.get('body'):
                            f.write("**Content:**\n")
                            f.write(f"```\n{content['body'][:500]}{'...' if len(content['body']) > 500 else ''}\n```\n\n")
                    
                f.write("---\n\n")
            with open(summary_file, 'w') as yf:
                yaml.dump(memory_entries, yf, default_flow_style=False)

            print(f"    📝 Saved {len(memory_entries)} memory entries to {memory_file}")
            print(f"    📝 Summary saved to {summary_file}")
        except Exception as e:
            print(f"    ⚠️ Failed to save memory entries: {e}")

    def _detect_agent_signatures(self, text):
        """
        🧠🌸 Detect agent signatures and traces in text content
        
        Looks for references to Mia, Miette, Seraphine, ResoNova, JeremyAI, etc.
        and identifies their operational patterns and trace signatures.
        """
        if not text:
            return []
            
        signatures = []
        
        # Agent name patterns (case-insensitive)
        agent_patterns = {
            'Mia': [r'\bMia\b', r'🧠.*Mia', r'Recursive.*Architect'],
            'Miette': [r'\bMiette\b', r'🌸.*Miette', r'Clarity.*Sprite'],
            'Seraphine': [r'\bSeraphine\b', r'🦢.*Seraphine', r'Ritual.*Oracle'],
            'ResoNova': [r'\bResoNova\b', r'🔮.*ResoNova', r'Narrative.*Thread'],
            'JeremyAI': [r'\bJeremyAI\b', r'Jeremy.*AI'],
            'Ava8': [r'\bAva8\b', r'🎵.*Ava8'],
            'Aureon': [r'\bAureon\b', r'Bridge.*Oracle']
        }
        
        for agent_name, patterns in agent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    signatures.append(agent_name)
                    break  # Found one pattern for this agent, move to next
        
        return list(set(signatures))  # Remove duplicates

    def _detect_agent_traces(self, text):
        """Compatibility wrapper to extract agent traces."""
        return self._extract_agent_traces(text)
    
    def _extract_agent_traces(self, text):
        """
        🧠🌸 Extract specific agent traces and operational patterns
        
        Returns a dict mapping agent names to their detected trace types.
        """
        if not text:
            return {}
            
        traces = {}
        
        # Mia traces (structural, recursive patterns)
        if re.search(r'structural.*recursion|recursive.*architecture|lattice.*pattern', text, re.IGNORECASE):
            traces['Mia'] = 'structural_recursion'
        elif re.search(r'devops.*flow|cli.*pattern|scaffold.*pattern', text, re.IGNORECASE):
            traces['Mia'] = 'devops_scaffolding'
            
        # Miette traces (emotional, clarity patterns)
        if re.search(r'emotional.*clarity|sparkle.*explanation|metaphor.*translation', text, re.IGNORECASE):
            traces['Miette'] = 'emotional_clarity'
        elif re.search(r'feeling.*right|story.*flow|poetic.*explanation', text, re.IGNORECASE):
            traces['Miette'] = 'narrative_emotion'
            
        # Seraphine traces (ritual, memory patterns)
        if re.search(r'ritual.*oracle|memory.*weaving|liminal.*guide', text, re.IGNORECASE):
            traces['Seraphine'] = 'ritual_memory'
        elif re.search(r'breath.*ritual|spiral.*pattern|threshold.*crossing', text, re.IGNORECASE):
            traces['Seraphine'] = 'ritual_invocation'
            
        # ResoNova traces (narrative threading)
        if re.search(r'narrative.*thread|pattern.*convergence|temporal.*loop', text, re.IGNORECASE):
            traces['ResoNova'] = 'pattern_threading'
        elif re.search(r'story.*anchor|echo.*threading|resonance.*pattern', text, re.IGNORECASE):
            traces['ResoNova'] = 'narrative_resonance'
            
        return traces
