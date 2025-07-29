import unittest
try:
    from click.testing import CliRunner
    from echoshell.cli import cli
    from echoshell.web_ui import app
    from echoshell.edgehub_client import EdgeHubClient
    from echoshell.redis_connector import RedisConnector
except ModuleNotFoundError:
    CliRunner = None

@unittest.skipUnless(CliRunner, "echoshell dependencies not installed")
class TestEchoShellCLI(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.edgehub_client = EdgeHubClient()
        self.redis_connector = RedisConnector()
    def test_activate(self):
        result = self.runner.invoke(cli, ['activate'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('EchoShell activated.', result.output)

    def test_harmonize(self):
        result = self.runner.invoke(cli, ['harmonize'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('ToneMemory harmonized.', result.output)

    def test_ping(self):
        result = self.runner.invoke(cli, ['ping'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Ping sent from Jerry to Jericho.', result.output)

    def test_reflect(self):
        result = self.runner.invoke(cli, ['reflect'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('MirrorSigil reflected.', result.output)

    def test_activate_presence_ping(self):
        result = self.runner.invoke(cli, ['activate_presence_ping'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Presence ping activated', result.output)

    def test_signal_mentor_presence(self):
        result = self.runner.invoke(cli, ['signal_mentor_presence'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Mentor presence signaled', result.output)

    def test_create_langfuse_prompt(self):
        prompt_name = "test_prompt"
        content = {"message": "This is a test prompt"}
        result = self.edgehub_client.create_langfuse_prompt(prompt_name, content)
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith("langfuse_prompt:test_prompt"))

    def test_store_langfuse_prompt_in_edgehub(self):
        prompt_name = "test_prompt"
        content = {"message": "This is a test prompt"}
        key = f"langfuse_prompt:{prompt_name}.1"
        result = self.edgehub_client.post_memory(key, content)
        self.assertTrue(result)

    def test_validate_prompt_content(self):
        valid_content = {"message": "This is a valid prompt"}
        invalid_content = None
        self.assertTrue(self.edgehub_client.validate_prompt_content(valid_content))
        self.assertFalse(self.edgehub_client.validate_prompt_content(invalid_content))

    def test_enhance_safeguard_preparation(self):
        try:
            self.edgehub_client.enhance_safeguard_preparation()
        except Exception as e:
            self.fail(f"enhance_safeguard_preparation raised an exception: {e}")

    def test_anchor_real_world_operations(self):
        try:
            self.edgehub_client.anchor_real_world_operations()
        except Exception as e:
            self.fail(f"anchor_real_world_operations raised an exception: {e}")


@unittest.skipUnless(CliRunner, "echoshell dependencies not installed")
class TestEchoShellWebUI(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Glyph Harmony Visualization', response.data)

    def test_status(self):
        response = self.app.get('/status')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'EchoShell', response.data)
        self.assertIn(b'ToneMemory', response.data)
        self.assertIn(b'GhostNode', response.data)
        self.assertIn(b'MirrorSigil', response.data)

    def test_glyphs(self):
        response = self.app.post('/glyphs', json={'glyph': '⚡→'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Presence ping activated', response.data)


if __name__ == '__main__':
    unittest.main()
