import io
import tempfile
import sys
import importlib.util
import json
from pathlib import Path
import runpy
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch, MagicMock

spec = importlib.util.spec_from_file_location("local_mcode", Path(__file__).parents[1] / "tools/aihot/local_mcode.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LocalMcodeTests(unittest.TestCase):
    def test_server_local_uses_docker_argv_and_existing_script_selections(self):
        cases = [
            ('opencode', ['--workflow-next', '2'], 'process-workflow.ts', ['--next', '2']),
            ('opencode', ['--upstream-next', '1'], 'process-upstream-batch.ts', ['--next', '1']),
            ('opencode', ['--review', 'review-1'], 'process-upstream-reviews.ts', ['review-1']),
            ('opencode', ['--next', '3'], 'process-local-mcode.ts', ['--next', '3']),
            ('mcode', ['article-1', 'article-2'], 'process-local-mcode.ts', ['article-1', 'article-2']),
        ]
        for engine, options, script, selection in cases:
            with self.subTest(engine=engine, options=options), tempfile.TemporaryDirectory() as folder:
                child = MagicMock(stdout=io.StringIO(''))
                child.poll.return_value = child.wait.return_value = 0
                with patch.object(sys, 'argv', ['runner', '--server-local', *options]), \
                        patch.object(module.shutil, 'which', return_value='/model-cli'), \
                        patch.object(module.subprocess, 'Popen', return_value=child) as launch, \
                        patch.object(module.Path, 'home', return_value=Path(folder)), \
                        patch('sys.stdout', new_callable=io.StringIO):
                    self.assertEqual(module.main(engine=engine), 0)
                self.assertEqual(launch.call_args.args[0], [
                    'docker', 'exec', '-i', '-e', 'MCODE_STDIO_ENABLED=true',
                    '-e', 'MODEL_CALLS_ENABLED=true', '-e', 'LOCAL_CLI_PROVIDER=' + engine,
                    'muqiao-intel-api-1', 'node', 'scripts/' + script, *selection,
                ])
                self.assertIs(launch.call_args.kwargs['stdin'], subprocess.PIPE)
                self.assertIs(launch.call_args.kwargs['stdout'], subprocess.PIPE)
                self.assertFalse(launch.call_args.kwargs.get('shell', False))

    def test_legacy_ssh_transport_remains_the_default(self):
        child = MagicMock(stdout=io.StringIO(''))
        child.poll.return_value = child.wait.return_value = 0
        with patch.object(sys, 'argv', ['runner', '--host', 'custom-436', '--next', '2']), \
                patch.object(module.shutil, 'which', return_value='/opencode'), \
                patch.object(module.subprocess, 'Popen', return_value=child) as launch, \
                patch('sys.stdout', new_callable=io.StringIO):
            self.assertEqual(module.main(engine='opencode'), 0)
        self.assertEqual(launch.call_args.args[0], [
            'ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
            '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3', 'custom-436',
            'cd /opt/intelligence-hub/aihot/app && docker compose -p muqiao-intel '
            '-f docker-compose.yml -f compose.override.yaml exec -T '
            '-e MCODE_STDIO_ENABLED=true -e MODEL_CALLS_ENABLED=true '
            '-e LOCAL_CLI_PROVIDER=opencode api node scripts/process-local-mcode.ts --next 2',
        ])

    def test_opencode_user_is_only_allowed_for_server_local_opencode(self):
        for engine, options in [('opencode', []), ('mcode', ['--server-local'])]:
            with self.subTest(engine=engine), \
                    patch.object(sys, 'argv', ['runner', '--opencode-user', 'agent436', '--next', '1', *options]), \
                    patch.object(module.subprocess, 'Popen') as launch, \
                    patch('sys.stderr', new_callable=io.StringIO):
                with self.assertRaises(SystemExit) as error:
                    module.main(engine=engine)
                self.assertEqual(error.exception.code, 2)
                launch.assert_not_called()

    def test_demoted_opencode_owns_only_its_workspace_before_cli_execution(self):
        executable = '/var/lib/agent436/.local/bin/opencode'
        body = {'model': module.OPENCODE_MODEL, 'messages': [{'role': 'user', 'content': 'material'}]}
        events = [{'type': 'text', 'part': {'text': 'answer'}},
                  {'type': 'step_finish', 'part': {'reason': 'stop', 'tokens': {}}}]
        environment = dict(module.os.environ)
        with patch.object(module.pwd, 'getpwnam', return_value=SimpleNamespace(pw_uid=1436, pw_gid=1436)) as account, \
                patch.object(module.os, 'chown') as chown:
            def execute(command, **kwargs):
                self.assertEqual(command[:5], ['runuser', '-u', 'agent436', '--', executable])
                workspace = command[command.index('--dir') + 1]
                chown.assert_called_once_with(workspace, 1436, 1436)
                self.assertTrue(Path(workspace).is_dir())
                self.assertEqual(kwargs['env'], {
                    **environment, 'OPENCODE_CONFIG_CONTENT': kwargs['env']['OPENCODE_CONFIG_CONTENT'],
                })
                cfg = json.loads(kwargs['env']['OPENCODE_CONFIG_CONTENT'])
                self.assertEqual(cfg['model'], module.OPENCODE_MODEL)
                self.assertEqual(cfg['permission'], {'*': 'deny'})
                self.assertFalse(kwargs.get('shell', False))
                return subprocess.CompletedProcess(command, 0, '\n'.join(json.dumps(e) for e in events), '')
            with patch.object(module.subprocess, 'run', side_effect=execute):
                response = module.answer_opencode(body, executable, user='agent436')
        account.assert_called_once_with('agent436')
        self.assertEqual(response['choices'][0]['message']['content'], 'answer')
        self.assertEqual(dict(module.os.environ), environment)
        self.assertFalse(Path(chown.call_args.args[0]).exists())

    def test_workflow_propagates_transport_and_demoted_user_through_stdio(self):
        executable = '/var/lib/agent436/.local/bin/opencode'
        request = {'id': 'request-1', 'body': {'model': module.OPENCODE_MODEL}}
        child = MagicMock(stdout=io.StringIO(module.PREFIX + json.dumps(request) + '\n'), stdin=io.StringIO())
        child.poll.side_effect = [None, 0]
        child.wait.return_value = 0
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(sys, 'argv', ['workflow.py', '--server-local', '--opencode', executable, '--opencode-user', 'agent436']), \
                patch.dict(sys.modules, {'local_mcode': module}), \
                patch.object(module.shutil, 'which', return_value=executable) as which, \
                patch.object(module.subprocess, 'Popen', return_value=child) as launch, \
                patch.object(module, 'answer_opencode', return_value={'answer': 'mock'}) as answer, \
                patch.object(module.Path, 'home', return_value=Path(folder)), \
                patch('sys.stdout', new_callable=io.StringIO):
            with self.assertRaises(SystemExit) as result:
                runpy.run_path(str(Path(__file__).parents[1] / 'tools/aihot/workflow.py'), run_name='__main__')
            self.assertEqual(result.exception.code, 0)
            record = json.loads((Path(folder) / '.local/state/intelligence-hub-workflow/last-run.json').read_text())
        which.assert_called_once_with(executable)
        self.assertEqual(launch.call_args.args[0][:3], ['docker', 'exec', '-i'])
        self.assertEqual(launch.call_args.args[0][-3:], ['scripts/process-workflow.ts', '--next', '2'])
        answer.assert_called_once_with(request['body'], executable, user='agent436')
        self.assertEqual(json.loads(child.stdin.getvalue()), {'id': request['id'], 'response': {'answer': 'mock'}})
        self.assertEqual((record['status'], record['modelCalls']), ('completed', 1))

    def test_workflow_records_pause_and_failure_instead_of_reporting_empty_success(self):
        for remote_code, remote_status, expected in [(0, "budget-paused", "budget-paused"), (1, "failed", "failed")]:
            with tempfile.TemporaryDirectory() as folder:
                child = MagicMock()
                child.stdout = io.StringIO(json.dumps({"workflow": "test", "status": remote_status}) + "\n")
                child.poll.return_value = remote_code
                child.wait.return_value = remote_code
                with patch.object(sys, "argv", ["runner", "--workflow-next", "2"]), patch.object(module.shutil, "which", return_value="/opencode"), patch.object(module.subprocess, "Popen", return_value=child) as launch, patch.object(module.Path, "home", return_value=Path(folder)):
                    self.assertEqual(module.main(engine="opencode"), remote_code)
                self.assertIn("process-workflow.ts", launch.call_args.args[0][-1])
                record = json.loads((Path(folder) / ".local/state/intelligence-hub-workflow/last-run.json").read_text())
                self.assertEqual(record["status"], expected)
                self.assertEqual(record["modelCalls"], 0)
                self.assertEqual(record["exitCode"], remote_code)
                self.assertTrue(record["finishedAt"])

    def test_json_requests_require_a_final_object_and_multiple_steps_are_rejected(self):
        body = {"model": module.OPENCODE_MODEL, "messages": [{"role": "system", "content": "Return a score"}, {"role": "user", "content": "material"}], "response_format": {"type": "json_object"}}
        events = [{"type": "text", "part": {"text": '{"attentionScore":80}'}}, {"type": "step_finish", "part": {"reason": "stop", "tokens": {}}}]
        with patch.object(module.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "\n".join(json.dumps(e) for e in events), "")) as run:
            module.answer_opencode(body, "/opencode")
        cfg = json.loads(run.call_args.kwargs["env"]["OPENCODE_CONFIG_CONTENT"])
        self.assertIn("只返回一个", cfg["agent"]["news"]["prompt"])
        self.assertEqual(cfg["agent"]["news"]["steps"], 2)
        self.assertEqual(cfg["agent"]["news"]["effort"], "low")
        with patch.object(module.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "\n".join(json.dumps(e) for e in events + [events[-1]]), "")):
            with self.assertRaises(RuntimeError):
                module.answer_opencode(body, "/opencode")

    def test_opencode_event_stream_preserves_answer_and_denies_tools(self):
        events = [{"type": "text", "part": {"text": '{"attentionScore":88}'}},
                  {"type": "step_finish", "part": {"reason": "stop", "tokens": {"total": 15, "input": 12, "output": 3}}}]
        with patch.object(module.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "\n".join(json.dumps(e) for e in events), "")) as run:
            response = module.answer_opencode({"model": module.OPENCODE_MODEL, "messages": [{"role": "system", "content": "score system"}, {"role": "user", "content": "material"}], "temperature": 0.1}, "/opencode")
        self.assertEqual(response["choices"][0]["message"]["content"], events[0]["part"]["text"])
        self.assertEqual(response["usage"]["total_tokens"], 15)
        self.assertIn("--pure", run.call_args.args[0])
        cfg = json.loads(run.call_args.kwargs["env"]["OPENCODE_CONFIG_CONTENT"])
        self.assertEqual(cfg["agent"]["news"]["prompt"], "score system")
        self.assertEqual(cfg["agent"]["news"]["temperature"], 0.1)
        self.assertEqual(cfg["agent"]["news"]["steps"], 2)
        self.assertEqual(cfg["permission"], {"*": "deny"})
        self.assertEqual(cfg["enabled_providers"], ["minimax-cn-coding-plan"])
        self.assertEqual(cfg["small_model"], module.OPENCODE_MODEL)
        self.assertIn("--title", run.call_args.args[0])
        self.assertEqual(run.call_args.kwargs["input"], "material")

    def test_opencode_errors_and_incomplete_streams_cannot_publish(self):
        body = {"model": module.OPENCODE_MODEL, "messages": [{"role": "user", "content": "test"}]}
        for event in ({"type": "error"}, {"type": "tool_use"}, {"type": "text", "part": {"text": "unfinished"}}):
            with patch.object(module.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps(event), "")):
                with self.assertRaises(RuntimeError):
                    module.answer_opencode(body, "/opencode")
        with self.assertRaisesRegex(ValueError, "Unexpected OpenCode"):
            module.answer_opencode({**body, "model": "minimax/MiniMax-M3"}, "/opencode")

    def test_opencode_length_stop_is_rejected_with_safe_diagnostics(self):
        body = {"model": module.OPENCODE_MODEL, "messages": [{"role": "user", "content": "test"}]}
        event = {"type": "step_finish", "part": {"reason": "length"}}
        with patch.object(module.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps(event), "")):
            with self.assertRaisesRegex(RuntimeError, 'reason=length'):
                module.answer_opencode(body, "/opencode")
        event['part']['reason'] = 'sensitive-provider-diagnostic'
        with patch.object(module.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps(event), "")):
            with self.assertRaisesRegex(RuntimeError, 'reason=unknown') as failure:
                module.answer_opencode(body, "/opencode")
        self.assertNotIn('sensitive-provider', str(failure.exception))

    def test_preserves_answer_and_usage_without_tools_or_credentials(self):
        result = {"status": "succeeded", "output": '{"attentionScore":88}', "runId": "r",
                  "model": {"providerId": "minimax", "modelId": module.MODEL.split("/", 1)[1]},
                  "usage": {"inputTokens": 12, "outputTokens": 3, "totalTokens": 15}}
        with patch.object(module.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps(result), "")) as run:
            response = module.answer_request({"model": module.MODEL, "messages": [{"role": "user", "content": "score"}]}, "/mcode")
        self.assertEqual(response["choices"][0]["message"]["content"], result["output"])
        self.assertEqual(response["usage"]["total_tokens"], 15)
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--permission") + 1], "off")
        self.assertEqual(command[command.index("--max-steps") + 1], "1")
        self.assertIn("--input", command)

    def test_fails_closed_on_provider_change_failure_or_images(self):
        body = {"model": module.MODEL, "messages": [{"role": "user", "content": "test"}]}
        with patch.object(module.subprocess, "run", return_value=subprocess.CompletedProcess([], 4, "", "secret-provider-details")):
            with self.assertRaisesRegex(RuntimeError, "mcode exited 4") as error:
                module.answer_request(body, "/mcode")
            self.assertNotIn("secret-provider-details", str(error.exception))
        with self.assertRaisesRegex(ValueError, "Unexpected model"):
            module.answer_request({**body, "model": "other"}, "/mcode")
        with self.assertRaisesRegex(ValueError, "text only"):
            module.answer_request({**body, "messages": [{"content": [{"type": "image_url"}]}]}, "/mcode")


if __name__ == "__main__":
    unittest.main()
