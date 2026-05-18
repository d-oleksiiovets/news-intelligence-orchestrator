from typer.testing import CliRunner
from main import app
import main

runner = CliRunner()

def test_run_command_succes(mocker):
    mock_migration = mocker.patch("main._run_migration")
    mock_pipeline = mocker.patch("main.PipelineRunner")
    mocker.patch("main.load_config", return_value={"active_llm_settings": "test.yaml"})

    result = runner.invoke(app, ["run"])

    assert result.exit_code == 0
    mock_migration.assert_called_once()
    mock_pipeline.return_value.run.assert_called_once()
    assert "Pipeline failed" not in result.stdout

def test_scheduler_command(mocker):
    mock_migration = mocker.patch("main._run_migration")
    mock_pipeline = mocker.Mock()
    mock_pipeline.run = mocker.Mock()
    mocker.patch("main._build_pipeline", return_value=mock_pipeline)

    mock_start = mocker.patch("main.start_scheduler")

    result = runner.invoke(app, ["scheduler"])

    assert result.exit_code == 0
    mock_migration.assert_called_once()
    mock_pipeline.run.assert_not_called()
    mock_start.assert_called_once_with(mock_pipeline.run, main.CONFIG)

def test_run_command_error(mocker):
    mocker.patch("main._run_migration")
    mock_pipeline = mocker.patch("main.PipelineRunner")
    mock_pipeline.return_value.run.side_effect = RuntimeError("GPU Out of Memory")

    result = runner.invoke(app, ["run"])

    assert result.exit_code == 1
    assert "Pipeline failed: GPU Out of Memory" in result.stderr

def test_dashboard_params(mocker):
    mock_run_dash = mocker.patch("main.run_dashboard")
     
    result = runner.invoke(app, ["dashboard", "--port", "9000", "--no-browser"])
    
    assert result.exit_code == 0
    mock_run_dash.assert_called_once_with(port=9000, browser=False)
