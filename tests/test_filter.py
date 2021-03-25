from click.testing import CliRunner
from pathlib import Path
import re
from botrecon import botrecon
import warnings


runner = CliRunner()
path = str(Path('tests', 'data', 'filter.csv'))
regex = r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}'


def make_args(ips, path):
    args = []
    for ip in ips:
        args += ['--ip', ip]
    args += [path]
    return args


def test_filter_ip(ip='147.32.84.208'):
    with warnings.catch_warnings():
        warnings.filterwarnings(
            action='ignore',
            category=DeprecationWarning,
            module=r'.*patsy'
        )
        # For some reason this line causes a warning,
        # but it doesn't happen in any of the other tests
        result = runner.invoke(botrecon, ['--ip', ip, path])
    out = str(result.stdout_bytes)

    matches = re.findall(regex, out)
    assert len(matches) == 1
    assert matches[0] == ip


def test_filter_ip_multiple():
    ips = ['147.32.84.208', '10.0.0.7', '142.16.17.30', '147.32.85.208']
    args = make_args(ips, path)
    result = runner.invoke(botrecon, args)
    out = str(result.stdout_bytes)

    matches = re.findall(regex, out)
    assert len(matches) == len(ips)


def test_filter_range(ip='147.32.84.0/24'):
    result = runner.invoke(botrecon, ['--ip', ip, path])
    out = str(result.stdout_bytes)

    matches = re.findall(regex, out)
    assert len(matches) == 4


def test_filter_range2(ip='147.32.84.0/255.255.255.0'):
    result = runner.invoke(botrecon, ['--ip', ip, path])
    out = str(result.stdout_bytes)

    matches = re.findall(regex, out)
    assert len(matches) == 4


def test_filter_range3(ip='142.0.0.0/8'):
    result = runner.invoke(botrecon, ['--ip', ip, path])
    out = str(result.stdout_bytes)

    matches = re.findall(regex, out)
    assert len(matches) == 8


def test_filter_range4(ip='147.32.84.0/255.255.255.0'):
    result = runner.invoke(botrecon, ['--ip', ip, path])
    out = str(result.stdout_bytes)

    matches = re.findall(regex, out)
    assert len(matches) == 4


def test_filter_range_multiple():
    ips = ['147.32.84.0/24', '10.0.0.0/16', '142.16.0.0/16']
    args = make_args(ips, path)

    result = runner.invoke(botrecon, args)
    out = str(result.stdout_bytes)

    matches = re.findall(regex, out)
    assert len(matches) == 4 + 2 + 4


def test_filter_mixed():
    ips = ['142.15.85.0/24', '10.1.0.0/16', '147.32.84.211', '142.16.17.20']
    args = make_args(ips, path)

    result = runner.invoke(botrecon, args)
    out = str(result.stdout_bytes)

    matches = re.findall(regex, out)
    assert len(matches) == 4 + 2 + 2


def test_filter_from_file(tmp_path):
    ips = ['142.15.85.0/24', '10.1.0.0/16', '147.32.84.211', '142.16.17.20']
    ips = "\n".join(ips)
    tmp_path = tmp_path / 'ip_test'
    tmp_path.write_text(ips)

    result = runner.invoke(botrecon, ['--ip', str(tmp_path), path])
    out = str(result.stdout_bytes)

    matches = re.findall(regex, out)
    assert len(matches) == 4 + 2 + 2


def test_filter_from_files(tmp_path):
    ips = ['142.15.85.0/24', '147.32.84.211', '10.1.0.0/16', '142.16.17.20']
    # Divide the list into two
    ips1 = "\n".join(ips[:2])
    ips2 = "\n".join(ips[2:])

    # Save it as two separate files
    tmp_path2 = tmp_path / 'ip_test2'
    tmp_path1 = tmp_path / 'ip_test1'

    tmp_path1.write_text(ips1)
    tmp_path2.write_text(ips2)

    args = make_args([str(tmp_path1), str(tmp_path2)], path)

    result = runner.invoke(botrecon, args)
    out = str(result.stdout_bytes)

    matches = re.findall(regex, out)
    assert len(matches) == 4 + 2 + 2
