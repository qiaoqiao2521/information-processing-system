import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("local_mcode", Path(__file__).parents[1] / "tools/aihot/local_mcode.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LocalMcodeTests(unittest.TestCase):
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
