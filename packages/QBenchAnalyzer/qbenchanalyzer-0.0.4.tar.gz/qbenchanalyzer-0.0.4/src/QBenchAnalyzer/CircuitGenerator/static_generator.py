from .generator_interface import ICircuitGenerator
from qiskit import QuantumCircuit


class StaticCircuitGenerator(ICircuitGenerator):
    def __init__(self, name, path, circuit_name, min_number_length=0):
        super().__init__(name)
        self.path = path
        self.circuit_name = circuit_name
        self.min_number_length = min_number_length

    def _generate_path(self, number_of_qubits):
        str_number_of_qubits = str(number_of_qubits)
        str_append_zeros = '0' * (self.min_number_length - len(str_number_of_qubits)) if self.min_number_length > len(
            str_number_of_qubits) else ''
        i_path = len(self.path) if self.path[-1] != "/" else len(self.path)-1
        i_cir_name = 0 if self.circuit_name[0] != "/" else 1
        str_n_qubits = f"{str_append_zeros}{str_number_of_qubits}"
        file_name = f"/{self.circuit_name[i_cir_name:]}_{str_n_qubits}.qasm"
        return self.path[:i_path] + file_name

    def generate_qiskit_circuit(self, number_of_qubits):
        circuit_path = self._generate_path(number_of_qubits)
        qc = QuantumCircuit.from_qasm_file(circuit_path)
        return qc
