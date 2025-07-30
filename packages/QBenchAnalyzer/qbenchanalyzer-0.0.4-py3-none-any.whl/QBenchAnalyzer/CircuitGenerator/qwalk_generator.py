from qiskit import AncillaRegister, QuantumCircuit, QuantumRegister
from .generator_interface import ICircuitGenerator


class QWalkGenerator(ICircuitGenerator):
    def __init__(self, name="QWalk", depth=1, ancillary_mode="noancilla"):
        super().__init__(name)
        self.depth = depth
        self.ancillary_mode = ancillary_mode

    def _standardize_qasm(self, str_qasm):
        import re

        split_line = str_qasm[:53].split("\n")
        n = int(split_line[2].split("[")[1].split(']')[0])

        rep = {
            "qreg coin[1];\n": "",
            f"qreg node[{n}]": f"qreg node[{n+1}]",
            "coin[0]": f"node[{n}]"
        }
        rep = dict((re.escape(k), v) for k, v in rep.items())
        pattern = re.compile("|".join(rep.keys()))
        str_qasm = pattern.sub(lambda m: rep[re.escape(m.group(0))], str_qasm)
        return str_qasm

    def generate_qiskit_circuit(self, number_of_qubits):
        n = number_of_qubits - 1                # One is used for the coin
        coin = QuantumRegister(1, "coin")
        node = QuantumRegister(n, "node")

        # Calculate how many qubits are needed for ancilla
        n_anc = 0
        ancillary_cutoff_recursion = 3
        if self.ancillary_mode == "recursion" and n > ancillary_cutoff_recursion:
            n_anc = 1
        ancillary_cutoff_vchain = 2
        if (self.ancillary_mode == "v-chain" or self.ancillary_mode == "v-chain-dirty") and n > ancillary_cutoff_vchain:
            n_anc = n - 2

        # Create the circuit
        if n_anc == 0:          # Without ancilla
            qc = QuantumCircuit(node, coin, name="qwalk")
            for _ in range(self.depth):
                # Hadamard coin operator
                qc.h(coin)
                # Controlled increment
                for i in range(0, n - 1):
                    qc.mcx(coin[:] + node[i + 1:], node[i], mode=self.ancillary_mode)
                qc.cx(coin, node[n - 1])
                # Controlled decrement
                qc.x(coin)
                qc.x(node[1:])
                for i in range(0, n - 1):
                    qc.mcx(coin[:] + node[i + 1:], node[i], mode=self.ancillary_mode)
                qc.cx(coin, node[n - 1])
                qc.x(node[1:])
                qc.x(coin)
        else:          # With ancilla
            anc = AncillaRegister(n_anc, "anc")
            qc = QuantumCircuit(node, coin, anc, name="qwalk")
            for _ in range(self.depth):
                # Hadamard coin operator
                qc.h(coin)
                # Controlled increment
                for i in range(0, n - 1):
                    qc.mcx(
                        coin[:] + node[i + 1:],
                        node[i],
                        mode=self.ancillary_mode,
                        ancilla_qubits=anc[:],
                    )
                qc.cx(coin, node[n - 1])
                # Controlled decrement
                qc.x(coin)
                qc.x(node[1:])
                for i in range(0, n - 1):
                    qc.mcx(
                        coin[:] + node[i + 1:],
                        node[i],
                        mode=self.ancillary_mode,
                        ancilla_qubits=anc[:],
                    )
                qc.cx(coin, node[n - 1])
                qc.x(node[1:])
                qc.x(coin)
        qc.measure_all()
        return qc
