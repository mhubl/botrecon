Work in progress
# BotRecon
BotRecon is a simple command line tool that can help you secure your network from botnets. Just collect your network traffic (see [details](#details)), point BotRecon to the netflow capture file and wait for the results.

## Contents
1. [Description](#botrecon)
2. [Installation](#installation)
3. [Details](#details)
4. [Usage](#usage)

## Installation
Download the repository

    git clone https://github.com/mhubl/botrecon.git
    
Move into the directory

    cd botrecon
    
Install the dependencies

    pip install -r requirements.txt
    
Install the package

    pip install .
    
BotRecon should now be usable as `botrecon`. If it's not available make sure `~/.local/bin` is in your $PATH variable.

## Details

## Usage
    Usage: botrecon [OPTIONS] INPUT_FILE [OUTPUT_FILE]

      Get a list of infected hosts based on network traffic

      BotRecon takes data about the network traffic, uses machine learning to
      finds hosts infected with botnet malware. It can also be used as an
      interface to use with your own machine learning model if it supports the
      scikit-learn API.

      INPUT_FILE is a path to the file with captured NetFlow traffic. Data
      should be in a csv format unless a different --type is specified. BotRecon
      expects the following columns:

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

      -v, --verbose                   Increases the default verbosity of the
                                      application.

      -s, --silent                    Completely disables console output from the
                                      application.

      -d, --debug                     Enable debug mode.
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
                                      require additional python modeules to work.
                                      [default: csv]

      -V, --version                   Show the version and exit.
      -h, --help                      Show this message and exit.
