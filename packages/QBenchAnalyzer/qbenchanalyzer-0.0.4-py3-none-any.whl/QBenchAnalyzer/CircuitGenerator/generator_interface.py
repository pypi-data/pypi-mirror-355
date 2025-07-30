from qiskit import QuantumCircuit
from qiskit.qasm2 import dumps


class ICircuitGenerator:
    def __init__(self, name):
        self.name = name

    def generate_qiskit_circuit(self, number_of_qubits) -> QuantumCircuit:
        pass

    def _standardize_qasm(self, str_qasm):
        return str_qasm

    def generate_and_save_as_qasm(self, number_of_qubits, file_name):
        qc = self.generate_qiskit_circuit(number_of_qubits)
        qasm_str = dumps(qc)
        qasm_str = self._standardize_qasm(qasm_str)
        with open(file_name, 'w') as f:
            f.write(qasm_str)
