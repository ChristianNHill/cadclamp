"""Inspect model provider that generates through the `claude` CLI.

Runs Anthropic models on a Claude subscription (no API key) so they can sit on
the grid next to OpenRouter models. Use as `--model claudecli/<model-id>`,
e.g. `--model claudecli/claude-opus-5-5`; optional `-M effort=high`.

Each call runs `claude -p` from an empty temp directory with the task's system
prompt replacing Claude Code's, all tools disabled, user settings (hooks,
plugins, memory) and MCP servers excluded. A probe on 2026-09-23 showed what
still reaches the model: a one-line Agent SDK prefix and generic environment,
date, model-name and account-email reminders; nothing CAD- or project-related.
It is still a different harness from a bare API call, so results carry the
`claude-cli` harness label and are only merged with API columns after the
opus-5 calibration bridge agrees (see scripts/leaderboard.py).
"""

from __future__ import annotations

import asyncio
import json
import tempfile

from inspect_ai.model import (
    GenerateConfig,
    ModelAPI,
    ModelOutput,
    ModelUsage,
    modelapi,
)


class ClaudeCLI(ModelAPI):
    def __init__(
        self,
        model_name: str,
        base_url: str | None = None,
        api_key: str | None = None,
        config: GenerateConfig = GenerateConfig(),
        **model_args,
    ) -> None:
        super().__init__(model_name, base_url, api_key, [], config)
        self.effort = model_args.get("effort")

    def max_connections(self) -> int:
        # subscription rate limits, not API quotas
        return 2

    def should_retry(self, ex: Exception) -> bool:
        # Concurrent CLI processes occasionally race the OAuth token refresh
        # and one reports "Not logged in" (seen 2026-09-23); it clears on retry.
        return isinstance(ex, RuntimeError) and "Not logged in" in str(ex)

    async def generate(self, input, tools, tool_choice, config):
        system = "\n\n".join(m.text for m in input if m.role == "system")
        turns = [m for m in input if m.role != "system"]
        if len(turns) != 1 or turns[0].role != "user":
            # claude -p takes one prompt; the repair solver's multi-turn
            # transcript would need re-rendering, which changes the harness.
            raise NotImplementedError("claudecli supports single-shot runs only (attempts=1)")

        # images go in as a stream-json user message (tested 2026-09-25);
        # text-only prompts keep the plain -p path the bridge validated
        images = [c for c in turns[0].content if getattr(c, "type", None) == "image"] if isinstance(turns[0].content, list) else []
        stdin = None
        if images:
            blocks = []
            for c in images:
                media, data = c.image.split(";base64,", 1)
                blocks.append({"type": "image", "source": {"type": "base64", "media_type": media.removeprefix("data:"), "data": data}})
            blocks.append({"type": "text", "text": turns[0].text})
            stdin = (json.dumps({"type": "user", "message": {"role": "user", "content": blocks}}) + "\n").encode()
        prompt_args = ["--input-format", "stream-json", "--output-format", "stream-json", "--verbose"] if images else [turns[0].text, "--output-format", "json"]
        cmd = [
            "claude", "-p", *prompt_args,
            "--model", self.model_name,
            "--system-prompt", system,
            "--tools", "",
            "--setting-sources", "project",
            "--strict-mcp-config",
            "--no-session-persistence",
        ]
        if self.effort:
            cmd += ["--effort", self.effort]

        with tempfile.TemporaryDirectory() as cwd:
            proc = await asyncio.create_subprocess_exec(
                *cmd, cwd=cwd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if stdin else None,
            )
            out, err = await proc.communicate(stdin)
        if images:  # stream-json: the last line of type "result" carries the answer
            lines = [ln for ln in out.decode().splitlines() if '"type":"result"' in ln.replace(" ", "")]
            out = lines[-1].encode() if lines else out
        try:
            result = json.loads(out)
        except json.JSONDecodeError:
            raise RuntimeError(f"claude CLI returned no JSON: {(out + err).decode()[-800:]}")
        if result.get("is_error"):
            # usage-limit and auth errors land here; raising lets
            # `inspect eval-retry` pick the sample up later
            raise RuntimeError(f"claude CLI error: {result.get('result')}")

        usage = result.get("usage", {})
        output = ModelOutput.from_content(model=self.model_name, content=result["result"])
        output.usage = ModelUsage(
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            reasoning_tokens=usage.get("output_tokens_details", {}).get("thinking_tokens"),
        )
        return output


@modelapi(name="claudecli")
def claudecli():
    return ClaudeCLI
