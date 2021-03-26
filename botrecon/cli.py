import click
from botrecon import get_data, Data
from botrecon import get_predictions
from botrecon import handle_output
from botrecon import IPEntity
from datetime import datetime
from pathlib import Path


def get_ips_from_file(path):
    ips = path.read_text()
    ips = ips.split('\n')
    return [IPEntity(ip) for ip in ips]


def parse_ip(ctx, param, value):
    import os
    if value:
        res = []
        for item in value:
            try:
                res.append(IPEntity(item))
            except ValueError as err:
                # Check for read access
                p = Path(item)
                if os.access(p, os.R_OK):
                    try:
                        res += get_ips_from_file(p)
                    except ValueError as err:
                        ctx.fail(err)
                else:
                    ctx.fail(err + ' or file not readable.')
        return res
    else:
        return value


def parse_model(ctx, param, value):
    params = ctx.params
    if "custom_model" in params and params["custom_model"] is not None:
        return Path(params["custom_model"])
    elif value is None:
        return ctx.default_map['model']
    else:
        return value


@click.command()
@click.option(  # TODO
    "-M",
    "--custom-model",
    default=None,
    type=click.Path(exists=True, readable=True),
    help="Path to your own custom model, has to conform with scikit-"
         "learn specifications - one of predict, predict_proba, or "
         "decision_function must be implemented. The model will "
         "receive the raw data from INPUT_FILE. It is recommended"
         "to use an sklearn pipeline ending with a classifier."
)
@click.option(
    "-m",
    "--model",
    default="rforest",
    show_default=True,
    callback=parse_model,
    type=click.Choice(["rforest", "svm", "rforest-experimental"], case_sensitive=False),
    help="One of the available, predefined models for classifying the "
         "traffic. This parameter is ignored if --custom-model/-M is "
         "passed. A description of all available models is available "
         "in the full documentation in README.md")
@click.option(  # TODO
    '-j',
    '--jobs',
    type=int,
    default=-1,
    show_default=True,
    help='Number of parallel jobs to use for predicting. Negative values will '
         'match the cpu count. Only applies to classifiers that support '
         'multiprocessing (such as the default random forest).'
)
@click.option(
    '-c',
    '--min-count',
    type=int,
    default=0,
    show_default=True,
    help='Minimum netflow count required for a host to be evaluated. If set to 0'
         'or lower no hosts are filtered.'
)
@click.option(
    "-v",
    "--verbose",
    "verbosity",
    flag_value=1,
    help="Increases the default verbosity of the application."
)
@click.option(
    "-s",
    "--silent",
    "verbosity",
    flag_value=-1,
    help="Completely disables console output from the application."
)
@click.option(
    "--normal-verbostity",
    "verbosity",
    flag_value=0,
    default=True,
    hidden=True
)
@click.option(
    "-r",
    "--range",
    "--ip",
    multiple=True,
    callback=parse_ip,
    default=None,
    help="An IP address, network, or a path to a file containing a "
         "list with one of either per line. If specified, hosts not "
         "on the list will be ignored. Can be passed multiple times."
)
@click.option(
    "-y",
    "--yes",
    "--confirm",
    is_flag=True,
    default=False,
    help="Automatically accepts any prompts shown by the application. "
         "Currently the only prompt appears when more than 50 infected "
         "hosts were identified and no output file was specified."
)
@click.option(
    "-t",
    "--type",
    "ftype",
    default="csv",
    show_default=True,
    type=click.Choice(list(Data.READERS.keys())),
    help='Type of the input file. Some types may require additional python '
         'modeules to work.'
)
@click.argument(
    "input_file",
    required=True,
    type=click.Path(readable=True, exists=True)
)
@click.argument(
    "output_file",
    required=False,
    type=click.Path(writable=True)
)
def botrecon(model, input_file, ftype, output_file, **kwargs):
    """Get a list of infected hosts based on network traffic"""
    ctx = click.get_current_context()

    if ctx.params['verbosity'] >= 0:
        click.echo(f'[{str(datetime.now())}] botrecon starting')

    try:
        predictions = get_predictions(get_data(input_file, ftype), model)
    except Exception as e:
        ctx.fail(e)

    handle_output(predictions, output_file)