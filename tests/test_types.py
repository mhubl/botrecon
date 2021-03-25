from click.testing import CliRunner
from pathlib import Path
from botrecon import botrecon


runner = CliRunner()
path = str(Path('tests', 'data', 'test'))


def test_csv(path=path, ext='.csv', ftype='csv'):
    result = runner.invoke(botrecon, ['-t', ftype, path + ext])
    assert result.exit_code == 0


def test_feather(path=path, ext='.feather', ftype='feather'):
    result = runner.invoke(botrecon, ['-t', ftype, path + ext])
    assert result.exit_code == 0


def test_excel(path=path, ext='.xlsx', ftype='excel'):
    result = runner.invoke(botrecon, ['-t', ftype, path + ext])
    assert result.exit_code == 0


def test_json(path=path, ext='.json', ftype='json'):
    result = runner.invoke(botrecon, ['-t', ftype, path + ext])
    assert result.exit_code == 0


def test_pickle(path=path, ext='.pkl', ftype='pickle'):
    result = runner.invoke(botrecon, ['-t', ftype, path + ext])
    assert result.exit_code == 0


def test_fwf(path=path, ext='.txt', ftype='fwf'):
    result = runner.invoke(botrecon, ['-t', ftype, path + ext])
    assert result.exit_code == 0


def test_parquet(path=path, ext='.parquet', ftype='parquet'):
    result = runner.invoke(botrecon, ['-t', ftype, path + ext])
    assert result.exit_code == 0


def test_stata(path=path, ext='.dta', ftype='stata'):
    result = runner.invoke(botrecon, ['-t', ftype, path + ext])
    assert result.exit_code == 0
