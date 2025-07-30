from .literal import METRIC_PROGRAM_COMMUNICATION, METRIC_ENTANGLEMENT_VARIANCE, METRIC_ENTANGLEMENT_RATIO, \
    METRIC_CRITICAL_DEPTH, METRIC_PARALLELISM
from .literal import PLOT_PARAM_INTERVAL, PLOT_PARAM_TITLE, PLOT_PARAM_xLABEL, PLOT_PARAM_yLABEL, PLOT_PARAM_FONTSIZE, \
    PLOT_PARAM_FIG_WIDTH, PLOT_PARAM_FIG_HEIGHT, PLOT_PARAM_LEGEND_LOC
from .metrics_generator import generate_metrics
import matplotlib.pyplot as plt

MARKERS = ['o', '^', 's', 'd', 'X']

DEFAULT_PLOT_PARAMS = {
    PLOT_PARAM_INTERVAL: None,
    PLOT_PARAM_TITLE: "",
    PLOT_PARAM_xLABEL: "",
    PLOT_PARAM_yLABEL: "",
    PLOT_PARAM_FONTSIZE: 14,
    PLOT_PARAM_FIG_WIDTH: 10,
    PLOT_PARAM_FIG_HEIGHT: 6,
    PLOT_PARAM_LEGEND_LOC: "upper right"
}


def _get_param(params, param_name):
    return params[param_name] if param_name in params else DEFAULT_PLOT_PARAMS[param_name]


def _plot_and_return(params, all_metrics, metrics_to_analyze):
    fig_size = (_get_param(params, PLOT_PARAM_FIG_WIDTH), _get_param(params, PLOT_PARAM_FIG_HEIGHT))
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=fig_size)
    interval = _get_param(params, PLOT_PARAM_INTERVAL)
    ax.set_xticks(interval)
    ax.set_xticklabels(map(str, interval))
    for i in range(len(metrics_to_analyze)):
        metric = metrics_to_analyze[i]
        marker = MARKERS[i]
        ax.plot(interval, [metrics[metric] for metrics in all_metrics], marker=marker, label=metric)
    ax.legend(loc=_get_param(params, PLOT_PARAM_LEGEND_LOC))
    ax.set_xlabel(_get_param(params, PLOT_PARAM_xLABEL))
    ax.set_ylabel(_get_param(params, PLOT_PARAM_yLABEL))
    fig.suptitle(_get_param(params, PLOT_PARAM_TITLE), fontsize=_get_param(params, PLOT_PARAM_FONTSIZE))
    return fig


def analyze_circuit_group_structural(circuit_generator, min_num_qubits, max_num_qubits, img_file_name="test.png",
                                     img_file_path="test/images/", plot_params=None):
    if plot_params is None:
        plot_params = DEFAULT_PLOT_PARAMS
    interval = range(min_num_qubits, max_num_qubits+1)
    plot_params[PLOT_PARAM_INTERVAL] = interval
    plot_params[PLOT_PARAM_TITLE] = circuit_generator.name
    all_metrics = [generate_metrics(circuit_generator.generate_qiskit_circuit(i)) for i in interval]
    metrics_to_analyze = [METRIC_PROGRAM_COMMUNICATION, METRIC_ENTANGLEMENT_VARIANCE, METRIC_ENTANGLEMENT_RATIO,
                          METRIC_CRITICAL_DEPTH, METRIC_PARALLELISM]
    fig = _plot_and_return(plot_params, all_metrics, metrics_to_analyze)
    fig.savefig(img_file_path + img_file_name)
