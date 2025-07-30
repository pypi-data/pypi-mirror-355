from QBenchAnalyzer.literal import METRIC_NUMBER_QUBITS, METRIC_NUMBER_GATES, METRIC_NUMBER_2_GATES, METRIC_DEPTH, \
    METRIC_CONSECUTIVE_2_GATES, METRIC_AVG_2_GATES_X_QUBIT, METRIC_PARALLELISM, METRIC_CRITICAL_DEPTH, \
    METRIC_ENTANGLEMENT_RATIO, METRIC_PROGRAM_COMMUNICATION, METRIC_ENTANGLEMENT_VARIANCE
from QBenchAnalyzer.metrics_generator import generate_metrics
from qiskit import QuantumCircuit
import pytest
import math


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


class TestErrors(ITest):
    def test_unsupported_gates(self):
        with pytest.raises(ValueError) as e_info:
            self.generate_metrics("3gate_circuit_3")
