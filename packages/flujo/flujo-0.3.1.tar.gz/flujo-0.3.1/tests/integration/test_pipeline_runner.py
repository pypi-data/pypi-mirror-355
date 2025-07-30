import asyncio
from unittest.mock import Mock
import pytest

from flujo.domain import Step
from flujo.application.flujo_engine import Flujo
from flujo.domain.models import PipelineResult
from flujo.testing.utils import StubAgent, DummyPlugin
from flujo.domain.plugins import PluginOutcome


async def test_runner_respects_max_retries() -> None:
    agent = StubAgent(["a", "b", "c"])
    plugin = DummyPlugin(
        [
            PluginOutcome(success=False),
            PluginOutcome(success=False),
            PluginOutcome(success=True),
        ]
    )
    step = Step("test", agent, max_retries=3, plugins=[plugin])
    pipeline = step
    runner = Flujo(pipeline)
    result = await runner.run_async("in")
    assert agent.call_count == 3
    assert isinstance(result, PipelineResult)
    assert result.step_history[0].attempts == 3


async def test_feedback_enriches_prompt() -> None:
    sol_agent = StubAgent(["sol1", "sol2"])
    plugin = DummyPlugin(
        [
            PluginOutcome(success=False, feedback="SQL Error: XYZ"),
            PluginOutcome(success=True),
        ]
    )
    step = Step.solution(sol_agent, max_retries=2, plugins=[plugin])
    runner = Flujo(step)
    await runner.run_async("SELECT *")
    assert sol_agent.call_count == 2
    assert "SQL Error: XYZ" in sol_agent.inputs[1]


async def test_conditional_redirection() -> None:
    primary = StubAgent(["first"])
    fixit = StubAgent(["fixed"])
    plugin = DummyPlugin(
        [
            PluginOutcome(success=False, redirect_to=fixit),
            PluginOutcome(success=True),
        ]
    )
    step = Step("s", primary, max_retries=2, plugins=[plugin])
    pipeline = step
    runner = Flujo(pipeline)
    await runner.run_async("prompt")
    assert primary.call_count == 1
    assert fixit.call_count == 1


async def test_on_failure_called() -> None:
    agent = StubAgent(["out"])
    plugin = DummyPlugin([PluginOutcome(success=False)])
    handler = Mock()
    step = Step("s", agent, max_retries=1, plugins=[plugin])
    step.on_failure(handler)
    runner = Flujo(step)
    await runner.run_async("prompt")
    handler.assert_called_once()


async def test_timeout_and_redirect_loop_detection() -> None:
    async def slow_validate(data):
        await asyncio.sleep(0.05)
        return PluginOutcome(success=True)

    class SlowPlugin:
        async def validate(self, data):
            return await slow_validate(data)

    plugin = SlowPlugin()
    agent = StubAgent(["ok"])
    step = Step("s", agent, plugins=[plugin], max_retries=1, timeout_s=0.01)
    runner = Flujo(step)
    try:
        await runner.run_async("prompt")
    except TimeoutError:
        pass

    # Redirect loop
    a1 = StubAgent(["a1"])
    a2 = StubAgent(["a2"])
    plugin_loop = DummyPlugin(
        [
            PluginOutcome(success=False, redirect_to=a2),
            PluginOutcome(success=False, redirect_to=a1),
        ]
    )
    step2 = Step("loop", a1, max_retries=3, plugins=[plugin_loop])
    runner2 = Flujo(step2)
    with pytest.raises(Exception):
        await runner2.run_async("p")


async def test_pipeline_cancellation() -> None:
    agent = StubAgent(["out"])
    step = Step("s", agent)
    runner = Flujo(step)
    task = asyncio.create_task(runner.run_async("prompt"))
    await asyncio.sleep(0)
    task.cancel()
    result = await task
    assert isinstance(result, PipelineResult)
