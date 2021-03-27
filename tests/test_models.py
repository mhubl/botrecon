from click.testing import CliRunner
from pathlib import Path
from botrecon import botrecon


runner = CliRunner()
path = str(Path('tests', 'data', 'test.csv'))


def test_jobs_svm():
    result = runner.invoke(botrecon, ['-m', 'svm', path])
    assert result.exit_code == 0


def test_jobs_rforest():
    result = runner.invoke(botrecon, ['-m', 'rforest', path])
    assert result.exit_code == 0


def test_jobs_rfexperimental():
    result = runner.invoke(botrecon, ['-m', 'rforest-experimental', path])
    assert result.exit_code == 0
