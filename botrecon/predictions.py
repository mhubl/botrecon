import click
import pandas as pd
import numpy as np


def get_predictions(data, model):
    """Makes predictions and returns a list of infected hosts"""
    ctx = click.get_current_context()
    verbose = ctx.params['verbosity'] > 0 or ctx.params['debug']

    if verbose:
        click.echo('Loading the model')

    model = load_model(model)
    model = adjust_njobs(model, ctx.params['jobs'])

    if verbose:
        click.echo('Filtering data')

    data = filter_hosts(data, ctx.params['min_count'])

    if verbose:
        click.echo('Predicting')

    batchify = ctx.params['batchify']
    if batchify[0]:
        predictions, threshold = make_predictions_batchified(data, model, batchify)
    else:
        predictions, threshold = make_predictions(data.data, model)

    if verbose:
        click.echo('Extracting infected hosts')

    return evaluate_per_host(predictions, data.hosts, threshold)


def make_predictions_batchified(data, model, batchify):
    """Splits data into batches, gets predictions for each and merges them back"""
    shape = data.data.shape[0]
    results = []

    ctx = click.get_current_context()
    if ctx.params['verbosity'] >= 0 and not ctx.params['debug']:
        with click.progressbar(label='Predicting', length=shape) as bar:
            for batch in data.batchify(*batchify):
                results.append(make_predictions(batch, model))
                bar.update(batch.shape[0])
    elif ctx.params['debug']:
        for batch in data.batchify(*batchify):
            if ctx.params['debug']:
                click.echo(f'batch shape: {batch.shape}, result length: {len(results)}')
            results.append(make_predictions(batch, model))
    else:
        for batch in data.batchify(*batchify):
            results.append(make_predictions(batch, model))

    threshold = results[0][1]
    preds = np.concatenate([result[0] for result in results])

    if preds.shape[0] != shape:
        raise ValueError('Unknown exception - batchifying failed.')

    return preds, threshold


def adjust_njobs(model, n_jobs):
    """Attempts to set the number of jobs for the classifier/pipeline"""
    ctx = click.get_current_context()
    try:
        # Attempt to set the param for each element of the pipeline
        for i in range(len(model)):
            if hasattr(model[i], 'n_jobs'):
                model[i].n_jobs = n_jobs
        return model
    except TypeError:
        # If it's not a pipeline, assume it's a standalone classifier
        if hasattr(model, 'n_jobs'):
            model.n_jobs = n_jobs
            return model
        else:
            # Otherwise it doesn't support multiprocessing
            if ctx.params['verbosity'] > 0 or ctx.params['debug']:
                click.echo('Specified classifier does not support multiprocessing.')
            return model


def make_predictions(data, model):
    """Performs final checks and predicts using the appropriate method."""
    if hasattr(model, 'predict_proba'):
        return model.predict_proba(data)[:, 1], .5
    elif hasattr(model, 'decision_function'):
        return model.decision_function(data), 0
    else:
        return model.predict(data), .5


def filter_hosts(data, min_count=0):
    """Removes hosts that do not satisfy filter conditions"""
    ctx = click.get_current_context()

    data.hosts['count'] = 0
    data.hosts['count'] = data.hosts.groupby('srcaddr').transform('count')['count']

    if min_count > 0:
        m = data.hosts['count'].map(lambda count: count > min_count)
        data.hosts = data.hosts[m]
        data.data = data.data[m]

    if ctx.params['range']:
        m = filter_ips(data.hosts, ctx.params["range"])
        if m is not None:
            data.hosts = data.hosts[m]
            data.data = data.data[m]

    return data


def filter_ips(hosts, ranges):
    """Removes hosts not in the specified ranges"""
    if not ranges:
        return None

    ignore_invalid = click.get_current_context().params['ignore_invalid']

    def condition(addr, ignore_invalid=ignore_invalid):
        # Checks if the passed address matches any of the specified ranges
        return np.any([r.matches(addr, ignore_invalid) for r in ranges])
    # Map returns a boolean array with True where the condition was satisfied
    return hosts['srcaddr'].map(condition)


def evaluate_per_host(preds, hosts, threshold=.5):
    """Returns a dataframe with infected hosts based on the passed predictions"""
    preds = pd.DataFrame({
        'host': hosts['srcaddr'],
        'count': hosts['count'],
        'pred': preds
    })

    preds.loc[:, 'count'] = preds.groupby('host').transform('count')['count']

    preds.loc[:, 'mean'] = preds.groupby('host')['pred'].transform('mean')
    preds.drop_duplicates('host', inplace=True)
    preds.loc[:, 'pred'] = np.int8(preds.loc[:, 'mean'] >= threshold)

    preds = preds.query('pred == 1')  # Only return infected hosts
    preds = preds.loc[:, ['host', 'mean', 'count']]
    preds = preds.sort_values('mean', ascending=False)
    return preds.reset_index(drop=True)


def load_model(model):
    """Loads the model from the passed path or name"""
    import sklearn
    import category_encoders
    import pickle
    import pkg_resources
    from pathlib import Path

    if isinstance(model, Path):
        return pickle.loads(model.read_bytes())

    model = 'models/' + model + '.pkl'
    model = pkg_resources.resource_string('botrecon', model)

    return pickle.loads(model)
