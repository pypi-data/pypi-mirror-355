# QBenchAnalyzer
A tool to generate a set of metrics for quantum circuits.

## How to use it
You can find an example of usage in the `demo.py` file. In general, you only want to use the
`generate_metrics` method. Here is a little example of how to use it.

```python
from QBenchAnalyzer import generate_metrics
from qiskit import QuantumCircuit

circuit = "qaoa_vanilla_04.qasm"
qc = QuantumCircuit.from_qasm_file(circuit)
metrics = generate_metrics(qc)
print(metrics)
```

and, if you used the same circuit as the included in the repository, this will return the following set of metrics:

```python
{'qubit_connections': {2: {0, 1, 3}, 3: {0, 1, 2}, 1: {0, 2, 3}, 0: {1, 2, 3}}, 'n_qubits': 4, 
 'n_2gates_x_qubit': {2: 6, 3: 6, 1: 6, 0: 6}, 'n_gates': 26, 'depth': 17, 'avg_2gates_x_qubit': 6.0, 
 'n_consecutive_2_gates': 3, 'n_2_gates': 12, 'n_2gates_critical_path': 10, 'entanglement_ratio': 0.46153846153846156, 
 'critical_depth': 0.8333333333333334, 'parallelism': 0.17647058823529407, 'program_communication': 1.0, 
 'entanglement_variance': 0.0}
```

Alternatively, you can generate predefined images using the method `analyze_circuit_group_structural`, which will generate
an analysis of the metrics for a group of circuits. For doing so, you will need to implement a class that
implements the `ICircuitGenerator` interface and use it to tell the method which circuits will you want to use.
Here is an example of a functional script for calculating the metrics of the QFT circuits using the circuits between 5 and
10 qubits:

```python
# Importing all the necessary stuff
from QBenchAnalyzer.circuit_generator import ICircuitGenerator
from QBenchAnalyzer import analyze_circuit_group_structural
from qiskit import QuantumCircuit

# Creating a class that could read all the circuits
class CircuitGenerator(ICircuitGenerator): # It is important that implement the ICircuitGenerator
    def __init__(self, name, file_name):
        super().__init__(name)           # Title of the image
        self.file_name = file_name       # File name of the circuits to read

    def generate_qiskit_circuit(self, number_of_qubits):
        # Calculate the path of the circuit with 'number_of_qubits' for reading
        file_path = f"./test/{self.file_name}_{number_of_qubits}.qasm" 
        # Return the circuit as a QuantumCircuit object
        return QuantumCircuit.from_qasm_file(file_path)

# Call this method to generate the graphic image of all metrics of one circuit group
analyze_circuit_group_structural(
    CircuitGenerator("Testing QFT", "qft"), # Instance of the circuit generator
    5,                                      # Smallest number of qubits of the circuit group to read
    10,                                     # Bigger number of qubits of the circuit group to read
    "example.jpg",                          # Name for the output image
    "./images/"                             # Path were the output should be store
)
```
Executing the example will output an image that will look like the following:

![Example of the image generated](./example.jpg)

And the final working directory tree will look like:
```
.
├── images
│   ├── example.jpg
├── test
│   ├── qft_5.qasm
│   ├── qft_6.qasm
│   ├── qft_7.qasm
│   ├── qft_8.qasm
│   ├── qft_9.qasm
│   └── qft_10.qasm
├── main.py
```

Also, if you are using statical predefined circuits, you can use the class `StaticCircuitGenerator`
to simplify, as shown in the following example:
```python
# Importing all the necessary stuff
from QBenchAnalyzer.circuit_generator import StaticCircuitGenerator
from QBenchAnalyzer import analyze_circuit_group_structural
    
# Create the instance of the StaticCircuitGenerator
circuit_generator = StaticCircuitGenerator(name='Testing QFT', path="./test/", circuit_name="qft")

# Call this method to generate the graphic image of all metrics of one circuit group
analyze_circuit_group_structural(
    circuit_generator,                 # Instance of the circuit generator
    5,                                 # Smallest number of qubits of the circuit group to read
    10,                                # Bigger number of qubits of the circuit group to read
    "example.jpg",                     # Name for the output image
    "./images/"                        # Path were the output should be store
)
```

## Contributing
If you want to make changes, it is needed to test all the changes in local before a merge request.
To do it, it is needed to install the local changes first, and then run the test. You can use the
following commands as a guide:
```
pip install .
python3 -m pytest
```