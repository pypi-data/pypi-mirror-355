from .literal import *
import math


BAD_GATES = ["barrier"]


def generate_basic_metrics(qc, metrics=None):
    def add_edge(a, b):
        if a not in q_connections:
            q_connections[a] = set()
        if a not in n_2g_q:
            n_2g_q[a] = 0
        q_connections[a].add(b)
        n_2g_q[a] += 1
        if b not in q_connections:
            q_connections[b] = set()
        if b not in n_2g_q:
            n_2g_q[b] = 0
        q_connections[b].add(a)
        n_2g_q[b] += 1

    def update_depth(op):
        unique_operators_set.add(op.operation.name)
        n_operands[0] += op.operation.num_qubits + op.operation.num_clbits
        new_depth_params = max([critical_depth[q._index] for q in op.qubits])
        new_depth = new_depth_params[0] + 1
        new_count_2gates = new_depth_params[1]
        if len(op.qubits) > 1:
            new_count_2gates += 1
        for q in op.qubits:
            critical_depth[q._index] = [new_depth, new_count_2gates]

    unique_operators_set = set()
    consecutive_gates = 0
    n_operands = [0]
    n_unique_operands = len(qc.qubits) + len(qc.clbits)
    n = len(qc.data)
    n_2_gates = 0
    q_connections = {}
    n_2g_q = {}
    critical_depth = {}
    for i in range(qc.num_qubits):
        critical_depth[i] = [0, 0]
    i = 0
    while i < n:
        if qc.data[i].operation.num_qubits > 2:
            error_text = "Found a quantum gate which affect more than 2 qubits, which is currently not supported.\n" \
                         + "Please compile the circuit for using only gates with 1 or 2 qubits.\n" \
                         + f"Unsupported gate: {str(qc.data)}"
            raise ValueError(error_text)
        temp_consecutive_gates = 0
        op = qc.data[i]
        update_depth(op)
        while i < n and qc.data[i].operation.num_qubits == 2:
            add_edge(op.qubits[0]._index, op.qubits[1]._index)
            temp_consecutive_gates += 1
            n_2_gates += 1
            i += 1
            if i < n:
                op = qc.data[i]
                update_depth(op)
        i += 1
        consecutive_gates = max(consecutive_gates, temp_consecutive_gates)

    if metrics is None:
        metrics = {}
    metrics[METRIC_QUBIT_CONNECTIONS] = q_connections
    metrics[METRIC_NUMBER_QUBITS] = qc.num_qubits
    metrics[METRIC_N_2_GATES_X_QUBIT] = n_2g_q
    metrics[METRIC_NUMBER_GATES] = qc.size()
    metrics[METRIC_DEPTH] = qc.depth()
    ops = qc.count_ops()
    metrics[METRIC_AVG_2_GATES_X_QUBIT] = 2 * n_2_gates / qc.num_qubits
    metrics[METRIC_CONSECUTIVE_2_GATES] = consecutive_gates
    metrics[METRIC_NUMBER_2_GATES] = n_2_gates
    metrics[METRIC_N_2_GATES_CRITICAL_PATH] = max([critical_depth[i] for i in range(qc.num_qubits)])[1]
    metrics[METRIC_N_UNIQUE_GATES] = len(unique_operators_set)
    metrics[METRIC_N_UNIQUE_OPERANDS] = n_unique_operands
    metrics[METRIC_N_OPERANDS] = n_operands[0]
    return metrics


def generate_derived_metrics(metrics):
    def calculate_parallelism(number_of_qubits, number_of_gates, depth):
        return ((number_of_gates / depth) - 1) * (1 / (number_of_qubits - 1))

    def calculate_program_communication(ds, number_of_qubits):
        sum_d = sum([len(ds[key]) for key in ds])
        return sum_d / (number_of_qubits * (number_of_qubits - 1))

    def calc_entanglement_var(number_of_qubits, n_2gates_x_qubit, avg_2gates_x_qubit):
        sum_2gxq = sum([(n_2gates_x_qubit[key] - avg_2gates_x_qubit) ** 2 for key in n_2gates_x_qubit])
        return math.log(sum_2gxq + 1, 10) / number_of_qubits

    metrics[METRIC_ENTANGLEMENT_RATIO] = metrics[METRIC_NUMBER_2_GATES] / metrics[METRIC_NUMBER_GATES]
    metrics[METRIC_CRITICAL_DEPTH] = metrics[METRIC_N_2_GATES_CRITICAL_PATH] / metrics[METRIC_NUMBER_2_GATES] if metrics[METRIC_NUMBER_2_GATES] > 1 else 0
    metrics[METRIC_PARALLELISM] = calculate_parallelism(metrics[METRIC_NUMBER_QUBITS],
                                                        metrics[METRIC_NUMBER_GATES],
                                                        metrics[METRIC_DEPTH])
    metrics[METRIC_PROGRAM_COMMUNICATION] = calculate_program_communication(metrics[METRIC_QUBIT_CONNECTIONS],
                                                                            metrics[METRIC_NUMBER_QUBITS])
    metrics[METRIC_ENTANGLEMENT_VARIANCE] = calc_entanglement_var(metrics[METRIC_NUMBER_QUBITS],
                                                                  metrics[METRIC_N_2_GATES_X_QUBIT],
                                                                  metrics[METRIC_AVG_2_GATES_X_QUBIT])
    metrics[METRIC_DIFFICULTY] = (metrics[METRIC_N_UNIQUE_GATES] / 2) * \
                                 (metrics[METRIC_N_OPERANDS] / metrics[METRIC_N_UNIQUE_OPERANDS])
    metrics[METRIC_VOCABULARY] = metrics[METRIC_N_UNIQUE_OPERANDS] + metrics[METRIC_N_UNIQUE_GATES]
    metrics[METRIC_LENGTH] = metrics[METRIC_NUMBER_GATES] + metrics[METRIC_N_OPERANDS]
    metrics[METRIC_VOLUME] = metrics[METRIC_LENGTH] * math.log(metrics[METRIC_VOCABULARY], 2)
    metrics[METRIC_EFFORT] = metrics[METRIC_DIFFICULTY] * metrics[METRIC_VOLUME]
    

def eliminate_bad_gates(qc):
    index_to_delete = []
    for index, instruction in enumerate(qc.data):
        if instruction.operation.name in BAD_GATES:
            index_to_delete.append(index)
    for i in range(len(index_to_delete)):
        del qc.data[index_to_delete[len(index_to_delete) - 1 - i]]


def generate_metrics(qc):
    eliminate_bad_gates(qc)
    metrics = {}
    generate_basic_metrics(qc, metrics)
    generate_derived_metrics(metrics)
    return metrics
