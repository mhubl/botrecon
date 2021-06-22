import click
from botrecon import get_data, Data
from botrecon import get_predictions
from botrecon import handle_output
from botrecon import IPEntity
from datetime import datetime
from pathlib import Path


def get_ips_from_file(path):
    """Returns a list of IPEntities for each IP/range in the passed file"""
    ips = path.read_text()
    ips = ips.split('\n')
    return [IPEntity(ip) for ip in ips]


def parse_jobs(ctx, param, value):
    """Silently change all negative values to -1 for sklearn/joblib to handle"""
    if value == 0:
        raise click.BadParameter(value)
    elif value < 0:
        return -1
    else:
        return value


def parse_ip(ctx, param, value):
    """Converts IPs or files with IPs to a list of IPEntity objects"""
    from os import access, R_OK
    if value:
        res = []
        for item in value:
            try:
                res.append(IPEntity(item))
            except ValueError as err:
                # Check for read access
                p = Path(item)
                if access(p, R_OK):
                    try:
                        res += get_ips_from_file(p)
                    except ValueError as err:
                        raise click.BadParameter(str(err))
                else:
                    raise click.BadParameter(str(err) + ' (and is not a readable file)')
        return res
    else:
        return value


def parse_model(ctx, param, value):
    """Returns the path or model name depending on if a custom one was passed"""
    params = ctx.params
    if "custom_model" in params and params["custom_model"] is not None:
        return Path(params["custom_model"])
    elif value is None:
        return ctx.default_map['model']
    else:
        return value


def parse_batchify(ctx, param, value):
    """Validates the logic behind passed batchify option values"""
    if value == (0, ''):
        return value

    typ = value[1]
    val = value[0]

    if typ == 'percent':
        typ = "%"
        value = (val, typ)

    if typ == '%':
        if not (0 < val < 100):
            err = f'Invalid value for type "%". Must be between 0 and 100, got {val}'
        else:
            return value
    elif typ == 'batches':
        return (int(val), typ)
    else:
        err = f'Invalid type {typ}, must be either "%" or "batches"'

    raise click.BadParameter(err)


@click.command(
    epilog="For a more detailed documentation see README.md\n"
           "https://github.com/mhubl/botrecon"
)
@click.option(
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
         "passed. A description of all available models can be found "
         "in README.md")
@click.option(
    '-j',
    '--jobs',
    type=int,
    default=-1,
    show_default=True,
    callback=parse_jobs,
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
    '-b',
    '--batchify',
    type=(click.FLOAT, click.STRING),
    default=(0, ''),
    callback=parse_batchify,
    help='Divide data into batches before predicting. Helpful for classifiers '
         'that have high memory usage or for large amounts of data. To use specify '
         'a value and then type. Type can be either "%" or "batches". If "%" the '
         'value has to be a float between 0 and 100. If "batches" it has to be '
         'a positive integer lower than the number of rows in data (after filtering). '
         'If no verbosity options are passed, this enables a progress bar for '
         'predicting. Example: `--batchify 5 %`'
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
    "-d",
    "--debug",
    is_flag=True,
    default=False,
    help="Enable debug mode."
)
@click.option(
    "-i",
    "--ignore-invalid",
    "--ignore-invalid-addresses",
    "ignore_invalid",
    default=False,
    is_flag=True,
    help='Controls the behavior in regards to invalid host addresses in the data.'
         'Setting this flag will make invalid addresses be silently ignored '
         'instead of raising an error. Ignored addresses will not be considered '
         'during classification. Only applies if filtering by IPs/ranges, no '
         'validity requirements are enforced otherwise.'
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
    "--confirm",
    "--yes",
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
         'modules to work.'
)
@click.version_option(None, '-V', '--version')
@click.help_option('-h', '--help')
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
    """Get a list of infected hosts based on network traffic

    BotRecon takes data about the network traffic, uses machine learning to
    finds hosts infected with botnet malware.
    It can also be used as an interface to use with your own machine learning
    model if it supports the scikit-learn API.

    INPUT_FILE is a path to the file with captured NetFlow traffic. Data should
    be in a csv format unless a different --type is specified. BotRecon expects
    the following data:

      source address\n
      protocol\n
      destination port\n
      source port\n
      state\n
      duration\n
      totalbytes\n
      sourcebytes\n

    OUTPUT_FILE is a path to the desired output file location. It will be saved
    as a .csv
    """
    ctx = click.get_current_context()

    if ctx.params['verbosity'] >= 0:
        click.echo(f'[{str(datetime.now())}] BotRecon starting\n')

    if ctx.params['verbosity'] > 0 or ctx.params['debug']:
        click.echo('Loading data')
    try:
        predictions = get_predictions(
            get_data(input_file, ftype, isinstance(model, Path)),
            model
        )
    except Exception as e:
        if ctx.params['debug']:
            raise
        else:
            ctx.fail(e)

    handle_output(predictions, output_file)
