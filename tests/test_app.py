from dataclasses import dataclass
import queue
import pytest
from unittest.mock import MagicMock, patch
from SmartCubeGamingController.modes.binds.moves import MoveList, MoveType
from SmartCubeGamingController.app import App


@dataclass
class MockedDependencies:
    app: App
    server: MagicMock
    bindings_config: MagicMock
    move_history: MagicMock
    console: MagicMock


@pytest.fixture
def mock_dependencies():
    """Patch all external dependencies at construction time."""
    with patch("SmartCubeGamingController.app.Server") as MockServer, \
         patch("SmartCubeGamingController.app.Parser") as MockParser, \
         patch("SmartCubeGamingController.app.MoveHistory") as MockMoveHistory, \
         patch("SmartCubeGamingController.app.Console") as MockConsole:

        # Server setup
        mock_server = MagicMock()
        mock_server.mode_queue = queue.Queue()
        mock_server.move_queue = queue.Queue()
        mock_server.settings.binds_path = "/fake/path"
        MockServer.return_value = mock_server

        # Parser setup
        mock_bindings_config = MagicMock()
        MockParser.return_value.parse.return_value = mock_bindings_config

        # MoveHistory setup
        mock_move_history = MagicMock()
        MockMoveHistory.return_value = mock_move_history

        # Console setup
        mock_console = MagicMock()
        MockConsole.return_value = mock_console

        app = App()

        yield MockedDependencies(
            app=app,
            server=mock_server,
            bindings_config=mock_bindings_config,
            console=mock_console,
            move_history=mock_move_history,
        )


class TestRunOnce:
    def test_empty_queues_returns_early(self, mock_dependencies: MockedDependencies):
        """When both queues are empty, _run_once returns without doing anything."""
        app = mock_dependencies.app
        move_history = mock_dependencies.move_history

        app._run_once()

        move_history.append.assert_not_called()

    def test_mode_queue_updates_current_mode(self, mock_dependencies: MockedDependencies):
        """A mode message on the queue updates _current_mode."""
        app = mock_dependencies.app
        mock_dependencies.server.mode_queue.put("CONSOLE")

        app._run_once()  # consumes mode, but move_queue is empty -> returns early

        assert app._current_mode == "CONSOLE"

    def test_empty_mode_queue_preserves_current_mode(self, mock_dependencies: MockedDependencies):
        """If no mode message arrives, _current_mode stays unchanged."""
        app = mock_dependencies.app
        app._current_mode = "CONSOLE"

        app._run_once()

        assert app._current_mode == "CONSOLE"

    def test_bind_mode_appends_move_to_history(self, mock_dependencies: MockedDependencies):
        """In BIND mode, a move is appended to move history."""
        app = mock_dependencies.app
        move_history = mock_dependencies.move_history
        mock_dependencies.server.move_queue.put("U")
        move_history.find_match.return_value = None

        app._run_once()

        move_history.append.assert_called_once_with(MoveType.U)

    def test_bind_mode_updates_binds_buffer(self, mock_dependencies: MockedDependencies):
        """In BIND mode the server's binds_buffer is updated with the history string."""
        app = mock_dependencies.app
        server = mock_dependencies.server
        move_history = mock_dependencies.move_history
        move_history.to_str.return_value = "U R"
        move_history.find_match.return_value = None
        server.move_queue.put("U")

        app._run_once()

        assert server.binds_buffer == "U R"

    def test_bind_mode_executes_commands_on_match(self, mock_dependencies: MockedDependencies):
        """When a move sequence matches a binding, its commands are executed."""
        app = mock_dependencies.app
        move_history = mock_dependencies.move_history
        bindings_config = mock_dependencies.bindings_config

        mock_match = MagicMock()
        move_history.find_match.return_value = mock_match

        mock_commands = MagicMock()
        bindings_config.bindings.bindings.get.return_value = mock_commands

        mock_dependencies.server.move_queue.put("U")

        app._run_once()

        mock_commands.execute.assert_called_once()

    def test_bind_mode_clears_history_on_match(self, mock_dependencies: MockedDependencies):
        """After a successful match, move history is cleared."""
        app = mock_dependencies.app
        move_history = mock_dependencies.move_history
        bindings_config = mock_dependencies.bindings_config

        move_history.find_match.return_value = MagicMock()
        bindings_config.bindings.bindings.get.return_value = MagicMock()
        mock_dependencies.server.move_queue.put("R")

        app._run_once()

        move_history.clear.assert_called_once()

    def test_bind_mode_raises_on_missing_commands(self, mock_dependencies: MockedDependencies):
        """A match with no associated commands raises ValueError."""
        app = mock_dependencies.app
        move_history = mock_dependencies.move_history
        bindings_config = mock_dependencies.bindings_config

        move_history.find_match.return_value = MagicMock()
        bindings_config.bindings.bindings.get.return_value = None  # missing commands
        mock_dependencies.server.move_queue.put("F")

        with pytest.raises(ValueError, match="MoveList not found in bindings"):
            app._run_once()

    def test_bind_mode_no_match_does_not_clear_history(self, mock_dependencies: MockedDependencies):
        """Without a match, history is NOT cleared (partial sequence preserved)."""
        app = mock_dependencies.app
        move_history = mock_dependencies.move_history
        move_history.find_match.return_value = None
        mock_dependencies.server.move_queue.put("U")

        app._run_once()

        move_history.clear.assert_not_called()

    def test_console_mode_delegates_to_console(self, mock_dependencies: MockedDependencies):
        """In CONSOLE mode, moves are forwarded to the console handler."""
        app = mock_dependencies.app
        console = mock_dependencies.console
        server = mock_dependencies.server

        app._current_mode = "CONSOLE"
        server.move_queue.put("D")

        app._run_once()

        console.handle_move.assert_called_once_with(MoveType("D"))

    def test_console_mode_updates_cursor_state(self, mock_dependencies: MockedDependencies):
        """In CONSOLE mode, the server cursor state is synced from the console keyboard."""
        app = mock_dependencies.app
        server = mock_dependencies.server
        console = mock_dependencies.console

        app._current_mode = "CONSOLE"
        console.keyboard.cursor = "some_cursor_state"
        server.move_queue.put("D")

        app._run_once()

        assert server.cursor_state == "some_cursor_state"

    def test_console_mode_does_not_touch_move_history(self, mock_dependencies: MockedDependencies):
        """In CONSOLE mode, move history is never modified."""
        app = mock_dependencies.app
        move_history = mock_dependencies.move_history

        app._current_mode = "CONSOLE"
        mock_dependencies.server.move_queue.put("L")

        app._run_once()

        move_history.append.assert_not_called()
        move_history.clear.assert_not_called()


class TestRun:
    def test_run_starts_server_and_launches_chromium(self, mock_dependencies: MockedDependencies):
        """run() starts the server, launches chromium, then calls _run_once in a loop."""
        app = mock_dependencies.app
        server = mock_dependencies.server

        call_count = 0

        def fake_run_once():
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise StopIteration  # break the infinite loop after 2 iterations

        app._run_once = fake_run_once
        server.__enter__ = MagicMock(return_value=server)
        server.__exit__ = MagicMock(return_value=False)

        with pytest.raises(StopIteration):
            app.run()

        server.start.assert_called_once()
        server.launch_chromium.assert_called_once()
        assert call_count == 2
