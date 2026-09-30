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
