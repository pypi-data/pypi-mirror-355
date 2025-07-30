from QBenchAnalyzer import StaticCircuitGenerator
import pytest


class TestCircuitGenerator:
    @pytest.mark.parametrize("path,circuit_name,min_number_length,number_of_qubits,expected_result", [
        ("./hello/", "circuit", 1, 1, "./hello/circuit_1.qasm"),
        ("./hello/", "circuit", 2, 1, "./hello/circuit_01.qasm"),
        ("./hello/", "circuit", 1, 10, "./hello/circuit_10.qasm"),
        ("./hello", "/circuit", 1, 1, "./hello/circuit_1.qasm"),
        ("./hello", "circuit", 1, 1, "./hello/circuit_1.qasm"),
        ("./hello/", "/circuit", 1, 1, "./hello/circuit_1.qasm"),
    ])
    def test_scg_generate_path(self, path, circuit_name, min_number_length, number_of_qubits, expected_result):
        scg = StaticCircuitGenerator(name='TestSCG', path=path, circuit_name=circuit_name,
                                     min_number_length=min_number_length)
        assert scg._generate_path(number_of_qubits) == expected_result



