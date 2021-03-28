import click
import pandas as pd


def handle_output(preds, outfile):
    """Prints results to console or saves them in outfile"""
    ctx = click.get_current_context()
    # Change the column names to more presentable ones
    colnames = ["Host", "Mean Score", "Flow Count"]
    preds.columns = colnames

    if outfile is not None:
        preds.to_csv(outfile)
        return

    if ctx.params['verbosity'] >= 0:
        return output_to_console(ctx, preds)


def output_to_console(ctx, preds):
    """Prints results to console"""
    # Verify the user really wants to print if there's a lot
    if preds.shape[0] > 50 and not ctx.params['confirm']:
        prompt = ('More than 50 hosts have been identified as malicious. '
                  'Should they still be printed to the console? Choosing '
                  '"no" will let you choose an output file')
        if not click.confirm(prompt):
            f = click.prompt("Input a path to the desired output location",
                             type=click.Path(writable=True),
                             default=click.Path("output.csv"))
            preds.to_csv(f)
            return

    click.echo()
    if preds.shape[0] == 0:
        click.echo('No hosts were found to be infected.')
        return

    # Ensure the entire dataframe will be printed
    with pd.option_context("display.max_rows", len(preds)):
        click.echo(preds)
