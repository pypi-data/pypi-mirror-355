from QBenchAnalyzer.literal import METRIC_NUMBER_QUBITS, METRIC_NUMBER_GATES, METRIC_NUMBER_2_GATES, METRIC_DEPTH, \
    METRIC_CONSECUTIVE_2_GATES, METRIC_AVG_2_GATES_X_QUBIT, METRIC_PARALLELISM, METRIC_CRITICAL_DEPTH, \
    METRIC_ENTANGLEMENT_RATIO, METRIC_PROGRAM_COMMUNICATION, METRIC_ENTANGLEMENT_VARIANCE, METRIC_N_UNIQUE_OPERANDS, \
    METRIC_N_UNIQUE_GATES, METRIC_N_OPERANDS, METRIC_DIFFICULTY, METRIC_VOCABULARY, METRIC_VOLUME, METRIC_EFFORT, \
    METRIC_LENGTH
from QBenchAnalyzer.metrics_generator import generate_metrics
from qiskit import QuantumCircuit
import pytest
import math

pytestmark = pytest.mark.parametrize("circuit,expected_metrics",
                                     [
                                         ("qaoa_vanilla_03", {
                                             METRIC_NUMBER_QUBITS: 3,
                                             METRIC_NUMBER_GATES: 15,
                                             METRIC_NUMBER_2_GATES: 6,
                                             METRIC_DEPTH: 11,
                                             METRIC_CONSECUTIVE_2_GATES: 2,
                                             METRIC_AVG_2_GATES_X_QUBIT: 4.0,
                                             METRIC_PARALLELISM: 2/11,
                                             METRIC_CRITICAL_DEPTH: 1,
                                             METRIC_ENTANGLEMENT_RATIO: 6/15,
                                             METRIC_PROGRAM_COMMUNICATION: 1,
                                             METRIC_ENTANGLEMENT_VARIANCE: 0,
                                             METRIC_N_UNIQUE_OPERANDS: 3,
                                             METRIC_N_UNIQUE_GATES: 4,
                                             METRIC_N_OPERANDS: 21,
                                             METRIC_DIFFICULTY: (4 / 2) * (21 / 3),
                                             METRIC_VOCABULARY: 3 + 4,
                                             METRIC_VOLUME: (21 + 15) * math.log(3 + 4, 2),
                                             METRIC_EFFORT: ((4 / 2) * (21 / 3)) * ((21 + 15) * math.log(3 + 4, 2)),
                                             METRIC_LENGTH: 21 + 15,
                                         }),
                                         ("qaoa_vanilla_04", {
                                             METRIC_NUMBER_QUBITS: 4,
                                             METRIC_NUMBER_GATES: 26,
                                             METRIC_NUMBER_2_GATES: 12,
                                             METRIC_DEPTH: 17,
                                             METRIC_CONSECUTIVE_2_GATES: 3,
                                             METRIC_AVG_2_GATES_X_QUBIT: 6.0,
                                             METRIC_PARALLELISM: 3/17,
                                             METRIC_CRITICAL_DEPTH: 5/6,
                                             METRIC_ENTANGLEMENT_RATIO: 12/26,
                                             METRIC_PROGRAM_COMMUNICATION: 1,
                                             METRIC_ENTANGLEMENT_VARIANCE: 0,
                                             METRIC_N_UNIQUE_OPERANDS: 8,
                                             METRIC_N_UNIQUE_GATES: 4,
                                             METRIC_N_OPERANDS: 38,
                                             METRIC_DIFFICULTY: (4 / 2) * (38 / 8),
                                             METRIC_VOCABULARY: 8 + 4,
                                             METRIC_VOLUME: (26 + 38) * math.log(8 + 4, 2),
                                             METRIC_EFFORT: ((4 / 2) * (38 / 8)) * ((26 + 38) * math.log(8 + 4, 2)),
                                             METRIC_LENGTH: 26 + 38,
                                         }),
                                         ("hamiltonian_04", {
                                             METRIC_NUMBER_QUBITS: 4,
                                             METRIC_NUMBER_GATES: 25,
                                             METRIC_NUMBER_2_GATES: 6,
                                             METRIC_DEPTH: 13,
                                             METRIC_CONSECUTIVE_2_GATES: 2,
                                             METRIC_AVG_2_GATES_X_QUBIT: 3.0,
                                             METRIC_PARALLELISM: 4/13,
                                             METRIC_CRITICAL_DEPTH: 1,
                                             METRIC_ENTANGLEMENT_RATIO: 6/25,
                                             METRIC_PROGRAM_COMMUNICATION: 0.5,
                                             METRIC_ENTANGLEMENT_VARIANCE: math.log(5, 10) / 4,
                                             METRIC_N_UNIQUE_OPERANDS: 8,
                                             METRIC_N_UNIQUE_GATES: 4,
                                             METRIC_N_OPERANDS: 35,
                                             METRIC_DIFFICULTY: (4 / 2) * (35 / 8),
                                             METRIC_VOCABULARY: 8 + 4,
                                             METRIC_VOLUME: (25 + 35) * math.log(8 + 4, 2),
                                             METRIC_EFFORT: ((4 / 2) * (35 / 8)) * ((25 + 35) * math.log(8 + 4, 2)),
                                             METRIC_LENGTH: 25 + 35,
                                         }),
                                         ("hamiltonian_05", {
                                             METRIC_NUMBER_QUBITS: 5,
                                             METRIC_NUMBER_GATES: 32,
                                             METRIC_NUMBER_2_GATES: 8,
                                             METRIC_DEPTH: 16,
                                             METRIC_CONSECUTIVE_2_GATES: 2,
                                             METRIC_AVG_2_GATES_X_QUBIT: 3.2,
                                             METRIC_PARALLELISM: 1/4,
                                             METRIC_CRITICAL_DEPTH: 1,
                                             METRIC_ENTANGLEMENT_RATIO: 8/32,
                                             METRIC_PROGRAM_COMMUNICATION: 0.4,
                                             METRIC_ENTANGLEMENT_VARIANCE: math.log(5.8, 10) / 5,
                                             METRIC_N_UNIQUE_OPERANDS: 10,
                                             METRIC_N_UNIQUE_GATES: 4,
                                             METRIC_N_OPERANDS: 45,
                                             METRIC_DIFFICULTY: (4 / 2) * (45 / 10),
                                             METRIC_VOCABULARY: 10 + 4,
                                             METRIC_VOLUME: (32 + 45) * math.log(10 + 4, 2),
                                             METRIC_EFFORT: ((4 / 2) * (45 / 10)) * ((32 + 45) * math.log(10 + 4, 2)),
                                             METRIC_LENGTH: 32 + 45,
                                         }),
                                         ("grover_noancilla_1reg_2", {
                                             METRIC_NUMBER_QUBITS: 2,
                                             METRIC_NUMBER_GATES: 6,
                                             METRIC_NUMBER_2_GATES: 0,
                                             METRIC_DEPTH: 4,
                                             METRIC_CONSECUTIVE_2_GATES: 0,
                                             METRIC_AVG_2_GATES_X_QUBIT: 0,
                                             METRIC_PARALLELISM: 0.5,
                                             METRIC_CRITICAL_DEPTH: 0,
                                             METRIC_ENTANGLEMENT_RATIO: 0,
                                             METRIC_PROGRAM_COMMUNICATION: 0,
                                             METRIC_ENTANGLEMENT_VARIANCE: 0,
                                             METRIC_N_UNIQUE_OPERANDS: 4,
                                             METRIC_N_UNIQUE_GATES: 4,
                                             METRIC_N_OPERANDS: 8,
                                             METRIC_DIFFICULTY: (4 / 2) * (8 / 4),
                                             METRIC_VOCABULARY: 4 + 4,
                                             METRIC_VOLUME: (6 + 8) * math.log(4 + 4, 2),
                                             METRIC_EFFORT: ((4 / 2) * (8 / 4)) * ((6 + 8) * math.log(4 + 4, 2)),
                                             METRIC_LENGTH: 6 + 8,
                                         }),
                                         ("grover_noancilla_1reg_4", {
                                             METRIC_NUMBER_QUBITS: 4,
                                             METRIC_NUMBER_GATES: 142,
                                             METRIC_NUMBER_2_GATES: 52,
                                             METRIC_DEPTH: 93,
                                             METRIC_CONSECUTIVE_2_GATES: 2,
                                             METRIC_AVG_2_GATES_X_QUBIT: 26,
                                             METRIC_PARALLELISM: 49/279,
                                             METRIC_CRITICAL_DEPTH: 48/52,
                                             METRIC_ENTANGLEMENT_RATIO: 52/142,
                                             METRIC_PROGRAM_COMMUNICATION: 1,
                                             METRIC_ENTANGLEMENT_VARIANCE: math.log(81, 10) / 4,
                                             METRIC_N_UNIQUE_OPERANDS: 8,
                                             METRIC_N_UNIQUE_GATES: 5,
                                             METRIC_N_OPERANDS: 198,
                                             METRIC_DIFFICULTY: (5 / 2) * (198 / 8),
                                             METRIC_VOCABULARY: 8 + 5,
                                             METRIC_VOLUME: (142 + 198) * math.log(8 + 5, 2),
                                             METRIC_EFFORT: ((5 / 2) * (198 / 8)) * ((142 + 198) * math.log(8 + 5, 2)),
                                             METRIC_LENGTH: 142 + 198,
                                         }),
                                         ("ghz_10", {
                                             METRIC_NUMBER_QUBITS: 10,
                                             METRIC_NUMBER_GATES: 10,
                                             METRIC_NUMBER_2_GATES: 9,
                                             METRIC_DEPTH: 10,
                                             METRIC_CONSECUTIVE_2_GATES: 9,
                                             METRIC_AVG_2_GATES_X_QUBIT: 1.8,
                                             METRIC_PARALLELISM: 0,
                                             METRIC_CRITICAL_DEPTH: 1.0,
                                             METRIC_ENTANGLEMENT_RATIO: 0.9,
                                             METRIC_PROGRAM_COMMUNICATION: 0.2,
                                             METRIC_ENTANGLEMENT_VARIANCE: 0.041497335,
                                             METRIC_N_UNIQUE_OPERANDS: 10,
                                             METRIC_N_UNIQUE_GATES: 2,
                                             METRIC_N_OPERANDS: 19,
                                             METRIC_DIFFICULTY: (2 / 2) * (19 / 10),
                                             METRIC_VOCABULARY: 10 + 2,
                                             METRIC_VOLUME: (19 + 10) * math.log(10 + 2, 2),
                                             METRIC_EFFORT: ((2 / 2) * (19 / 10)) * ((19 + 10) * math.log(10 + 2, 2)),
                                             METRIC_LENGTH: 19 + 10,
                                         })
                                     ])


class ITest:
    def generate_path_file(self, file_name):
        return f"./test/circuits/{file_name}.qasm"

    def generate_metrics(self, circuit):
        qc = QuantumCircuit.from_qasm_file(self.generate_path_file(circuit))
        metrics = generate_metrics(qc)
        return metrics

    def assert_metric(self, circuit, expected_metrics, metric):
        metrics = self.generate_metrics(circuit)
        assert round(metrics[metric], 9) == round(expected_metrics[metric], 9)


class TestBasicMetrics(ITest):
    def test_n_qubits_metrics(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_NUMBER_QUBITS)

    def test_n_gates_metrics(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_NUMBER_GATES)

    def test_n_2gates_metrics(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_NUMBER_2_GATES)

    def test_depth_metrics(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_DEPTH)

    def test_consecutive_2gates_metrics(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_CONSECUTIVE_2_GATES)

    def test_avg_2gates_x_qubit_metrics(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_AVG_2_GATES_X_QUBIT)

    def test_n_unique_operands_metrics(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_N_UNIQUE_OPERANDS)

    def test_n_unique_gates_metrics(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_N_UNIQUE_GATES)

    def test_n_operands_metrics(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_N_OPERANDS)


class TestDerivedMetrics(ITest):
    def test_parallelism_metric(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_PARALLELISM)

    def test_critical_depth_metric(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_CRITICAL_DEPTH)

    def test_entanglement_ratio_metric(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_ENTANGLEMENT_RATIO)

    def test_program_communication_metric(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_PROGRAM_COMMUNICATION)

    def test_entanglement_variance_metric(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_ENTANGLEMENT_VARIANCE)

    def test_difficulty_metric(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_DIFFICULTY)

    def test_vocabulary_metric(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_VOCABULARY)

    def test_volume_metric(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_VOLUME)

    def test_effort_metric(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_EFFORT)

    def test_length_metric(self, circuit, expected_metrics):
        self.assert_metric(circuit, expected_metrics, METRIC_LENGTH)
