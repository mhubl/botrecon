# BotRecon
Botrecon is a simple command line tool that can help you secure your network from botnets. Just collect your network traffic (see [details](#data-requirements)), point botrecon to the netflow capture file and wait for the results.

## Contents
1. [Description](#botrecon)
2. [Installation](#installation)
3. [Details](#details)
    1. [Data requirements](#data-requirements)
    2. [Verbosity](#verbosity)
    3. [Models](#models)
4. [Examples](#examples)
5. [Usage](#usage)
6. [Liability notice](#liability-notice)

## Installation


### Python version

The newest version of python is generally recommended, but anything above python 3.6 is supported and should work both. Versions below 3.8 may not fully support all filetypes (e.g. pickle5), which might cause some tests to fail depending on your configuration.

### Installation steps
Download the repository

    git clone https://github.com/mhubl/botrecon.git

Move into the directory

    cd botrecon

Install the dependencies

    pip install -r requirements.txt

Install the package

    pip install .

BotRecon should now be usable as `botrecon`. If it isn't, make sure your appropriate `site-packages` directory or `~/.local/bin` is in your `$PATH`.

If you want to modify the code to fit your requirements, `requirements-dev.txt` contains dependencies for running tests and linting. It's also recommended to use the -e flag with pip for an editable install.

    pip install -r requirements-dev.txt
    pip install -e .
And afterwards, from the base directory:

Running tests

    pytest
Verifying style

    flake8

## Details
### Data requirements
The default models use netflow capture files and require the following columns:
* source address
* protocol
* destination port
* source port
* state
* duration
* total bytes
* source bytes

The names specified above are guaranteed to work, but if different ones are used botrecon will try to find the correct ones. In case a column cannot be located, an error message containing the missing name will be printed. If the file does not contain column names, it is expected that there are exactly 8 columns and botrecon assumes that the order is as listed above.
To read more about the netflow format see [the Wikipedia article on NetFlow](https://en.wikipedia.org/wiki/NetFlow) and [the OpenArgus website](https://openargus.org/).

### Verbosity
The verbose option enables some additional status/log messages during the execution, while debug disables additional error handling and should print full trace messages in most cases unrelated to parameter parsing and implicitly enables `--verbose` (unless `--silent` is enabled). Additionally, debug does not display the progress bar during predictions if data is batchified, but it prints a line each iteration.

### Models
Botrecon supports custom models, but also provides three default ones.

#### rforest
A Random Forest Classifier, it's the default option. This is potentially the best performing classifier out of the three attached by default. The returned scores are probabilities, ranging between 0 and 1.

#### svm
A Support Vector Machine classifier using the RBF kernel. Potentially a bit worse than the default. This uses the Nystrom method to approximate the kernel matrix, and will cause high memory usage. If you need to use it consider using `--batchify` if you encounter memory issues. This classifier does not support multiprocessing out of the box. Scores returned are **not** probabilities, any score above 0 is a positive classification and higher values mean higher confidence.

#### rforest-experimental
This is also a Random Forest Classifier, but trained on different training dataset in order to generalize better. This *might* actually perform better than the default, but it also might not, so use at your discretion. As in the default rforest, scores are probabilities in range between 0 and 1.

#### Custom model
To improve accuracy or adapt botrecon to your data you may want to use your own custom machine learning model. This is supported using the `-M/--custom-model` option. If a custom model is specified the data is passed to it without any transformations being applied, with the following exceptions:
* column containing source addresses is dropped
* column names are transformed to lowercase and all spaces are stripped

The model is expected to implement a `predict_proba`, `decision_function` or `predict` method. The score is then calculated as a mean of the classification scores for each host. The model is also loaded using pickle, so it needs to be picklable. If you're using a model that does not support that (e.g. a keras hdf5 model) you can [create a custom sklearn estimator](https://scikit-learn.org/stable/developers/develop.html) using a [BaseEstimator](https://scikit-learn.org/stable/modules/generated/sklearn.base.BaseEstimator.html) object and load it there. You can also use a similar subclassing approach with transformers if you need to import more packages than are made available by default ([sklearn](https://scikit-learn.org/stable/index.html) and [category_encoders](https://contrib.scikit-learn.org/category_encoders/)).

## Examples
Basic usage

    botrecon path/to/netflow/capture/file.csv

Using different filetypes

    botrecon -t feather path/to/netflow/capture/file.feather

Saving output to a file

    botrecon path/to/netflow/capture/file.csv path/to/desired/output.csv

Using a custom model

    botrecon -M /path/to/custom/model.pkl path/to/netflow/capture/file.csv

Displaying prediction progress using a progress bar, and

Splitting the data into 100 even batches to save memory using certain classifiers

    botrecon --batchify 1 % path/to/netflow/capture/file.csv

## Usage
    Usage: botrecon [OPTIONS] INPUT_FILE [OUTPUT_FILE]

      Get a list of infected hosts based on network traffic

      BotRecon takes data about the network traffic, uses machine learning to
      finds hosts infected with botnet malware. It can also be used as an
      interface to use with your own machine learning model if it supports the
      scikit-learn API.

      INPUT_FILE is a path to the file with captured NetFlow traffic. Data
      should be in a csv format unless a different --type is specified. BotRecon
      expects the following data:

        source address

        protocol

        destination port

        source port

        state

        duration

        totalbytes

        sourcebytes

      OUTPUT_FILE is a path to the desired output file location. It will be
      saved as a .csv

    Options:
      -M, --custom-model PATH         Path to your own custom model, has to
                                      conform with scikit-learn specifications -
                                      one of predict, predict_proba, or
                                      decision_function must be implemented. The
                                      model will receive the raw data from
                                      INPUT_FILE. It is recommendedto use an
                                      sklearn pipeline ending with a classifier.

      -m, --model [rforest|svm|rforest-experimental]
                                      One of the available, predefined models for
                                      classifying the traffic. This parameter is
                                      ignored if --custom-model/-M is passed. A
                                      description of all available models can be
                                      found in README.md  [default: rforest]

      -j, --jobs INTEGER              Number of parallel jobs to use for
                                      predicting. Negative values will match the
                                      cpu count. Only applies to classifiers that
                                      support multiprocessing (such as the default
                                      random forest).  [default: -1]

      -c, --min-count INTEGER         Minimum netflow count required for a host to
                                      be evaluated. If set to 0or lower no hosts
                                      are filtered.  [default: 0]

      -b, --batchify <FLOAT TEXT>...  Divide data into batches before predicting.
                                      Helpful for classifiers that have high
                                      memory usage or for large amounts of data.
                                      To use specify a value and then type. Type
                                      can be either "%" or "batches". If "%" the
                                      value has to be a float between 0 and 100.
                                      If "batches" it has to be a positive integer
                                      lower than the number of rows in data (after
                                      filtering). If no verbosity options are
                                      passed, this enables a progress bar for
                                      predicting. Example: `--batchify 5 %`

      -v, --verbose                   Increases the default verbosity of the
                                      application.

      -s, --silent                    Completely disables console output from the
                                      application.

      -d, --debug                     Enable debug mode.
      -i, --ignore-invalid, --ignore-invalid-addresses
                                      Controls the behavior in regards to invalid
                                      host addresses in the data.Setting this flag
                                      will make invalid addresses be silently
                                      ignored instead of raising an error. Ignored
                                      addresses will not be considered during
                                      classification. Only applies if filtering by
                                      IPs/ranges, no validity requirements are
                                      enforced otherwise.

      -r, --range, --ip TEXT          An IP address, network, or a path to a file
                                      containing a list with one of either per
                                      line. If specified, hosts not on the list
                                      will be ignored. Can be passed multiple
                                      times.

      -y, --yes, --confirm            Automatically accepts any prompts shown by
                                      the application. Currently the only prompt
                                      appears when more than 50 infected hosts
                                      were identified and no output file was
                                      specified.

      -t, --type [csv|feather|fwf|stata|json|pickle|parquet|excel]
                                      Type of the input file. Some types may
                                      require additional python modules to work.
                                      [default: csv]

      -V, --version                   Show the version and exit.
      -h, --help                      Show this message and exit.

      For a more detailed documentation see README.md
      https://github.com/mhubl/botrecon

## Liability notice

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

PLEASE NOTE THAT THE ABOVE NOTICE ALSO APPLIES TO THE ATTACHED MACHINE LEARNING MODELS. NO GUARANTEES ARE MADE IN REGARDS TO THEIR ACCURACY AND ABILITY TO PROPERLY DETECT ANY THREATS, THEY ARE NOT A REPLACEMENT FOR ANY OTHER SOLUTIONS OR SECURITY POLICIES.
