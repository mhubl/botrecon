from click.testing import CliRunner
from pathlib import Path
from botrecon import botrecon
import re


runner = CliRunner()
path = str(Path('tests', 'data', 'test.csv'))
regex = r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}'


def test_silent():
    result = runner.invoke(botrecon, ['-s', path])
    assert len(result.stdout_bytes) == 0


def test_min_count():
    # Test without arg first to see if file is okay
    result = runner.invoke(botrecon, [path])
    ips = re.findall(regex, str(result.stdout_bytes))
    assert len(ips) == 12, 'test file is broken if this failed'

    result = runner.invoke(botrecon, ['-c', 2, path])
    ips = re.findall(regex, str(result.stdout_bytes))
    assert len(ips) == 9

    result = runner.invoke(botrecon, ['-c', 40, path])
    ips = re.findall(regex, str(result.stdout_bytes))
    assert len(ips) == 1


def test_jobs_negative():
    result = runner.invoke(botrecon, ['-j', -20, path])
    assert result.exit_code == 0


def test_jobs_normal():
    result = runner.invoke(botrecon, ['-j', 1, path])
    assert result.exit_code == 0


def test_jobs_normal2():
    result = runner.invoke(botrecon, ['-j', 8, path])
    assert result.exit_code == 0


def test_jobs_zero():
    result = runner.invoke(botrecon, ['-j', 0, path])
    assert result.exit_code == 2

# def test_custom_model():
#     model_path = Path('botrecon', 'models', 'rforest.pkl')
#     print(model_path)
#     assert model_path.exists(), 'if failed the model is not available'
#     result_custom = runner.invoke(botrecon, ['-M', str(model_path), path])
#     assert result.exit_code == 0
