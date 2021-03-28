from click.testing import CliRunner
from pathlib import Path
from botrecon import botrecon
import warnings
import re


runner = CliRunner()
path = str(Path('tests', 'data', 'test.csv'))
regex = r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}'


def test_batchify_percent():
    with warnings.catch_warnings():
        warnings.filterwarnings(
            action='ignore',
            category=DeprecationWarning,
            module=r'.*patsy'
        )
        # For some reason this line causes a warning,
        # but it doesn't happen in any of the other tests
        result_batchified = runner.invoke(botrecon, ['-b', 10, '%', path])
    assert result_batchified.exit_code == 0

    ips_batchified = re.findall(regex, str(result_batchified.stdout_bytes))

    result_normal = runner.invoke(botrecon, [path])
    ips_normal = re.findall(regex, str(result_normal.stdout_bytes))
    assert ips_normal == ips_batchified


def test_batchify_percent_uneven():
    result_batchified = runner.invoke(botrecon, ['-b', 6, '%', path])
    assert result_batchified.exit_code == 0

    ips_batchified = re.findall(regex, str(result_batchified.stdout_bytes))

    result_normal = runner.invoke(botrecon, [path])
    ips_normal = re.findall(regex, str(result_normal.stdout_bytes))
    assert ips_normal == ips_batchified


def test_batchify_percent_too_large():
    result_batchified = runner.invoke(botrecon, ['-b', 101, '%', path])
    assert result_batchified.exit_code == 2


def test_batchify_percent_negative():
    result_batchified = runner.invoke(botrecon, ['-b', -2, '%', path])
    assert result_batchified.exit_code == 2


def test_batchify_batches():
    result_batchified = runner.invoke(botrecon, ['-b', 10, 'batches', path])
    assert result_batchified.exit_code == 0

    ips_batchified = re.findall(regex, str(result_batchified.stdout_bytes))

    result_normal = runner.invoke(botrecon, [path])
    ips_normal = re.findall(regex, str(result_normal.stdout_bytes))
    assert ips_normal == ips_batchified


def test_batchify_batches_too_large():
    # test data has 5k rows
    result_batchified = runner.invoke(botrecon, ['-b', 10000, 'batches', path])
    assert result_batchified.exit_code == 2


def test_batchify_batches_negative():
    result_batchified = runner.invoke(botrecon, ['-b', -10, 'batches', path])
    assert result_batchified.exit_code == 2


def test_batchify_batches_float():
    result1 = runner.invoke(botrecon, ['-b', 10.5, 'batches', path])
    assert result1.exit_code == 0

    result2 = runner.invoke(botrecon, ['-b', 10, 'batches', path])
    assert result2.exit_code == 0

    ips1 = re.findall(regex, str(result1.stdout_bytes))
    ips2 = re.findall(regex, str(result2.stdout_bytes))

    assert ips1 == ips2
