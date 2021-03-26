import click
import pandas as pd
import numpy as np


def get_predictions(data, model):
    ctx = click.get_current_context()

    model = load_model(model)
    model = adjust_njobs(model, ctx.params['jobs'])
    data = filter_hosts(data, ctx.params['min_count'])

    predictions = make_predictions(data.data, model)

    return evaluate_per_host(predictions, data.hosts)


def adjust_njobs(model, n_jobs):
    """Attempts to set the number of jobs for the classifier/pipeline"""
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
            ctx = click.get_current_context()
            if ctx.params['verbosity'] > 0:
                click.echo('Specified classifier does not support multiprocessing.')
            return model


def make_predictions(data, model):
    """Performs final checks and predicts using the appropriate method."""
    if hasattr(model, 'predict_proba'):
        return model.predict_proba(data)[:, 1]
    elif hasattr(model, 'decision_function'):
        return model.decision_function(data)[:, 1]
    else:
        return model.predict(data)


def filter_hosts(data, min_count=0):
    ctx = click.get_current_context()

    data.hosts['count'] = 0
    data.hosts['count'] = data.hosts.groupby(
        'srcaddr').transform('count')['count']

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
    if not ranges:
        return None

    def condition(addr):
        # Checks if the passed address matches any of the specified ranges
        return np.any([r.matches(addr) for r in ranges])
    # Map returns a boolean array with True where the condition was satisfied
    return hosts['srcaddr'].map(condition)


def evaluate_per_host(preds, hosts, threshold=.5):
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
