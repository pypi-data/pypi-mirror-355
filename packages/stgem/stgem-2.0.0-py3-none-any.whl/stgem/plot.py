import pandas as pd
import plotly.graph_objs as go
import seaborn as sns
from matplotlib import pyplot as plt

from stgem import FeatureVector
from stgem.features import PiecewiseConstantSignal, Signal, Real


def plotting(data, sequence):
    """
    Implementation of plotly which require data to have specific format.

    Parameters:
        data (pd.Series): A pandas Series containing the signal data for multiple executions. 
            Each element should always be a nested list which is like [[timestamp 1, timestamp 2,...],[value1, value2, ...]]
        sequence (str): The name or identifier of the signal sequence being plotted based on the SUT input and outputs

    Returns:
        fig (go.Figure): A Plotly figure object containing the plot.
    """
    fig = go.Figure()

    time_stamp = pd.Series()
    values = pd.DataFrame()

    time_stamp = data.iloc[0][0]

    for index, value in data.items():
        new_row = pd.DataFrame([value[1]])
        fig.add_trace(go.Scatter(
            x=time_stamp,
            y=new_row.iloc[0],
            mode='lines',
            name=f'Values for Signal: {sequence}, Execution {index}',
            visible='legendonly'
        ))
        values = pd.concat([values, new_row], ignore_index=True)

    average_values = values.mean()
    min_values = values.min()
    max_values = values.max()

    # Plot the average values
    fig.add_trace(go.Scatter(
        x=time_stamp,
        y=average_values,
        mode='lines',
        name=f'Average Values for Signal: {sequence}'
    ))

    # Plot the min values
    fig.add_trace(go.Scatter(
        x=time_stamp,
        y=min_values,
        mode='lines',
        name=f'Min Values for Signal: {sequence}',
        line=dict(dash='dash'),
        visible='legendonly'
    ))

    # Plot the max values
    fig.add_trace(go.Scatter(
        x=time_stamp,
        y=max_values,
        mode='lines',
        name=f'Max Values for Signal: {sequence}',
        line=dict(dash='dot'),
        visible='legendonly'
    ))

    # Update layout for interactive features e.g. scaling
    fig.update_layout(
        title=f'SUT {sequence} signal Plotting among All Executions',
        xaxis_title='Time',
        yaxis_title='Values',
        template='plotly_white',
        xaxis=dict(
            rangeslider=dict(
                visible=True
            ),
            type="linear"
        ),
        yaxis=dict(
            fixedrange=False
        )
    )

    return fig


def plotting_feature(data, sequence, feature):
    """
    Plots single feature data based on feature type. Current, supporting PiecewiseConstantSignal and Signal

    Parameters:
        data (pd.Series): A pandas Series containing the feature data for multiple executions given by the test results.
        sequence (str): The name or identifier of the signal sequence being plotted based on the SUT input and outputs
        feature (object): The feature object.

    Returns:
        fig (go.Figure): A Plotly figure object containing the plot if the feature is PiecewiseConstantSignal or Signal.
        None: If the feature is of type Real.
    """
    ## convert the PiecewiseConstantSignal data format to synthesized signal with timestamps
    if isinstance(feature, PiecewiseConstantSignal):
        formated_data = pd.Series(dtype=object)
        for index, value in data.items():
            feature.set(value)
            synthesized_signal = feature.synthesize_signal()
            nested_list = [arr.tolist() for arr in synthesized_signal]
            formated_data.at[index] = nested_list  # Append nested list to the Series

        return plotting(formated_data, sequence)

    elif isinstance(feature, Signal):
        return plotting(data, sequence)

    elif isinstance(feature, Real):
        pass
    else:
        raise Exception("Unknown Feature object")


def get_robustness_cumavg(data):
    """
    Using the cumulative average robustness score as a surrogate for the Kaplan-Meier survival curve.
    
    We suppose the robustness scores will be positive during the initial running of several executions of the test generators due to the nature of the exploration.
    With time (execution) goes on, the robustness scores will decrease due to the fact that the generator will have a higher chance to generate test cases
    which can be treated as Critical task (robustness < Threshold) or even counterexamples (robustness <= 0) due to its exploitation nature.
    Thus, using cumulated average robustness score could be a choice to synthesize the Kaplan-Meier Survival Curve.

    Parameters:
        data (pd.Series): A pandas Series containing the robustness data for multiple executions given by the test results.

    Returns:
        robustness_cumavg (pd.Series): A pandas Series containing the result of the robustness_cumavg
    """
    # Calculate the cumulative sum
    cumsum = data.cumsum()
    # Calculate the cumulative count
    count = pd.Series(range(1, len(data) + 1), index=data.index)
    # Calculate the cumulative average
    robustness_cumavg = cumsum / count
    return robustness_cumavg


def plotting_survival_curve(data, name='Robustness Survival Curve'):
    """
    Plots Robustness Survival Curve.

    Parameters:
        data (pd.Series): A pandas Series containing the robustness data for multiple executions given by the test results.
        name (str): The name of the plot.

    Returns:
        fig (go.Figure): A Plotly figure object containing the plot.
    """

    # Calculate the cumulated average score in a way to substitute the concept of the survivial probabilities of Kaplan-Meier Survival Curve
    robustness_cumavg = get_robustness_cumavg(data)

    # Create a plotly figure
    fig = go.Figure()

    # Add a trace for the survival curve
    fig.add_trace(go.Scatter(
        x=robustness_cumavg.index,
        y=robustness_cumavg.values,
        mode='lines',
        name=name
    ))

    # Set the title of the plot
    fig.update_layout(
        title=name,
        xaxis_title='Number of Executions',
        yaxis_title='Cumulated Average Robustness Score'
    )

    return fig


def results_plotting(sut, results):
    """
    Plots the results of a system under test (SUT) based on the input and output feature.

    Parameters:
        sut (object): The system under test object containing the feature information.
        results (pd.DataFrame): A pandas DataFrame containing the results data for plotting.

    Returns:
        None: The function generates and shows the plots for the input and output features.
    """
    # Exit plotting if there is no data found
    if results.empty:
        return

        # Extract input and outputs features
    input_features = sut.new_ifv().flatten_to_list()
    output_features = sut.new_ofv().flatten_to_list()

    # Plotting each input feature's data based on the mapping between feature name and colomn name in dataframe
    for index, feature in enumerate(input_features):
        if feature.name not in results.columns:
            print(f"Input feature: {feature.name} does not exist in the results set!")
            continue
        else:
            fig = plotting_feature(data=results[feature.name], sequence=f'Input {index + 1}', feature=feature)
            if fig:
                fig.show()

    # Plotting each output feature's data based on the mapping between feature name and colomn name in dataframe
    for index, feature in enumerate(output_features):
        if feature.name not in results.columns:
            print(f"Output feature: {feature.name} does not exist in the results set!")
            continue
        else:
            fig = plotting_feature(data=results[feature.name], sequence=f'Output {index + 1}', feature=feature)
            if fig:
                fig.show()

    # Plotting robustness survival curve
    if list(results.index) == list(range(results.index[0], results.index[0] + len(results))):
        fig = plotting_survival_curve(data=results['robustness'], name='robustness Survival Curve')
        if fig:
            fig.show()
    else:
        print("It is better to draw the 'Robustness Survival Curve' based on the entire executions'")


def plot_multiple_tests_scatter(fv: FeatureVector, title, test_names, tests):
    """
    Plot multiple scatter plots of test results.

    Parameters:
    fv (FeatureVector): A feature vector containing the features to plot.
    title (str): The title of the overall figure.
    test_names (list of str): A list of names for each test.
    tests (list of dict): A list of dictionaries where each dictionary contains test results for features.

    The function creates scatter plots for each pair of features across multiple tests and displays them in a grid.
    """

    nv = len(fv._features) - 1
    nt = len(tests)

    sns.set_style("darkgrid")
    fig, ax = plt.subplots(nv, nt)
    fig.set_figheight(5 * nv)
    fig.set_figwidth(5 * nt)
    fig.suptitle(title)

    for r in range(1, len(fv._features)):
        description = fv._features[0].name + " - " + fv._features[r].name
        for i in range(len(tests)):
            ax[r - 1, i].set_title(test_names[i])
            ax[r - 1, i].scatter(tests[i][fv._features[0].name],
                                 tests[i][fv._features[r].name])
            ax[r - 1, i].set_xlabel(fv._features[0].name)
            ax[r - 1, i].set_ylabel(fv._features[r].name)
            ax[r - 1, i].set_xlim(fv._features[0].range[0], fv._features[0].range[1])
            ax[r - 1, i].set_ylim(fv._features[r].range[0], fv._features[r].range[1])

        r = r + 1
    plt.show()
