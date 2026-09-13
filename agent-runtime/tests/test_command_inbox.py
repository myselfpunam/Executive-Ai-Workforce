from agent_runtime.command_inbox import CommandInbox, CommandResult
from agent_runtime.control_state import ControlState


def test_same_command_id_delivered_twice_only_takes_effect_once():
    control_state = ControlState()
    inbox = CommandInbox()
    apply_count = 0

    def apply_pause() -> CommandResult:
        nonlocal apply_count
        apply_count += 1
        control_state.request_pause()
        control_state.confirm_paused()
        return CommandResult(
            command_id="cmd_1",
            status="APPLIED",
            resulting_state=control_state.state.value,
            state_version=control_state.state_version,
        )

    first = inbox.handle("cmd_1", apply_pause)
    second = inbox.handle("cmd_1", apply_pause)  # simulated retry: same command_id

    assert apply_count == 1  # the real transition only happened once
    assert first == second  # the retry got back the identical prior result
    assert control_state.state_version == 2  # not 4 — no double transition


def test_different_command_ids_are_each_applied_once():
    control_state = ControlState()
    inbox = CommandInbox()

    def apply_pause() -> CommandResult:
        control_state.request_pause()
        control_state.confirm_paused()
        return CommandResult("cmd_a", "APPLIED", control_state.state.value, control_state.state_version)

    def apply_resume() -> CommandResult:
        control_state.request_resume()
        control_state.confirm_resumed()
        return CommandResult("cmd_b", "APPLIED", control_state.state.value, control_state.state_version)

    inbox.handle("cmd_a", apply_pause)
    inbox.handle("cmd_b", apply_resume)

    assert control_state.state.value == "ACTIVE"
    assert control_state.state_version == 4
