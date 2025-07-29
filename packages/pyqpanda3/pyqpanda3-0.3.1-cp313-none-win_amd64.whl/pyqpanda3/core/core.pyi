import numpy
from typing import Any, ClassVar, overload

Gate: OpType
Measure: OpType

class CBit:
    def __init__(self, arg0: int) -> None:
        """__init__(self: core.CBit, arg0: int) -> None

        Initialize a CBit with an address.
        """
    def get_cbit_addr(self) -> int:
        """get_cbit_addr(self: core.CBit) -> int

        Get the address of the CBit.
        """
    def __int__(self) -> int:
        """__int__(self: core.CBit) -> int

        Convert the CBit to its address as an integer.
        """

class CPUQVM:
    def __init__(self) -> None:
        """__init__(self: core.CPUQVM) -> None"""
    def expval_hamiltonian(self, prog: QProg, hamiltonian, shots: int = ..., noise_model: NoiseModel = ...) -> float:
        """expval_hamiltonian(self: core.CPUQVM, prog: core.QProg, hamiltonian: QPanda3::Hamiltonian, shots: int = 1000, noise_model: core.NoiseModel = <core.NoiseModel object at 0x00000218DA6C30F0>) -> float


         @brief Calculate the expected value of a given Hamiltonian with respect to a quantum program.
 
         @details This member function of the CPUQVM class computes the expected value (or expectation value) 
         of a specified Hamiltonian using a quantum program. It allows for the simulation of quantum 
         circuits with optional noise modeling.
 
         @param prog The quantum program to be executed.
         @param hamiltonian The Hamiltonian for which the expected value is to be calculated.
         @param shots The number of times the quantum program is sampled to estimate the expected value. 
                      Defaults to 1000 if not specified.
         @param noise_model The noise model to be applied during the simulation. Defaults to a default-constructed 
                      NoiseModel if not specified.
 
         @return The expected value of the Hamiltonian as a double.
         
        """
    def expval_pauli_operator(self, prog: QProg, pauli_operator, shots: int = ..., noise_model: NoiseModel = ...) -> float:
        """expval_pauli_operator(self: core.CPUQVM, prog: core.QProg, pauli_operator: QPanda3::PauliOperator, shots: int = 1000, noise_model: core.NoiseModel = <core.NoiseModel object at 0x00000218DA6F2D30>) -> float


         @brief Calculate the expected value of a given PauliOperator with respect to a quantum program.
 
         @details This member function of the CPUQVM class computes the expected value (or expectation value) 
         of a specified PauliOperator using a quantum program. It allows for the simulation of quantum 
         circuits with optional noise modeling.
 
         @param prog The quantum program to be executed.
         @param pauli_operator The PauliOperator for which the expected value is to be calculated.
         @param shots The number of times the quantum program is sampled to estimate the expected value. 
                      Defaults to 1000 if not specified.
         @param noise_model The noise model to be applied during the simulation. Defaults to a default-constructed 
                      NoiseModel if not specified.
 
         @return The expected value of the PauliOperator as a double.
         
        """
    def result(self) -> QResult:
        """result(self: core.CPUQVM) -> core.QResult


        @brief Get the result of the quantum program execution.
        @return The result of the quantum simulation.
         
        """
    def run(self, prog: QProg, shots: int, model: NoiseModel = ...) -> None:
        """run(self: core.CPUQVM, prog: core.QProg, shots: int, model: core.NoiseModel = <core.NoiseModel object at 0x00000218DA6DD1F0>) -> None


        @brief Run a quantum program using the CPUQVM simulator.
        @param prog The quantum program to be executed.
        @param shots The number of shots (repetitions) for measurement.
        @param model The noise model to apply (default is NoiseModel()).

        @return None
         
        """

class DAGNode:
    def __init__(self, arg0: QGate, arg1: int) -> None:
        """__init__(self: core.DAGNode, arg0: core.QGate, arg1: int) -> None"""
    def add_post_node(self, arg0: DAGNode) -> None:
        """add_post_node(self: core.DAGNode, arg0: core.DAGNode) -> None"""
    def add_pre_node(self, arg0: DAGNode) -> None:
        """add_pre_node(self: core.DAGNode, arg0: core.DAGNode) -> None"""
    def get_index(self) -> int:
        """get_index(self: core.DAGNode) -> int"""
    def get_post_nodes(self) -> list[DAGNode]:
        """get_post_nodes(self: core.DAGNode) -> list[core.DAGNode]"""
    def get_pre_nodes(self) -> list[DAGNode]:
        """get_pre_nodes(self: core.DAGNode) -> list[core.DAGNode]"""
    def get_qgate(self) -> QGate:
        """get_qgate(self: core.DAGNode) -> core.QGate"""
    def remove_edges(self) -> None:
        """remove_edges(self: core.DAGNode) -> None"""
    @overload
    def remove_post_node(self, arg0: DAGNode) -> None:
        """remove_post_node(*args, **kwargs)
        Overloaded function.

        1. remove_post_node(self: core.DAGNode, arg0: core.DAGNode) -> None

        2. remove_post_node(self: core.DAGNode, arg0: int) -> None
        """
    @overload
    def remove_post_node(self, arg0: int) -> None:
        """remove_post_node(*args, **kwargs)
        Overloaded function.

        1. remove_post_node(self: core.DAGNode, arg0: core.DAGNode) -> None

        2. remove_post_node(self: core.DAGNode, arg0: int) -> None
        """
    @overload
    def remove_pre_node(self, arg0: DAGNode) -> None:
        """remove_pre_node(*args, **kwargs)
        Overloaded function.

        1. remove_pre_node(self: core.DAGNode, arg0: core.DAGNode) -> None

        2. remove_pre_node(self: core.DAGNode, arg0: int) -> None
        """
    @overload
    def remove_pre_node(self, arg0: int) -> None:
        """remove_pre_node(*args, **kwargs)
        Overloaded function.

        1. remove_pre_node(self: core.DAGNode, arg0: core.DAGNode) -> None

        2. remove_pre_node(self: core.DAGNode, arg0: int) -> None
        """

class DAGQCircuit:
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: core.DAGQCircuit) -> None


        @brief Construct a new DAGQCircuit object.
             

        2. __init__(self: core.DAGQCircuit, arg0: core.DAGQCircuit) -> None


        @brief Copy constructor for DAGQCircuit.
        @param other The other DAGQCircuit to copy from.
             

        3. __init__(self: core.DAGQCircuit, circuit: core.QCircuit) -> None


        @brief Construct a new DAGQCircuit object from a QCircuit.
        @param circuit The QCircuit to convert.
             
        """
    @overload
    def __init__(self, arg0: DAGQCircuit) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: core.DAGQCircuit) -> None


        @brief Construct a new DAGQCircuit object.
             

        2. __init__(self: core.DAGQCircuit, arg0: core.DAGQCircuit) -> None


        @brief Copy constructor for DAGQCircuit.
        @param other The other DAGQCircuit to copy from.
             

        3. __init__(self: core.DAGQCircuit, circuit: core.QCircuit) -> None


        @brief Construct a new DAGQCircuit object from a QCircuit.
        @param circuit The QCircuit to convert.
             
        """
    @overload
    def __init__(self, circuit: QCircuit) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: core.DAGQCircuit) -> None


        @brief Construct a new DAGQCircuit object.
             

        2. __init__(self: core.DAGQCircuit, arg0: core.DAGQCircuit) -> None


        @brief Copy constructor for DAGQCircuit.
        @param other The other DAGQCircuit to copy from.
             

        3. __init__(self: core.DAGQCircuit, circuit: core.QCircuit) -> None


        @brief Construct a new DAGQCircuit object from a QCircuit.
        @param circuit The QCircuit to convert.
             
        """
    @overload
    def add_edge(self, src_node: DAGNode, target_node: DAGNode) -> None:
        """add_edge(*args, **kwargs)
        Overloaded function.

        1. add_edge(self: core.DAGQCircuit, src_node: core.DAGNode, target_node: core.DAGNode) -> None


        @brief Add an edge between two nodes.
        @param src_node Pointer to the source node.
        @param target_node Pointer to the target node.
             

        2. add_edge(self: core.DAGQCircuit, src_index: int, target_index: int) -> None


        @brief Add an edge between two nodes using their indices.
        @param src_index The index of the source node.
        @param target_index The index of the target node.
             
        """
    @overload
    def add_edge(self, src_index: int, target_index: int) -> None:
        """add_edge(*args, **kwargs)
        Overloaded function.

        1. add_edge(self: core.DAGQCircuit, src_node: core.DAGNode, target_node: core.DAGNode) -> None


        @brief Add an edge between two nodes.
        @param src_node Pointer to the source node.
        @param target_node Pointer to the target node.
             

        2. add_edge(self: core.DAGQCircuit, src_index: int, target_index: int) -> None


        @brief Add an edge between two nodes using their indices.
        @param src_index The index of the source node.
        @param target_index The index of the target node.
             
        """
    def add_vertex(self, gate: QGate) -> int:
        """add_vertex(self: core.DAGQCircuit, gate: core.QGate) -> int


        @brief Add a vertex to the circuit.
        @param gate The quantum gate to add.
        @return size_t The index of the added vertex.
             
        """
    def add_vertexs(self, gates: list[QGate]) -> list[int]:
        """add_vertexs(self: core.DAGQCircuit, gates: list[core.QGate]) -> list[int]


        @brief Add multiple vertices to the circuit.
        @param gates A vector of quantum gates to add.
        @return std::vector<size_t> A vector of indices for the added vertices.
             
        """
    def append(self, gate: QGate) -> None:
        """append(self: core.DAGQCircuit, gate: core.QGate) -> None


        @brief Append a gate to the circuit.
        @param gate The quantum gate to append.
             
        """
    def build(self) -> None:
        """build(self: core.DAGQCircuit) -> None


        @brief Build the circuit.
             
        """
    def clear(self) -> None:
        """clear(self: core.DAGQCircuit) -> None


        @brief Clear the circuit.
             
        """
    def edges(self) -> list[tuple[int, int]]:
        """edges(self: core.DAGQCircuit) -> list[tuple[int, int]]


        @brief Returns the list of edges in the graph.
        @return std::vector<std::pair<int,int>> The list of edges.
            
        """
    def from_circuit(self, circuit: QCircuit, using_only_q2_gate: bool = ...) -> None:
        """from_circuit(self: core.DAGQCircuit, circuit: core.QCircuit, using_only_q2_gate: bool = False) -> None


        @brief Initialize the circuit from a QCircuit.
        @param circuit The QCircuit to convert.
        @param using_only_q2_gate Flag to determine if only Q2 gates are used.
             
        """
    def from_qprog(self, prog: QProg, using_only_q2_gate: bool = ..., is_pilot: bool = ...) -> None:
        """from_qprog(self: core.DAGQCircuit, prog: core.QProg, using_only_q2_gate: bool = False, is_pilot: bool = False) -> None


        @brief Initialize the circuit from a QProg.
        @param prog The QProg to convert.
        @param using_only_q2_gate Flag to determine if only Q2 gates are used.
        @param is_pilot Flag to determine if used for Pilot transpile.
             
        """
    def gate_list(self) -> list[QGate]:
        """gate_list(self: core.DAGQCircuit) -> list[core.QGate]


        @brief Get the list of gates in the circuit.
        @return std::vector<QGate> The list of gates.
            
        """
    def gates(self) -> list[QGate]:
        """gates(self: core.DAGQCircuit) -> list[core.QGate]


        @brief Returns the list of gates in the graph.
        @return std::vector<QGate> The list of gates.
            
        """
    def get_back_node(self) -> list[int]:
        """get_back_node(self: core.DAGQCircuit) -> list[int]


        @brief Get the last node in the circuit.
        @return std::vector<size_t> The qubits of the last node.
            
        """
    def get_depth(self) -> int:
        """get_depth(self: core.DAGQCircuit) -> int


        @brief Get the depth of the circuit.
        @return size_t The depth of the circuit.
             
        """
    def get_gate(self, gate_index: int) -> QGate:
        """get_gate(self: core.DAGQCircuit, gate_index: int) -> core.QGate


        @brief Get a gate by index.
        @param gate_index The index of the gate.
        @return QGate& Reference to the gate.
             
        """
    def get_initial_front_layer_gates(self) -> list[QGate]:
        """get_initial_front_layer_gates(self: core.DAGQCircuit) -> list[core.QGate]


        @brief Returns the initial front layer gates of the graph.
        @return std::vector<QGate> The initial front layer gates.
            
        """
    def get_num_gates(self) -> int:
        """get_num_gates(self: core.DAGQCircuit) -> int


        @brief Get the number of gates in the circuit.
        @return size_t The number of gates.
             
        """
    def get_vertex(self, node_index: int) -> DAGNode:
        """get_vertex(self: core.DAGQCircuit, node_index: int) -> core.DAGNode


        @brief Get a vertex by index.
        @param node_index The index of the vertex.
        @return DAGNode* Pointer to the vertex.
             
        """
    def get_vertex_list(self) -> list[DAGNode]:
        """get_vertex_list(self: core.DAGQCircuit) -> list[core.DAGNode]


        @brief Get the list of vertices.
        @return std::list<DAGNode>& Reference to the list of vertices.
             
        """
    def get_vertex_vec(self) -> list[DAGNode]:
        """get_vertex_vec(self: core.DAGQCircuit) -> list[core.DAGNode]


        @brief Get the vector of vertices.
        @return const std::vector<DAGNode*>& Vector of vertex pointers.
             
        """
    def in_degree(self, node_index: int) -> int:
        """in_degree(self: core.DAGQCircuit, node_index: int) -> int


        @brief Get the in-degree of a specified node.
        @param node_index The index of the node.
        @return size_t The in-degree of the node.
             
        """
    def in_edges(self, node_index: int) -> list[list[int]]:
        """in_edges(self: core.DAGQCircuit, node_index: int) -> list[list[int]]


        @brief Get the incoming edges for a specified node.
        @param node_index The index of the node.
        @return std::vector<std::vector<size_t>> Incoming edges.
             
        """
    def in_neighbors(self, node_index: int) -> list[int]:
        """in_neighbors(self: core.DAGQCircuit, node_index: int) -> list[int]


        @brief Get the incoming neighbors for a specified node.
        @param node_index The index of the node.
        @return std::vector<size_t> Incoming neighbors.
             
        """
    def insert(self, index: int, gates: list[QGate]) -> None:
        """insert(self: core.DAGQCircuit, index: int, gates: list[core.QGate]) -> None


        @brief Insert gates at a specific index.
        @param index The index at which to insert gates.
        @param gates The gates to insert.
             
        """
    def layers(self) -> list[list[int]]:
        """layers(self: core.DAGQCircuit) -> list[list[int]]


        @brief Get the layers of the circuit.
        @return std::vector<std::vector<int>> The layers of gates.
             
        """
    def longest_path(self) -> list[int]:
        """longest_path(self: core.DAGQCircuit) -> list[int]


        @brief Returns the longest path in the graph.
        @return std::vector<int> The longest path.
            
        """
    def nodes(self) -> list[int]:
        """nodes(self: core.DAGQCircuit) -> list[int]


        @brief Returns the list of nodes in the graph.
        @return std::vector<int> The list of nodes.
            
        """
    def out_degree(self, node_index: int) -> int:
        """out_degree(self: core.DAGQCircuit, node_index: int) -> int


        @brief Get the out-degree of a specified node.
        @param node_index The index of the node.
        @return size_t The out-degree of the node.
             
        """
    def out_edges(self, node_index: int) -> list[list[int]]:
        """out_edges(self: core.DAGQCircuit, node_index: int) -> list[list[int]]


        @brief Get the outgoing edges for a specified node.
        @param node_index The index of the node.
        @return std::vector<std::vector<size_t>> Outgoing edges.
             
        """
    def out_neighbors(self, node_index: int) -> list[int]:
        """out_neighbors(self: core.DAGQCircuit, node_index: int) -> list[int]


        @brief Get the outgoing neighbors for a specified node.
        @param node_index The index of the node.
        @return std::vector<size_t> Outgoing neighbors.
             
        """
    def reallocate_index(self) -> None:
        """reallocate_index(self: core.DAGQCircuit) -> None


        @brief Reallocate the indices of the nodes.
            
        """
    def remove_back(self) -> None:
        """remove_back(self: core.DAGQCircuit) -> None


        @brief Remove the last node.
            
        """
    @overload
    def remove_edge(self, src_node: DAGNode, target_node: DAGNode) -> None:
        """remove_edge(*args, **kwargs)
        Overloaded function.

        1. remove_edge(self: core.DAGQCircuit, src_node: core.DAGNode, target_node: core.DAGNode) -> None


        @brief Remove an edge between two nodes.
        @param src_node Pointer to the source node.
        @param target_node Pointer to the target node.
             

        2. remove_edge(self: core.DAGQCircuit, src_index: int, target_index: int) -> None


        @brief Remove an edge using the indices of two nodes.
        @param src_index The index of the source node.
        @param target_index The index of the target node.
             
        """
    @overload
    def remove_edge(self, src_index: int, target_index: int) -> None:
        """remove_edge(*args, **kwargs)
        Overloaded function.

        1. remove_edge(self: core.DAGQCircuit, src_node: core.DAGNode, target_node: core.DAGNode) -> None


        @brief Remove an edge between two nodes.
        @param src_node Pointer to the source node.
        @param target_node Pointer to the target node.
             

        2. remove_edge(self: core.DAGQCircuit, src_index: int, target_index: int) -> None


        @brief Remove an edge using the indices of two nodes.
        @param src_index The index of the source node.
        @param target_index The index of the target node.
             
        """
    @overload
    def remove_vertex(self, node: DAGNode) -> None:
        """remove_vertex(*args, **kwargs)
        Overloaded function.

        1. remove_vertex(self: core.DAGQCircuit, node: core.DAGNode) -> None


        @brief Remove a vertex from the circuit.
        @param node Pointer to the node to remove.
             

        2. remove_vertex(self: core.DAGQCircuit, node_index: int) -> None


        @brief Remove a vertex by index.
        @param node_index The index of the vertex to remove.
             
        """
    @overload
    def remove_vertex(self, node_index: int) -> None:
        """remove_vertex(*args, **kwargs)
        Overloaded function.

        1. remove_vertex(self: core.DAGQCircuit, node: core.DAGNode) -> None


        @brief Remove a vertex from the circuit.
        @param node Pointer to the node to remove.
             

        2. remove_vertex(self: core.DAGQCircuit, node_index: int) -> None


        @brief Remove a vertex by index.
        @param node_index The index of the vertex to remove.
             
        """
    def reserve_size(self) -> None:
        """reserve_size(self: core.DAGQCircuit) -> None


        @brief Reserve size for node vector.
            
        """
    def to_circuit(self) -> QCircuit:
        """to_circuit(self: core.DAGQCircuit) -> core.QCircuit


        @brief Get the QCircuit representation of the DAG.
        @return const QCircuit& Reference to the QCircuit.
             
        """
    def to_qprog(self) -> QProg:
        """to_qprog(self: core.DAGQCircuit) -> core.QProg


        @brief Convert the circuit to a QProg.
        @return QProg The converted QProg.
             
        """
    def two_qubit_gate_nodes(self) -> list[int]:
        """two_qubit_gate_nodes(self: core.DAGQCircuit) -> list[int]


        @brief Returns the list of nodes associated with two-qubit gates.
        @return std::vector<int> The list of nodes.
            
        """
    def two_qubit_gates(self) -> list[QGate]:
        """two_qubit_gates(self: core.DAGQCircuit) -> list[core.QGate]


        @brief Returns the list of two-qubit gates in the graph.
        @return std::vector<QGate> The list of two-qubit gates.
            
        """
    def __lshift__(self, arg0: QGate) -> DAGQCircuit:
        """__lshift__(self: core.DAGQCircuit, arg0: core.QGate) -> core.DAGQCircuit


                        @brief Overloaded operator to append a gate.
                        @param gate The quantum gate to append.
                        @return DAGQCircuit& Reference to this instance.
        """

class DensityMatrixSimulator:
    def __init__(self) -> None:
        """__init__(self: core.DensityMatrixSimulator) -> None"""
    def density_matrix(self) -> numpy.ndarray[numpy.complex128[m, n]]:
        """density_matrix(self: core.DensityMatrixSimulator) -> numpy.ndarray[numpy.complex128[m, n]]


        @brief Get the density matrix of the quantum system.
        @return A matrix representing the density matrix.
         
        """
    def reduced_density_matrix(self, arg0: list[int]) -> numpy.ndarray[numpy.complex128[m, n]]:
        """reduced_density_matrix(self: core.DensityMatrixSimulator, arg0: list[int]) -> numpy.ndarray[numpy.complex128[m, n]]


        @brief Get the reduced density matrix for a subset of qubits.
        @param qubits The indices of the qubits.

        @return A matrix representing the reduced density matrix.
         
        """
    def run(self, prog: QProg, model: NoiseModel = ...) -> None:
        """run(self: core.DensityMatrixSimulator, prog: core.QProg, model: core.NoiseModel = <core.NoiseModel object at 0x00000218DA6F10F0>) -> None


        @brief Run a quantum program with noise model.
        @param prog The quantum program to run.
        @param model The noise model to apply during the run.

        @return A result of the simulation.
         
        """
    @overload
    def state_prob(self, index: int) -> float:
        """state_prob(*args, **kwargs)
        Overloaded function.

        1. state_prob(self: core.DensityMatrixSimulator, index: int) -> float


        @brief Get the probability of a specific state.
        @param qubit_idx The index of the qubit to check.

        @return The probability of the state.
         

        2. state_prob(self: core.DensityMatrixSimulator, index: str) -> float


        @brief Get the probability of a specific state using a binary string representation.
        @param state The state as a binary string.

        @return The probability of the state.
         
        """
    @overload
    def state_prob(self, index: str) -> float:
        """state_prob(*args, **kwargs)
        Overloaded function.

        1. state_prob(self: core.DensityMatrixSimulator, index: int) -> float


        @brief Get the probability of a specific state.
        @param qubit_idx The index of the qubit to check.

        @return The probability of the state.
         

        2. state_prob(self: core.DensityMatrixSimulator, index: str) -> float


        @brief Get the probability of a specific state using a binary string representation.
        @param state The state as a binary string.

        @return The probability of the state.
         
        """
    @overload
    def state_probs(self) -> list[float]:
        """state_probs(*args, **kwargs)
        Overloaded function.

        1. state_probs(self: core.DensityMatrixSimulator) -> list[float]


        @brief Get the probabilities of all possible states.
        @return A list of probabilities for all possible states.
         

        2. state_probs(self: core.DensityMatrixSimulator, qubits: list[int]) -> list[float]


        @brief Get the probabilities of states for specific qubits.
        @param qubits The indices of qubits.

        @return A list of probabilities for the specified qubits.
         

        3. state_probs(self: core.DensityMatrixSimulator, arg0: list[str]) -> list[float]


        @brief Get the probabilities of states for specific binary string representations.
        @param states A list of states as binary strings.

        @return A list of probabilities for the specified states.
         
        """
    @overload
    def state_probs(self, qubits: list[int]) -> list[float]:
        """state_probs(*args, **kwargs)
        Overloaded function.

        1. state_probs(self: core.DensityMatrixSimulator) -> list[float]


        @brief Get the probabilities of all possible states.
        @return A list of probabilities for all possible states.
         

        2. state_probs(self: core.DensityMatrixSimulator, qubits: list[int]) -> list[float]


        @brief Get the probabilities of states for specific qubits.
        @param qubits The indices of qubits.

        @return A list of probabilities for the specified qubits.
         

        3. state_probs(self: core.DensityMatrixSimulator, arg0: list[str]) -> list[float]


        @brief Get the probabilities of states for specific binary string representations.
        @param states A list of states as binary strings.

        @return A list of probabilities for the specified states.
         
        """
    @overload
    def state_probs(self, arg0: list[str]) -> list[float]:
        """state_probs(*args, **kwargs)
        Overloaded function.

        1. state_probs(self: core.DensityMatrixSimulator) -> list[float]


        @brief Get the probabilities of all possible states.
        @return A list of probabilities for all possible states.
         

        2. state_probs(self: core.DensityMatrixSimulator, qubits: list[int]) -> list[float]


        @brief Get the probabilities of states for specific qubits.
        @param qubits The indices of qubits.

        @return A list of probabilities for the specified qubits.
         

        3. state_probs(self: core.DensityMatrixSimulator, arg0: list[str]) -> list[float]


        @brief Get the probabilities of states for specific binary string representations.
        @param states A list of states as binary strings.

        @return A list of probabilities for the specified states.
         
        """

class Encode:
    def __init__(self) -> None:
        """__init__(self: core.Encode) -> None"""
    @overload
    def amplitude_encode(self, qubits: list[int], data: list[float]) -> None:
        """amplitude_encode(*args, **kwargs)
        Overloaded function.

        1. amplitude_encode(self: core.Encode, qubits: list[int], data: list[float]) -> None


        @brief Performs amplitude encoding on the given qubits.

        @details This function encodes classical data into a quantum state using amplitude encoding. The classical data is used to prepare the quantum state, which is then encoded into the qubits specified. This is commonly used for quantum machine learning and quantum data processing.

        @param qubit The quantum vector to be encoded.
        @param data The classical data to be encoded into the quantum state.

        @return The encoded quantum state.


        2. amplitude_encode(self: core.Encode, qubits: list[int], data: list[complex]) -> None


        @brief Performs amplitude encoding using complex numbers on the given qubits.

        @details This function encodes classical complex data into a quantum state using amplitude encoding. The provided complex data is normalized and mapped onto the amplitudes of the quantum state, allowing for efficient quantum representation of classical information.

        @param qubit The quantum vector to be encoded.
        @param data The classical complex data to be encoded into the quantum state.

        @return The encoded quantum state.
    
        """
    @overload
    def amplitude_encode(self, qubits: list[int], data: list[complex]) -> None:
        """amplitude_encode(*args, **kwargs)
        Overloaded function.

        1. amplitude_encode(self: core.Encode, qubits: list[int], data: list[float]) -> None


        @brief Performs amplitude encoding on the given qubits.

        @details This function encodes classical data into a quantum state using amplitude encoding. The classical data is used to prepare the quantum state, which is then encoded into the qubits specified. This is commonly used for quantum machine learning and quantum data processing.

        @param qubit The quantum vector to be encoded.
        @param data The classical data to be encoded into the quantum state.

        @return The encoded quantum state.


        2. amplitude_encode(self: core.Encode, qubits: list[int], data: list[complex]) -> None


        @brief Performs amplitude encoding using complex numbers on the given qubits.

        @details This function encodes classical complex data into a quantum state using amplitude encoding. The provided complex data is normalized and mapped onto the amplitudes of the quantum state, allowing for efficient quantum representation of classical information.

        @param qubit The quantum vector to be encoded.
        @param data The classical complex data to be encoded into the quantum state.

        @return The encoded quantum state.
    
        """
    @overload
    def amplitude_encode_recursive(self, qubits: list[int], data: list[float]) -> None:
        """amplitude_encode_recursive(*args, **kwargs)
        Overloaded function.

        1. amplitude_encode_recursive(self: core.Encode, qubits: list[int], data: list[float]) -> None


        @brief Performs recursive amplitude encoding on the given qubits.

        @details This function encodes classical data into a quantum state using recursive amplitude encoding. This method decomposes the encoding process into smaller subproblems, enabling efficient representation of high-dimensional data with a structured approach.

        @param qubit The quantum vector to be encoded.
        @param data The classical data to be encoded into the quantum state.

        @return The encoded quantum state.


        2. amplitude_encode_recursive(self: core.Encode, qubits: list[int], data: list[complex]) -> None


        @brief Encodes data into a quantum state using recursive amplitude encoding.

        @details This function recursively encodes an amplitude vector into a quantum circuit. The recursive approach efficiently decomposes the data encoding process, enabling structured representation of high-dimensional data.

        @param qubits The qubits used for encoding.
        @param data The amplitude vector to be encoded.

        @return The quantum circuit implementing the recursive amplitude encoding.

        """
    @overload
    def amplitude_encode_recursive(self, qubits: list[int], data: list[complex]) -> None:
        """amplitude_encode_recursive(*args, **kwargs)
        Overloaded function.

        1. amplitude_encode_recursive(self: core.Encode, qubits: list[int], data: list[float]) -> None


        @brief Performs recursive amplitude encoding on the given qubits.

        @details This function encodes classical data into a quantum state using recursive amplitude encoding. This method decomposes the encoding process into smaller subproblems, enabling efficient representation of high-dimensional data with a structured approach.

        @param qubit The quantum vector to be encoded.
        @param data The classical data to be encoded into the quantum state.

        @return The encoded quantum state.


        2. amplitude_encode_recursive(self: core.Encode, qubits: list[int], data: list[complex]) -> None


        @brief Encodes data into a quantum state using recursive amplitude encoding.

        @details This function recursively encodes an amplitude vector into a quantum circuit. The recursive approach efficiently decomposes the data encoding process, enabling structured representation of high-dimensional data.

        @param qubits The qubits used for encoding.
        @param data The amplitude vector to be encoded.

        @return The quantum circuit implementing the recursive amplitude encoding.

        """
    def angle_encode(self, qubits: list[int], data: list[float], gate_type: GateType = ...) -> None:
        """angle_encode(self: core.Encode, qubits: list[int], data: list[float], gate_type: core.GateType = GateType.RY_GATE) -> None


        @brief Encodes data into a quantum state using angle encoding.

        @details This function encodes classical data into a quantum circuit by mapping each data value to a corresponding qubit rotation angle. Angle encoding is commonly used in variational quantum algorithms and quantum machine learning.

        @param qubits The qubits used for encoding.
        @param prob_vec The data values to be encoded as rotation angles.

        @return The quantum circuit implementing the angle encoding.
        
        """
    @overload
    def approx_mps_encode(self, qubits: list[int], data: list[float], layers: int = ..., sweeps: int = ..., double2float: bool = ...) -> None:
        """approx_mps_encode(*args, **kwargs)
        Overloaded function.

        1. approx_mps_encode(self: core.Encode, qubits: list[int], data: list[float], layers: int = 3, sweeps: int = 100, double2float: bool = False) -> None


        @brief Performs Approximate Matrix Product State (MPS) encoding.

        @details This function encodes the input data into a quantum state using the Approximate Matrix Product State (MPS) encoding technique. MPS encoding is useful for efficiently representing quantum states with a low-rank approximation. The encoding is optimized by iteratively applying sweeps and adjusting the number of layers.

        @param qubits The qubits on which the encoding will be performed.
        @param input_data The classical input data(double) to be encoded into the quantum state.
        @param num_layers The number of layers for encoding. Default is 3.
        @param num_sweeps The number of sweeps for optimization. Default is 100.
        @param convert_to_float A flag to convert double data to float. Default is false.

        @return The encoded quantum circuit based on the input parameters.

        @raises run_fail An error occurred during the encoding process.


        2. approx_mps_encode(self: core.Encode, qubits: list[int], data: list[complex], layers: int = 3, sweeps: int = 100) -> None


        @brief Performs Approximate Matrix Product State (MPS) encoding.

        @details This function encodes the input data into a quantum state using the Approximate Matrix Product State (MPS) encoding technique. MPS encoding is useful for efficiently representing quantum states with a low-rank approximation. The encoding is optimized by iteratively applying sweeps and adjusting the number of layers.

        @param qubits The qubits on which the encoding will be performed.
        @param input_data The classical input data(complex) to be encoded into the quantum state.
        @param num_layers The number of layers for encoding. Default is 3.
        @param num_sweeps The number of sweeps for optimization. Default is 100.
        @param convert_to_float A flag to convert double data to float. Default is false.

        @return The encoded quantum circuit based on the input parameters.

        @raises run_fail An error occurred during the encoding process.

        """
    @overload
    def approx_mps_encode(self, qubits: list[int], data: list[complex], layers: int = ..., sweeps: int = ...) -> None:
        """approx_mps_encode(*args, **kwargs)
        Overloaded function.

        1. approx_mps_encode(self: core.Encode, qubits: list[int], data: list[float], layers: int = 3, sweeps: int = 100, double2float: bool = False) -> None


        @brief Performs Approximate Matrix Product State (MPS) encoding.

        @details This function encodes the input data into a quantum state using the Approximate Matrix Product State (MPS) encoding technique. MPS encoding is useful for efficiently representing quantum states with a low-rank approximation. The encoding is optimized by iteratively applying sweeps and adjusting the number of layers.

        @param qubits The qubits on which the encoding will be performed.
        @param input_data The classical input data(double) to be encoded into the quantum state.
        @param num_layers The number of layers for encoding. Default is 3.
        @param num_sweeps The number of sweeps for optimization. Default is 100.
        @param convert_to_float A flag to convert double data to float. Default is false.

        @return The encoded quantum circuit based on the input parameters.

        @raises run_fail An error occurred during the encoding process.


        2. approx_mps_encode(self: core.Encode, qubits: list[int], data: list[complex], layers: int = 3, sweeps: int = 100) -> None


        @brief Performs Approximate Matrix Product State (MPS) encoding.

        @details This function encodes the input data into a quantum state using the Approximate Matrix Product State (MPS) encoding technique. MPS encoding is useful for efficiently representing quantum states with a low-rank approximation. The encoding is optimized by iteratively applying sweeps and adjusting the number of layers.

        @param qubits The qubits on which the encoding will be performed.
        @param input_data The classical input data(complex) to be encoded into the quantum state.
        @param num_layers The number of layers for encoding. Default is 3.
        @param num_sweeps The number of sweeps for optimization. Default is 100.
        @param convert_to_float A flag to convert double data to float. Default is false.

        @return The encoded quantum circuit based on the input parameters.

        @raises run_fail An error occurred during the encoding process.

        """
    def basic_encode(self, qubits: list[int], data: str) -> None:
        """basic_encode(self: core.Encode, qubits: list[int], data: str) -> None


        @brief Performs basic quantum state encoding.

        @details This function implements a basic encoding scheme that maps classical string data onto a quantum circuit. The encoding method depends on the specific quantum algorithm and application.

        @param qubits The qubits used for encoding.
        @param data The string data to be encoded.

        @return The quantum circuit implementing the basic encoding.

        """
    def bid_amplitude_encode(self, qubits: list[int], data: list[float], split: int = ...) -> None:
        """bid_amplitude_encode(self: core.Encode, qubits: list[int], data: list[float], split: int = -1) -> None


        @brief Encodes data into a quantum state using BID encoding.

        @details This function implements BID encoding, which decomposes the target quantum state into smaller blocks iteratively. This method provides an efficient way to encode double amplitude.

        @param qubits The qubits used for encoding.
        @param data The amplitude vector representing the quantum state to be encoded.
        @param split The integer specifying the block size for iterative decomposition.

        @return The quantum circuit implementing the BID encoding.

        """
    def dc_amplitude_encode(self, qubits: list[int], data: list[float]) -> None:
        """dc_amplitude_encode(self: core.Encode, qubits: list[int], data: list[float]) -> None


        @brief Encodes data into a quantum state using DC amplitude encoding.

        @details This function implements DC (Divide-and-Conquer) amplitude encoding, which efficiently maps classical amplitude data onto a quantum circuit. This method leverages a hierarchical decomposition approach to optimize state preparation.

        @param qubits The qubits used for encoding.
        @param data The amplitude vector representing the quantum state to be encoded.

        @return The quantum circuit implementing the DC amplitude encoding.

        """
    def dense_angle_encode(self, qubits: list[int], data: list[float]) -> None:
        """dense_angle_encode(self: core.Encode, qubits: list[int], data: list[float]) -> None


        @brief Encodes data into a quantum state using dense angle encoding.

        @details This function performs dense angle encoding, mapping classical data values to qubit rotation angles in a more compact and information-efficient manner. This approach allows for enhanced expressivity in quantum circuits, making it useful for quantum machine learning and variational algorithms.

        @param qubits The qubits used for encoding.
        @param prob_vec The data values to be encoded as rotation angles.

        @return The quantum circuit implementing the dense angle encoding.

        """
    @overload
    def ds_quantum_state_preparation(self, qubits: list[int], data: dict[str, float]) -> None:
        """ds_quantum_state_preparation(*args, **kwargs)
        Overloaded function.

        1. ds_quantum_state_preparation(self: core.Encode, qubits: list[int], data: dict[str, float]) -> None


        @brief Prepares a quantum state based on provided parameters.

        @details This function prepares a quantum state on the given qubits by applying quantum gates defined by the provided state parameters. The quantum circuit generated can be used for further quantum computations or measurements.

        @param qubits The qubits on which the quantum state is to be prepared.
        @param data A map of state parameters (double) used for state preparation.

        @return The quantum circuit that prepares the desired quantum state.


        2. ds_quantum_state_preparation(self: core.Encode, qubits: list[int], data: dict[str, complex]) -> None


        @brief Prepares a quantum state based on provided parameters.

        @details This function prepares a quantum state on the given qubits by applying quantum gates defined by the provided state parameters. The quantum circuit generated can be used for further quantum computations or measurements.

        @param qubits The qubits on which the quantum state is to be prepared.
        @param data A map of state parameters (complex) used for state preparation.

        @return The quantum circuit that prepares the desired quantum state.


        3. ds_quantum_state_preparation(self: core.Encode, qubits: list[int], data: list[float]) -> None


        @brief Prepares a quantum state based on provided parameters.

        @details This function prepares a quantum state on the given qubits by applying quantum gates defined by the provided state parameters. The quantum circuit generated can be used for further quantum computations or measurements.

        @param qubits The qubits on which the quantum state is to be prepared.
        @param data A map of state parameters (list<double>) used for state preparation.

        @return The quantum circuit that prepares the desired quantum state.


        4. ds_quantum_state_preparation(self: core.Encode, qubits: list[int], data: list[complex]) -> None


        @brief Prepares a quantum state based on provided parameters.

        @details This function prepares a quantum state on the given qubits by applying quantum gates defined by the provided state parameters. The quantum circuit generated can be used for further quantum computations or measurements.

        @param qubits The qubits on which the quantum state is to be prepared.
        @param data A map of state parameters (list<complex>) used for state preparation.

        @return The quantum circuit that prepares the desired quantum state.

        """
    @overload
    def ds_quantum_state_preparation(self, qubits: list[int], data: dict[str, complex]) -> None:
        """ds_quantum_state_preparation(*args, **kwargs)
        Overloaded function.

        1. ds_quantum_state_preparation(self: core.Encode, qubits: list[int], data: dict[str, float]) -> None


        @brief Prepares a quantum state based on provided parameters.

        @details This function prepares a quantum state on the given qubits by applying quantum gates defined by the provided state parameters. The quantum circuit generated can be used for further quantum computations or measurements.

        @param qubits The qubits on which the quantum state is to be prepared.
        @param data A map of state parameters (double) used for state preparation.

        @return The quantum circuit that prepares the desired quantum state.


        2. ds_quantum_state_preparation(self: core.Encode, qubits: list[int], data: dict[str, complex]) -> None


        @brief Prepares a quantum state based on provided parameters.

        @details This function prepares a quantum state on the given qubits by applying quantum gates defined by the provided state parameters. The quantum circuit generated can be used for further quantum computations or measurements.

        @param qubits The qubits on which the quantum state is to be prepared.
        @param data A map of state parameters (complex) used for state preparation.

        @return The quantum circuit that prepares the desired quantum state.


        3. ds_quantum_state_preparation(self: core.Encode, qubits: list[int], data: list[float]) -> None


        @brief Prepares a quantum state based on provided parameters.

        @details This function prepares a quantum state on the given qubits by applying quantum gates defined by the provided state parameters. The quantum circuit generated can be used for further quantum computations or measurements.

        @param qubits The qubits on which the quantum state is to be prepared.
        @param data A map of state parameters (list<double>) used for state preparation.

        @return The quantum circuit that prepares the desired quantum state.


        4. ds_quantum_state_preparation(self: core.Encode, qubits: list[int], data: list[complex]) -> None


        @brief Prepares a quantum state based on provided parameters.

        @details This function prepares a quantum state on the given qubits by applying quantum gates defined by the provided state parameters. The quantum circuit generated can be used for further quantum computations or measurements.

        @param qubits The qubits on which the quantum state is to be prepared.
        @param data A map of state parameters (list<complex>) used for state preparation.

        @return The quantum circuit that prepares the desired quantum state.

        """
    @overload
    def ds_quantum_state_preparation(self, qubits: list[int], data: list[float]) -> None:
        """ds_quantum_state_preparation(*args, **kwargs)
        Overloaded function.

        1. ds_quantum_state_preparation(self: core.Encode, qubits: list[int], data: dict[str, float]) -> None


        @brief Prepares a quantum state based on provided parameters.

        @details This function prepares a quantum state on the given qubits by applying quantum gates defined by the provided state parameters. The quantum circuit generated can be used for further quantum computations or measurements.

        @param qubits The qubits on which the quantum state is to be prepared.
        @param data A map of state parameters (double) used for state preparation.

        @return The quantum circuit that prepares the desired quantum state.


        2. ds_quantum_state_preparation(self: core.Encode, qubits: list[int], data: dict[str, complex]) -> None


        @brief Prepares a quantum state based on provided parameters.

        @details This function prepares a quantum state on the given qubits by applying quantum gates defined by the provided state parameters. The quantum circuit generated can be used for further quantum computations or measurements.

        @param qubits The qubits on which the quantum state is to be prepared.
        @param data A map of state parameters (complex) used for state preparation.

        @return The quantum circuit that prepares the desired quantum state.


        3. ds_quantum_state_preparation(self: core.Encode, qubits: list[int], data: list[float]) -> None


        @brief Prepares a quantum state based on provided parameters.

        @details This function prepares a quantum state on the given qubits by applying quantum gates defined by the provided state parameters. The quantum circuit generated can be used for further quantum computations or measurements.

        @param qubits The qubits on which the quantum state is to be prepared.
        @param data A map of state parameters (list<double>) used for state preparation.

        @return The quantum circuit that prepares the desired quantum state.


        4. ds_quantum_state_preparation(self: core.Encode, qubits: list[int], data: list[complex]) -> None


        @brief Prepares a quantum state based on provided parameters.

        @details This function prepares a quantum state on the given qubits by applying quantum gates defined by the provided state parameters. The quantum circuit generated can be used for further quantum computations or measurements.

        @param qubits The qubits on which the quantum state is to be prepared.
        @param data A map of state parameters (list<complex>) used for state preparation.

        @return The quantum circuit that prepares the desired quantum state.

        """
    @overload
    def ds_quantum_state_preparation(self, qubits: list[int], data: list[complex]) -> None:
        """ds_quantum_state_preparation(*args, **kwargs)
        Overloaded function.

        1. ds_quantum_state_preparation(self: core.Encode, qubits: list[int], data: dict[str, float]) -> None


        @brief Prepares a quantum state based on provided parameters.

        @details This function prepares a quantum state on the given qubits by applying quantum gates defined by the provided state parameters. The quantum circuit generated can be used for further quantum computations or measurements.

        @param qubits The qubits on which the quantum state is to be prepared.
        @param data A map of state parameters (double) used for state preparation.

        @return The quantum circuit that prepares the desired quantum state.


        2. ds_quantum_state_preparation(self: core.Encode, qubits: list[int], data: dict[str, complex]) -> None


        @brief Prepares a quantum state based on provided parameters.

        @details This function prepares a quantum state on the given qubits by applying quantum gates defined by the provided state parameters. The quantum circuit generated can be used for further quantum computations or measurements.

        @param qubits The qubits on which the quantum state is to be prepared.
        @param data A map of state parameters (complex) used for state preparation.

        @return The quantum circuit that prepares the desired quantum state.


        3. ds_quantum_state_preparation(self: core.Encode, qubits: list[int], data: list[float]) -> None


        @brief Prepares a quantum state based on provided parameters.

        @details This function prepares a quantum state on the given qubits by applying quantum gates defined by the provided state parameters. The quantum circuit generated can be used for further quantum computations or measurements.

        @param qubits The qubits on which the quantum state is to be prepared.
        @param data A map of state parameters (list<double>) used for state preparation.

        @return The quantum circuit that prepares the desired quantum state.


        4. ds_quantum_state_preparation(self: core.Encode, qubits: list[int], data: list[complex]) -> None


        @brief Prepares a quantum state based on provided parameters.

        @details This function prepares a quantum state on the given qubits by applying quantum gates defined by the provided state parameters. The quantum circuit generated can be used for further quantum computations or measurements.

        @param qubits The qubits on which the quantum state is to be prepared.
        @param data A map of state parameters (list<complex>) used for state preparation.

        @return The quantum circuit that prepares the desired quantum state.

        """
    @overload
    def efficient_sparse(self, qubits: list[int], data: dict[str, float]) -> None:
        """efficient_sparse(*args, **kwargs)
        Overloaded function.

        1. efficient_sparse(self: core.Encode, qubits: list[int], data: dict[str, float]) -> None


        @brief Performs an efficient sparse operation on the given qubits.

        @details This function applies an efficient sparse operation to the specified qubits using the provided parameters. Sparse operations allow for reduced resource utilization by focusing on non-zero elements, optimizing the operation for quantum circuits with large state spaces.

        @param qubits The qubits on which the sparse operation is to be performed.
        @param data A map of parameters (double) defining the sparse operation.

        @return The quantum circuit implementing the efficient sparse operation.


        2. efficient_sparse(self: core.Encode, qubits: list[int], data: dict[str, complex]) -> None


        @brief Performs an efficient sparse operation on the given qubits.

        @details This function applies an efficient sparse operation to the specified qubits using the provided parameters. Sparse operations allow for reduced resource utilization by focusing on non-zero elements, optimizing the operation for quantum circuits with large state spaces.

        @param qubits The qubits on which the sparse operation is to be performed.
        @param data A map of parameters (complex) defining the sparse operation.

        @return The quantum circuit implementing the efficient sparse operation.


        3. efficient_sparse(self: core.Encode, qubit: list[int], data: list[float]) -> None


        @brief Performs an efficient sparse operation on the given qubits.

        @details This function applies an efficient sparse operation to the specified qubits using the provided parameters. Sparse operations allow for reduced resource utilization by focusing on non-zero elements, optimizing the operation for quantum circuits with large state spaces.

        @param qubits The qubits on which the sparse operation is to be performed.
        @param data A map of parameters (list<double>) defining the sparse operation.

        @return The quantum circuit implementing the efficient sparse operation.


        4. efficient_sparse(self: core.Encode, qubits: list[int], data: list[complex]) -> None


        @brief Performs an efficient sparse operation on the given qubits.

        @details This function applies an efficient sparse operation to the specified qubits using the provided parameters. Sparse operations allow for reduced resource utilization by focusing on non-zero elements, optimizing the operation for quantum circuits with large state spaces.

        @param qubits The qubits on which the sparse operation is to be performed.
        @param data A map of parameters (list<complex>) defining the sparse operation.

        @return The quantum circuit implementing the efficient sparse operation.

        """
    @overload
    def efficient_sparse(self, qubits: list[int], data: dict[str, complex]) -> None:
        """efficient_sparse(*args, **kwargs)
        Overloaded function.

        1. efficient_sparse(self: core.Encode, qubits: list[int], data: dict[str, float]) -> None


        @brief Performs an efficient sparse operation on the given qubits.

        @details This function applies an efficient sparse operation to the specified qubits using the provided parameters. Sparse operations allow for reduced resource utilization by focusing on non-zero elements, optimizing the operation for quantum circuits with large state spaces.

        @param qubits The qubits on which the sparse operation is to be performed.
        @param data A map of parameters (double) defining the sparse operation.

        @return The quantum circuit implementing the efficient sparse operation.


        2. efficient_sparse(self: core.Encode, qubits: list[int], data: dict[str, complex]) -> None


        @brief Performs an efficient sparse operation on the given qubits.

        @details This function applies an efficient sparse operation to the specified qubits using the provided parameters. Sparse operations allow for reduced resource utilization by focusing on non-zero elements, optimizing the operation for quantum circuits with large state spaces.

        @param qubits The qubits on which the sparse operation is to be performed.
        @param data A map of parameters (complex) defining the sparse operation.

        @return The quantum circuit implementing the efficient sparse operation.


        3. efficient_sparse(self: core.Encode, qubit: list[int], data: list[float]) -> None


        @brief Performs an efficient sparse operation on the given qubits.

        @details This function applies an efficient sparse operation to the specified qubits using the provided parameters. Sparse operations allow for reduced resource utilization by focusing on non-zero elements, optimizing the operation for quantum circuits with large state spaces.

        @param qubits The qubits on which the sparse operation is to be performed.
        @param data A map of parameters (list<double>) defining the sparse operation.

        @return The quantum circuit implementing the efficient sparse operation.


        4. efficient_sparse(self: core.Encode, qubits: list[int], data: list[complex]) -> None


        @brief Performs an efficient sparse operation on the given qubits.

        @details This function applies an efficient sparse operation to the specified qubits using the provided parameters. Sparse operations allow for reduced resource utilization by focusing on non-zero elements, optimizing the operation for quantum circuits with large state spaces.

        @param qubits The qubits on which the sparse operation is to be performed.
        @param data A map of parameters (list<complex>) defining the sparse operation.

        @return The quantum circuit implementing the efficient sparse operation.

        """
    @overload
    def efficient_sparse(self, qubit: list[int], data: list[float]) -> None:
        """efficient_sparse(*args, **kwargs)
        Overloaded function.

        1. efficient_sparse(self: core.Encode, qubits: list[int], data: dict[str, float]) -> None


        @brief Performs an efficient sparse operation on the given qubits.

        @details This function applies an efficient sparse operation to the specified qubits using the provided parameters. Sparse operations allow for reduced resource utilization by focusing on non-zero elements, optimizing the operation for quantum circuits with large state spaces.

        @param qubits The qubits on which the sparse operation is to be performed.
        @param data A map of parameters (double) defining the sparse operation.

        @return The quantum circuit implementing the efficient sparse operation.


        2. efficient_sparse(self: core.Encode, qubits: list[int], data: dict[str, complex]) -> None


        @brief Performs an efficient sparse operation on the given qubits.

        @details This function applies an efficient sparse operation to the specified qubits using the provided parameters. Sparse operations allow for reduced resource utilization by focusing on non-zero elements, optimizing the operation for quantum circuits with large state spaces.

        @param qubits The qubits on which the sparse operation is to be performed.
        @param data A map of parameters (complex) defining the sparse operation.

        @return The quantum circuit implementing the efficient sparse operation.


        3. efficient_sparse(self: core.Encode, qubit: list[int], data: list[float]) -> None


        @brief Performs an efficient sparse operation on the given qubits.

        @details This function applies an efficient sparse operation to the specified qubits using the provided parameters. Sparse operations allow for reduced resource utilization by focusing on non-zero elements, optimizing the operation for quantum circuits with large state spaces.

        @param qubits The qubits on which the sparse operation is to be performed.
        @param data A map of parameters (list<double>) defining the sparse operation.

        @return The quantum circuit implementing the efficient sparse operation.


        4. efficient_sparse(self: core.Encode, qubits: list[int], data: list[complex]) -> None


        @brief Performs an efficient sparse operation on the given qubits.

        @details This function applies an efficient sparse operation to the specified qubits using the provided parameters. Sparse operations allow for reduced resource utilization by focusing on non-zero elements, optimizing the operation for quantum circuits with large state spaces.

        @param qubits The qubits on which the sparse operation is to be performed.
        @param data A map of parameters (list<complex>) defining the sparse operation.

        @return The quantum circuit implementing the efficient sparse operation.

        """
    @overload
    def efficient_sparse(self, qubits: list[int], data: list[complex]) -> None:
        """efficient_sparse(*args, **kwargs)
        Overloaded function.

        1. efficient_sparse(self: core.Encode, qubits: list[int], data: dict[str, float]) -> None


        @brief Performs an efficient sparse operation on the given qubits.

        @details This function applies an efficient sparse operation to the specified qubits using the provided parameters. Sparse operations allow for reduced resource utilization by focusing on non-zero elements, optimizing the operation for quantum circuits with large state spaces.

        @param qubits The qubits on which the sparse operation is to be performed.
        @param data A map of parameters (double) defining the sparse operation.

        @return The quantum circuit implementing the efficient sparse operation.


        2. efficient_sparse(self: core.Encode, qubits: list[int], data: dict[str, complex]) -> None


        @brief Performs an efficient sparse operation on the given qubits.

        @details This function applies an efficient sparse operation to the specified qubits using the provided parameters. Sparse operations allow for reduced resource utilization by focusing on non-zero elements, optimizing the operation for quantum circuits with large state spaces.

        @param qubits The qubits on which the sparse operation is to be performed.
        @param data A map of parameters (complex) defining the sparse operation.

        @return The quantum circuit implementing the efficient sparse operation.


        3. efficient_sparse(self: core.Encode, qubit: list[int], data: list[float]) -> None


        @brief Performs an efficient sparse operation on the given qubits.

        @details This function applies an efficient sparse operation to the specified qubits using the provided parameters. Sparse operations allow for reduced resource utilization by focusing on non-zero elements, optimizing the operation for quantum circuits with large state spaces.

        @param qubits The qubits on which the sparse operation is to be performed.
        @param data A map of parameters (list<double>) defining the sparse operation.

        @return The quantum circuit implementing the efficient sparse operation.


        4. efficient_sparse(self: core.Encode, qubits: list[int], data: list[complex]) -> None


        @brief Performs an efficient sparse operation on the given qubits.

        @details This function applies an efficient sparse operation to the specified qubits using the provided parameters. Sparse operations allow for reduced resource utilization by focusing on non-zero elements, optimizing the operation for quantum circuits with large state spaces.

        @param qubits The qubits on which the sparse operation is to be performed.
        @param data A map of parameters (list<complex>) defining the sparse operation.

        @return The quantum circuit implementing the efficient sparse operation.

        """
    def get_circuit(self) -> QCircuit:
        """get_circuit(self: core.Encode) -> core.QCircuit


        @brief Retrieves the quantum circuit from the encoder.

        @details This function returns the quantum circuit that was generated by the encoding process. The returned circuit can then be used for further quantum operations or measurements.

        @return The corresponding quantum circuit object.

        """
    @overload
    def get_fidelity(self, data: list[float]) -> float:
        """get_fidelity(*args, **kwargs)
        Overloaded function.

        1. get_fidelity(self: core.Encode, data: list[float]) -> float


        @brief Calculates the fidelity based on the provided data.

        @details This function computes the fidelity of a quantum state based on the input data. Fidelity measures how close two quantum states are, and this function evaluates it based on the provided input data vector.

        @param data A vector of doubles representing the input data used for calculating fidelity.

        @return The calculated fidelity value, indicating the similarity between the quantum states.


        2. get_fidelity(self: core.Encode, data: list[complex]) -> float


        @brief Calculates the fidelity based on the provided data.

        @details This function computes the fidelity of a quantum state based on the input data. Fidelity measures how close two quantum states are, and this function evaluates it based on the provided input data vector.

        @param data A vector of complex representing the input data used for calculating fidelity.

        @return The calculated fidelity value, indicating the similarity between the quantum states.


        3. get_fidelity(self: core.Encode, data: list[float]) -> float


        @brief Calculates the fidelity based on the provided data.

        @details This function computes the fidelity of a quantum state based on the input data. Fidelity measures how close two quantum states are, and this function evaluates it based on the provided input data vector.

        @param data A vector of float representing the input data used for calculating fidelity.

        @return The calculated fidelity value, indicating the similarity between the quantum states.

        """
    @overload
    def get_fidelity(self, data: list[complex]) -> float:
        """get_fidelity(*args, **kwargs)
        Overloaded function.

        1. get_fidelity(self: core.Encode, data: list[float]) -> float


        @brief Calculates the fidelity based on the provided data.

        @details This function computes the fidelity of a quantum state based on the input data. Fidelity measures how close two quantum states are, and this function evaluates it based on the provided input data vector.

        @param data A vector of doubles representing the input data used for calculating fidelity.

        @return The calculated fidelity value, indicating the similarity between the quantum states.


        2. get_fidelity(self: core.Encode, data: list[complex]) -> float


        @brief Calculates the fidelity based on the provided data.

        @details This function computes the fidelity of a quantum state based on the input data. Fidelity measures how close two quantum states are, and this function evaluates it based on the provided input data vector.

        @param data A vector of complex representing the input data used for calculating fidelity.

        @return The calculated fidelity value, indicating the similarity between the quantum states.


        3. get_fidelity(self: core.Encode, data: list[float]) -> float


        @brief Calculates the fidelity based on the provided data.

        @details This function computes the fidelity of a quantum state based on the input data. Fidelity measures how close two quantum states are, and this function evaluates it based on the provided input data vector.

        @param data A vector of float representing the input data used for calculating fidelity.

        @return The calculated fidelity value, indicating the similarity between the quantum states.

        """
    @overload
    def get_fidelity(self, data: list[float]) -> float:
        """get_fidelity(*args, **kwargs)
        Overloaded function.

        1. get_fidelity(self: core.Encode, data: list[float]) -> float


        @brief Calculates the fidelity based on the provided data.

        @details This function computes the fidelity of a quantum state based on the input data. Fidelity measures how close two quantum states are, and this function evaluates it based on the provided input data vector.

        @param data A vector of doubles representing the input data used for calculating fidelity.

        @return The calculated fidelity value, indicating the similarity between the quantum states.


        2. get_fidelity(self: core.Encode, data: list[complex]) -> float


        @brief Calculates the fidelity based on the provided data.

        @details This function computes the fidelity of a quantum state based on the input data. Fidelity measures how close two quantum states are, and this function evaluates it based on the provided input data vector.

        @param data A vector of complex representing the input data used for calculating fidelity.

        @return The calculated fidelity value, indicating the similarity between the quantum states.


        3. get_fidelity(self: core.Encode, data: list[float]) -> float


        @brief Calculates the fidelity based on the provided data.

        @details This function computes the fidelity of a quantum state based on the input data. Fidelity measures how close two quantum states are, and this function evaluates it based on the provided input data vector.

        @param data A vector of float representing the input data used for calculating fidelity.

        @return The calculated fidelity value, indicating the similarity between the quantum states.

        """
    def get_out_qubits(self) -> list[int]:
        """get_out_qubits(self: core.Encode) -> list[int]


        @brief Retrieves the output qubits from the encoder.

        @details This function returns the qubits that represent the output of the encoding process. These output qubits can be used for further quantum computations or measurements.

        @return A vector of output qubits.

        """
    def iqp_encode(self, qubits: list[int], data: list[float], control_list: list[tuple[int, int]] = ..., bool_inverse: bool = ..., repeats: int = ...) -> None:
        """iqp_encode(self: core.Encode, qubits: list[int], data: list[float], control_list: list[tuple[int, int]] = [], bool_inverse: bool = False, repeats: int = 1) -> None


        @brief Encodes data into a quantum state using IQP (Instantaneous Quantum Polynomial) encoding.

        @details This function implements IQP encoding, which applies a series of parameterized diagonal quantum gates in the Hadamard basis. IQP circuits are known for their potential quantum advantage in certain computational tasks.

        @param qubits The qubits used for encoding.
        @param prob_vec The data values to be encoded.
        @param list The control list defining the qubit interactions.
        @param bool_inverse A boolean flag indicating whether to apply the inverse of the IQP encoding circuit.
        @param repeats The number of times the encoding circuit is repeated.

        @return The quantum circuit implementing the IQP encoding.

        """
    def schmidt_encode(self, qubits: list[int], data: list[float], cutoff: float = ...) -> None:
        """schmidt_encode(self: core.Encode, qubits: list[int], data: list[float], cutoff: float = 0) -> None


        @brief Encodes data into a quantum state using Schmidt decomposition.

        @details This function implements quantum state encoding based on the Schmidt decomposition method. It decomposes the target quantum state into a product of smaller subsystems, allowing for efficient encoding of high-dimensional quantum states. A cutoff parameter is used to control the truncation of small singular values.

        @param qubits The qubits used for encoding.
        @param data The amplitude vector representing the quantum state to be encoded.
        @param cutoff The threshold for truncating small singular values in the Schmidt decomposition.

        @return The quantum circuit implementing the Schmidt-based encoding.

        """
    @overload
    def sparse_isometry(self, qubits: list[int], data: dict[str, float]) -> None:
        """sparse_isometry(*args, **kwargs)
        Overloaded function.

        1. sparse_isometry(self: core.Encode, qubits: list[int], data: dict[str, float]) -> None


        @brief Performs a sparse isometry operation on the given qubits.

        @details This function applies a sparse isometry operation to the specified qubits using the provided parameters. Sparse isometries are useful for mapping quantum states while preserving inner product relations, often employed in quantum algorithms involving unitary transformations.

        @param qubits The qubits on which the isometry operation is to be performed.
        @param data A map of parameters (double) defining the isometry operation.

        @return The quantum circuit implementing the sparse isometry operation.


        2. sparse_isometry(self: core.Encode, qubits: list[int], data: dict[str, complex]) -> None


        @brief Performs a sparse isometry operation on the given qubits.

        @details This function applies a sparse isometry operation to the specified qubits using the provided parameters. Sparse isometries are useful for mapping quantum states while preserving inner product relations, often employed in quantum algorithms involving unitary transformations.

        @param qubits The qubits on which the isometry operation is to be performed.
        @param data A map of parameters (complex) defining the isometry operation.

        @return The quantum circuit implementing the sparse isometry operation.


        3. sparse_isometry(self: core.Encode, qubits: list[int], data: list[float]) -> None


        @brief Performs a sparse isometry operation on the given qubits.

        @details This function applies a sparse isometry operation to the specified qubits using the provided parameters. Sparse isometries are useful for mapping quantum states while preserving inner product relations, often employed in quantum algorithms involving unitary transformations.

        @param qubits The qubits on which the isometry operation is to be performed.
        @param data A map of parameters (list<double>) defining the isometry operation.

        @return The quantum circuit implementing the sparse isometry operation.


        4. sparse_isometry(self: core.Encode, qubits: list[int], data: list[complex]) -> None


        @brief Performs a sparse isometry operation on the given qubits.

        @details This function applies a sparse isometry operation to the specified qubits using the provided parameters. Sparse isometries are useful for mapping quantum states while preserving inner product relations, often employed in quantum algorithms involving unitary transformations.

        @param qubits The qubits on which the isometry operation is to be performed.
        @param data A map of parameters (list<complex>) defining the isometry operation.

        @return The quantum circuit implementing the sparse isometry operation.

        """
    @overload
    def sparse_isometry(self, qubits: list[int], data: dict[str, complex]) -> None:
        """sparse_isometry(*args, **kwargs)
        Overloaded function.

        1. sparse_isometry(self: core.Encode, qubits: list[int], data: dict[str, float]) -> None


        @brief Performs a sparse isometry operation on the given qubits.

        @details This function applies a sparse isometry operation to the specified qubits using the provided parameters. Sparse isometries are useful for mapping quantum states while preserving inner product relations, often employed in quantum algorithms involving unitary transformations.

        @param qubits The qubits on which the isometry operation is to be performed.
        @param data A map of parameters (double) defining the isometry operation.

        @return The quantum circuit implementing the sparse isometry operation.


        2. sparse_isometry(self: core.Encode, qubits: list[int], data: dict[str, complex]) -> None


        @brief Performs a sparse isometry operation on the given qubits.

        @details This function applies a sparse isometry operation to the specified qubits using the provided parameters. Sparse isometries are useful for mapping quantum states while preserving inner product relations, often employed in quantum algorithms involving unitary transformations.

        @param qubits The qubits on which the isometry operation is to be performed.
        @param data A map of parameters (complex) defining the isometry operation.

        @return The quantum circuit implementing the sparse isometry operation.


        3. sparse_isometry(self: core.Encode, qubits: list[int], data: list[float]) -> None


        @brief Performs a sparse isometry operation on the given qubits.

        @details This function applies a sparse isometry operation to the specified qubits using the provided parameters. Sparse isometries are useful for mapping quantum states while preserving inner product relations, often employed in quantum algorithms involving unitary transformations.

        @param qubits The qubits on which the isometry operation is to be performed.
        @param data A map of parameters (list<double>) defining the isometry operation.

        @return The quantum circuit implementing the sparse isometry operation.


        4. sparse_isometry(self: core.Encode, qubits: list[int], data: list[complex]) -> None


        @brief Performs a sparse isometry operation on the given qubits.

        @details This function applies a sparse isometry operation to the specified qubits using the provided parameters. Sparse isometries are useful for mapping quantum states while preserving inner product relations, often employed in quantum algorithms involving unitary transformations.

        @param qubits The qubits on which the isometry operation is to be performed.
        @param data A map of parameters (list<complex>) defining the isometry operation.

        @return The quantum circuit implementing the sparse isometry operation.

        """
    @overload
    def sparse_isometry(self, qubits: list[int], data: list[float]) -> None:
        """sparse_isometry(*args, **kwargs)
        Overloaded function.

        1. sparse_isometry(self: core.Encode, qubits: list[int], data: dict[str, float]) -> None


        @brief Performs a sparse isometry operation on the given qubits.

        @details This function applies a sparse isometry operation to the specified qubits using the provided parameters. Sparse isometries are useful for mapping quantum states while preserving inner product relations, often employed in quantum algorithms involving unitary transformations.

        @param qubits The qubits on which the isometry operation is to be performed.
        @param data A map of parameters (double) defining the isometry operation.

        @return The quantum circuit implementing the sparse isometry operation.


        2. sparse_isometry(self: core.Encode, qubits: list[int], data: dict[str, complex]) -> None


        @brief Performs a sparse isometry operation on the given qubits.

        @details This function applies a sparse isometry operation to the specified qubits using the provided parameters. Sparse isometries are useful for mapping quantum states while preserving inner product relations, often employed in quantum algorithms involving unitary transformations.

        @param qubits The qubits on which the isometry operation is to be performed.
        @param data A map of parameters (complex) defining the isometry operation.

        @return The quantum circuit implementing the sparse isometry operation.


        3. sparse_isometry(self: core.Encode, qubits: list[int], data: list[float]) -> None


        @brief Performs a sparse isometry operation on the given qubits.

        @details This function applies a sparse isometry operation to the specified qubits using the provided parameters. Sparse isometries are useful for mapping quantum states while preserving inner product relations, often employed in quantum algorithms involving unitary transformations.

        @param qubits The qubits on which the isometry operation is to be performed.
        @param data A map of parameters (list<double>) defining the isometry operation.

        @return The quantum circuit implementing the sparse isometry operation.


        4. sparse_isometry(self: core.Encode, qubits: list[int], data: list[complex]) -> None


        @brief Performs a sparse isometry operation on the given qubits.

        @details This function applies a sparse isometry operation to the specified qubits using the provided parameters. Sparse isometries are useful for mapping quantum states while preserving inner product relations, often employed in quantum algorithms involving unitary transformations.

        @param qubits The qubits on which the isometry operation is to be performed.
        @param data A map of parameters (list<complex>) defining the isometry operation.

        @return The quantum circuit implementing the sparse isometry operation.

        """
    @overload
    def sparse_isometry(self, qubits: list[int], data: list[complex]) -> None:
        """sparse_isometry(*args, **kwargs)
        Overloaded function.

        1. sparse_isometry(self: core.Encode, qubits: list[int], data: dict[str, float]) -> None


        @brief Performs a sparse isometry operation on the given qubits.

        @details This function applies a sparse isometry operation to the specified qubits using the provided parameters. Sparse isometries are useful for mapping quantum states while preserving inner product relations, often employed in quantum algorithms involving unitary transformations.

        @param qubits The qubits on which the isometry operation is to be performed.
        @param data A map of parameters (double) defining the isometry operation.

        @return The quantum circuit implementing the sparse isometry operation.


        2. sparse_isometry(self: core.Encode, qubits: list[int], data: dict[str, complex]) -> None


        @brief Performs a sparse isometry operation on the given qubits.

        @details This function applies a sparse isometry operation to the specified qubits using the provided parameters. Sparse isometries are useful for mapping quantum states while preserving inner product relations, often employed in quantum algorithms involving unitary transformations.

        @param qubits The qubits on which the isometry operation is to be performed.
        @param data A map of parameters (complex) defining the isometry operation.

        @return The quantum circuit implementing the sparse isometry operation.


        3. sparse_isometry(self: core.Encode, qubits: list[int], data: list[float]) -> None


        @brief Performs a sparse isometry operation on the given qubits.

        @details This function applies a sparse isometry operation to the specified qubits using the provided parameters. Sparse isometries are useful for mapping quantum states while preserving inner product relations, often employed in quantum algorithms involving unitary transformations.

        @param qubits The qubits on which the isometry operation is to be performed.
        @param data A map of parameters (list<double>) defining the isometry operation.

        @return The quantum circuit implementing the sparse isometry operation.


        4. sparse_isometry(self: core.Encode, qubits: list[int], data: list[complex]) -> None


        @brief Performs a sparse isometry operation on the given qubits.

        @details This function applies a sparse isometry operation to the specified qubits using the provided parameters. Sparse isometries are useful for mapping quantum states while preserving inner product relations, often employed in quantum algorithms involving unitary transformations.

        @param qubits The qubits on which the isometry operation is to be performed.
        @param data A map of parameters (list<complex>) defining the isometry operation.

        @return The quantum circuit implementing the sparse isometry operation.

        """

class GPUQVM:
    def __init__(self) -> None:
        """__init__(self: core.GPUQVM) -> None"""
    def result(self) -> QResult:
        """result(self: core.GPUQVM) -> core.QResult"""
    def run(self, prog: QProg, int: int, model: NoiseModel = ...) -> None:
        """run(self: core.GPUQVM, prog: core.QProg, int: int, model: core.NoiseModel = <core.NoiseModel object at 0x00000218DA6F1B70>) -> None"""

class GateType:
    __members__: ClassVar[dict] = ...  # read-only
    BARRIER: ClassVar[GateType] = ...
    CNOT: ClassVar[GateType] = ...
    CP: ClassVar[GateType] = ...
    CRX: ClassVar[GateType] = ...
    CRY: ClassVar[GateType] = ...
    CRZ: ClassVar[GateType] = ...
    CU: ClassVar[GateType] = ...
    CZ: ClassVar[GateType] = ...
    ECHO: ClassVar[GateType] = ...
    GATE_NOP: ClassVar[GateType] = ...
    GATE_UNDEFINED: ClassVar[GateType] = ...
    H: ClassVar[GateType] = ...
    I: ClassVar[GateType] = ...
    IDLE: ClassVar[GateType] = ...
    ISWAP: ClassVar[GateType] = ...
    ORACLE: ClassVar[GateType] = ...
    P: ClassVar[GateType] = ...
    RPHI: ClassVar[GateType] = ...
    RX: ClassVar[GateType] = ...
    RXX: ClassVar[GateType] = ...
    RY: ClassVar[GateType] = ...
    RYY: ClassVar[GateType] = ...
    RZ: ClassVar[GateType] = ...
    RZX: ClassVar[GateType] = ...
    RZZ: ClassVar[GateType] = ...
    S: ClassVar[GateType] = ...
    SQISWAP: ClassVar[GateType] = ...
    SWAP: ClassVar[GateType] = ...
    T: ClassVar[GateType] = ...
    TOFFOLI: ClassVar[GateType] = ...
    U1: ClassVar[GateType] = ...
    U2: ClassVar[GateType] = ...
    U3: ClassVar[GateType] = ...
    U4: ClassVar[GateType] = ...
    X: ClassVar[GateType] = ...
    X1: ClassVar[GateType] = ...
    Y: ClassVar[GateType] = ...
    Y1: ClassVar[GateType] = ...
    Z: ClassVar[GateType] = ...
    Z1: ClassVar[GateType] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, value: int) -> None:
        """__init__(self: core.GateType, value: int) -> None"""
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: core.GateType) -> int"""
    def __int__(self) -> int:
        """__int__(self: core.GateType) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str: ...
    @property
    def value(self) -> int: ...

class MeasureNode:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class NoiseModel:
    def __init__(self) -> None:
        """__init__(self: core.NoiseModel) -> None"""
    @overload
    def add_all_qubit_quantum_error(self, error, gate_type: GateType) -> None:
        """add_all_qubit_quantum_error(*args, **kwargs)
        Overloaded function.

        1. add_all_qubit_quantum_error(self: core.NoiseModel, error: QPanda3::QuantumError, gate_type: core.GateType) -> None


        @brief Add a quantum error for all qubits for a specific gate type.
        @param error The quantum error to add.
        @param gate_type The gate type where the error will apply.
        @return None
         

        2. add_all_qubit_quantum_error(self: core.NoiseModel, error: QPanda3::QuantumError, gate_types: list[core.GateType]) -> None


        @brief Add a quantum error for all qubits for multiple gate types.
        @param error The quantum error to add.
        @param gate_types A list of gate types where the error will apply.
        @return None
         
        """
    @overload
    def add_all_qubit_quantum_error(self, error, gate_types: list[GateType]) -> None:
        """add_all_qubit_quantum_error(*args, **kwargs)
        Overloaded function.

        1. add_all_qubit_quantum_error(self: core.NoiseModel, error: QPanda3::QuantumError, gate_type: core.GateType) -> None


        @brief Add a quantum error for all qubits for a specific gate type.
        @param error The quantum error to add.
        @param gate_type The gate type where the error will apply.
        @return None
         

        2. add_all_qubit_quantum_error(self: core.NoiseModel, error: QPanda3::QuantumError, gate_types: list[core.GateType]) -> None


        @brief Add a quantum error for all qubits for multiple gate types.
        @param error The quantum error to add.
        @param gate_types A list of gate types where the error will apply.
        @return None
         
        """
    def add_all_qubit_read_out_error(self, probs: list[list[float]]) -> None:
        """add_all_qubit_read_out_error(self: core.NoiseModel, probs: list[list[float]]) -> None


        @brief Add read-out error for all qubits.
        @param probs The probabilities of error outcomes.
        @return None
         
        """
    @overload
    def add_quantum_error(self, error, gate_type: GateType, qubits: list[int]) -> None:
        """add_quantum_error(*args, **kwargs)
        Overloaded function.

        1. add_quantum_error(self: core.NoiseModel, error: QPanda3::QuantumError, gate_type: core.GateType, qubits: list[int]) -> None


        @brief Add a quantum error for a specific gate and qubits.
        @param error The quantum error to add.
        @param gate_type The type of the gate where the error will apply.
        @param qubits A list of qubit indices where the error will apply.
        @return None
         

        2. add_quantum_error(self: core.NoiseModel, error: QPanda3::QuantumError, gate_types: list[core.GateType], qubits: list[int]) -> None


        @brief Add a quantum error for specific gates and qubits.
        @param error The quantum error to add.
        @param gate_types A list of gate types where the error will apply.
        @param qubits A list of qubit indices where the error will apply.
        @return None
         
        """
    @overload
    def add_quantum_error(self, error, gate_types: list[GateType], qubits: list[int]) -> None:
        """add_quantum_error(*args, **kwargs)
        Overloaded function.

        1. add_quantum_error(self: core.NoiseModel, error: QPanda3::QuantumError, gate_type: core.GateType, qubits: list[int]) -> None


        @brief Add a quantum error for a specific gate and qubits.
        @param error The quantum error to add.
        @param gate_type The type of the gate where the error will apply.
        @param qubits A list of qubit indices where the error will apply.
        @return None
         

        2. add_quantum_error(self: core.NoiseModel, error: QPanda3::QuantumError, gate_types: list[core.GateType], qubits: list[int]) -> None


        @brief Add a quantum error for specific gates and qubits.
        @param error The quantum error to add.
        @param gate_types A list of gate types where the error will apply.
        @param qubits A list of qubit indices where the error will apply.
        @return None
         
        """
    def add_read_out_error(self, probs: list[list[float]], qubit: int) -> None:
        """add_read_out_error(self: core.NoiseModel, probs: list[list[float]], qubit: int) -> None


        @brief Add read-out error for a specific qubit.
        @param probs The probabilities of error outcomes.
        @param qubit The index of the qubit.
        @return None
         
        """
    def is_enabled(self) -> bool:
        """is_enabled(self: core.NoiseModel) -> bool


        @brief Check if the noise model is enabled.
        @return True if the noise model is enabled, false otherwise.
         
        """

class NoiseOpType:
    __members__: ClassVar[dict] = ...  # read-only
    KARUS_MATRIICES: ClassVar[NoiseOpType] = ...
    NOISE: ClassVar[NoiseOpType] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, value: int) -> None:
        """__init__(self: core.NoiseOpType, value: int) -> None"""
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: core.NoiseOpType) -> int"""
    def __int__(self) -> int:
        """__int__(self: core.NoiseOpType) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str: ...
    @property
    def value(self) -> int: ...

class OpType:
    __members__: ClassVar[dict] = ...  # read-only
    Gate: ClassVar[OpType] = ...
    Measure: ClassVar[OpType] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, value: int) -> None:
        """__init__(self: core.OpType, value: int) -> None"""
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: core.OpType) -> int"""
    def __int__(self) -> int:
        """__int__(self: core.OpType) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str: ...
    @property
    def value(self) -> int: ...

class Operation:
    m_control_qubits: list[int]
    m_measure_cbits: list[int]
    m_operation_type: OpType
    m_target_qubits: list[int]
    def __init__(self) -> None:
        """__init__(self: core.Operation) -> None"""
    def is_controlled(self) -> bool:
        """is_controlled(self: core.Operation) -> bool"""

class PIC_TYPE:
    __members__: ClassVar[dict] = ...  # read-only
    LATEX: ClassVar[PIC_TYPE] = ...
    TEXT: ClassVar[PIC_TYPE] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, value: int) -> None:
        """__init__(self: core.PIC_TYPE, value: int) -> None"""
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: core.PIC_TYPE) -> int"""
    def __int__(self) -> int:
        """__int__(self: core.PIC_TYPE) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str: ...
    @property
    def value(self) -> int: ...

class PartialAmplitudeQVM:
    def __init__(self) -> None:
        """__init__(self: core.PartialAmplitudeQVM) -> None"""
    def get_state_vector(self, amplitudes: list[str]) -> list[complex]:
        """get_state_vector(self: core.PartialAmplitudeQVM, amplitudes: list[str]) -> list[complex]


        @brief Get the state vector of the quantum system after running the program.
        @return A vector representing the state of the quantum system.
         
        """
    def run(self, prog: QProg) -> None:
        """run(self: core.PartialAmplitudeQVM, prog: core.QProg) -> None


        @brief Run a quantum program using PartialAmplitudeQVM simulator.
        @return None
         
        """

class QCircuit:
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: core.QCircuit) -> None


        @brief Default constructor for QCircuit.
            

        2. __init__(self: core.QCircuit, qubits_num: int) -> None


        @brief Constructor for QCircuit with a specified number of qubits.
        @param qubits_num Number of qubits in the circuit.
            

        3. __init__(self: core.QCircuit, arg0: core.QCircuit) -> None


        @brief Copy constructor for QCircuit.
        @param circuit The QCircuit instance to copy.
            
        """
    @overload
    def __init__(self, qubits_num: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: core.QCircuit) -> None


        @brief Default constructor for QCircuit.
            

        2. __init__(self: core.QCircuit, qubits_num: int) -> None


        @brief Constructor for QCircuit with a specified number of qubits.
        @param qubits_num Number of qubits in the circuit.
            

        3. __init__(self: core.QCircuit, arg0: core.QCircuit) -> None


        @brief Copy constructor for QCircuit.
        @param circuit The QCircuit instance to copy.
            
        """
    @overload
    def __init__(self, arg0: QCircuit) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: core.QCircuit) -> None


        @brief Default constructor for QCircuit.
            

        2. __init__(self: core.QCircuit, qubits_num: int) -> None


        @brief Constructor for QCircuit with a specified number of qubits.
        @param qubits_num Number of qubits in the circuit.
            

        3. __init__(self: core.QCircuit, arg0: core.QCircuit) -> None


        @brief Copy constructor for QCircuit.
        @param circuit The QCircuit instance to copy.
            
        """
    @overload
    def append(self, gate: QGate) -> None:
        """append(*args, **kwargs)
        Overloaded function.

        1. append(self: core.QCircuit, gate: core.QGate) -> None


        @brief Append a gate to the circuit.
        @param The QGate to append.
            

        2. append(self: core.QCircuit, circuit: core.QCircuit) -> None


        @brief Append a circuit to the circuit.
        @param The QCircuit to append.
            
        """
    @overload
    def append(self, circuit: QCircuit) -> None:
        """append(*args, **kwargs)
        Overloaded function.

        1. append(self: core.QCircuit, gate: core.QGate) -> None


        @brief Append a gate to the circuit.
        @param The QGate to append.
            

        2. append(self: core.QCircuit, circuit: core.QCircuit) -> None


        @brief Append a circuit to the circuit.
        @param The QCircuit to append.
            
        """
    def clear(self) -> None:
        """clear(self: core.QCircuit) -> None


        @brief Clear all operations in the circuit.
            
        """
    def clear_control(self) -> None:
        """clear_control(self: core.QCircuit) -> None


        @brief Clear all control qubits from this circuit.
            
        """
    def control(self, qubits: list[int]) -> QCircuit:
        """control(self: core.QCircuit, qubits: list[int]) -> core.QCircuit


        @brief add control qubits in place.
        @param qubits A vector of control qubit indices.
        @return The current controlled circuit
            
        """
    def control_qubits(self) -> list[int]:
        """control_qubits(self: core.QCircuit) -> list[int]


        @brief Get the control qubit indices.
        @return A vector of control qubit indices.
            
        """
    def count_ops(self, only_q2: bool = ...) -> dict[str, int]:
        """count_ops(self: core.QCircuit, only_q2: bool = False) -> dict[str, int]


        @brief Count the operations in the circuit.
        @param only_q2 Boolean to consider only 2-qubit gates.
        @return A map of gate counts by name.
            
        """
    def dagger(self) -> QCircuit:
        """dagger(self: core.QCircuit) -> core.QCircuit


        @brief Get the dagger of the circuit.
        @return A new QCircuit instance representing the dagger.
            
        """
    def depth(self, only_q2: bool = ...) -> int:
        """depth(self: core.QCircuit, only_q2: bool = False) -> int


        @brief Get the depth of the circuit.
        @param only_q2 Boolean to consider only 2-qubit gates.
        @return The depth of the circuit.
            
        """
    def expand(self) -> QCircuit:
        """expand(self: core.QCircuit) -> core.QCircuit


        @brief Get the expand circuit .
        @return Theexpand circuit.
            
        """
    def gate_operations(self, only_q2: bool = ...) -> list[QGate]:
        """gate_operations(self: core.QCircuit, only_q2: bool = False) -> list[core.QGate]


        @brief Get all gate operations in the circuit.
        @param only_q2 Boolean to filter only 2-qubit gates.
        @return A vector of QGate instances.
            
        """
    def get_register_size(self) -> int:
        """get_register_size(self: core.QCircuit) -> int


        @brief Get the size of the register.
        @return The size of the register.
            
        """
    def matrix(self) -> numpy.ndarray[numpy.complex128[m, n]]:
        """matrix(self: core.QCircuit) -> numpy.ndarray[numpy.complex128[m, n]]


        @brief get matrix of circuit.
            
        """
    def name(self) -> str:
        """name(self: core.QCircuit) -> str


        @brief Get the name of the circuit.
        @return The name as a string.
            
        """
    def num_2q_gate(self) -> int:
        """num_2q_gate(self: core.QCircuit) -> int


        @brief Get the number of 2-qubit gates in the circuit.
        @return The count of 2-qubit gates.
            
        """
    @overload
    def operations(self) -> list[QGate | QCircuit]:
        """operations(self: core.QCircuit) -> list[Union[core.QGate, core.QCircuit]]


        @brief Get all operations in the circuit.
        @return A vector of operations (QGate or QCircuit).
            
        """
    @overload
    def operations(self, QGateorQCircuit) -> Any:
        """operations(self: core.QCircuit) -> list[Union[core.QGate, core.QCircuit]]


        @brief Get all operations in the circuit.
        @return A vector of operations (QGate or QCircuit).
            
        """
    def originir(self, precision: int = ...) -> str:
        """originir(self: core.QCircuit, precision: int = 8) -> str


                        @brief get originir str.
                        @param precision.
                        @return originir str.
            
        """
    def qubits(self) -> list[int]:
        """qubits(self: core.QCircuit) -> list[int]


        @brief Get the qubit indices used in the circuit.
        @return A vector of qubit indices.
            
        """
    @overload
    def remap(self, arg0: list[int]) -> QCircuit:
        """remap(*args, **kwargs)
        Overloaded function.

        1. remap(self: core.QCircuit, arg0: list[int]) -> core.QCircuit


                @brief remap qubits of this circuit.
                @return The remap circuit.

        2. remap(self: core.QCircuit, arg0: std::initializer_list<int>) -> core.QCircuit


                @brief remap qubits of this circuit.
                @return The remap circuit.
        """
    @overload
    def remap(self, arg0) -> QCircuit:
        """remap(*args, **kwargs)
        Overloaded function.

        1. remap(self: core.QCircuit, arg0: list[int]) -> core.QCircuit


                @brief remap qubits of this circuit.
                @return The remap circuit.

        2. remap(self: core.QCircuit, arg0: std::initializer_list<int>) -> core.QCircuit


                @brief remap qubits of this circuit.
                @return The remap circuit.
        """
    def set_name(self, name: str) -> None:
        """set_name(self: core.QCircuit, name: str) -> None


        @brief Set the name of the circuit.
        @param name The name to set.
            
        """
    def size(self) -> int:
        """size(self: core.QCircuit) -> int


        @brief Get the number of operations in the circuit.
        @return The number of operations.
            
        """
    def target_qubits(self) -> list[int]:
        """target_qubits(self: core.QCircuit) -> list[int]


        @brief Get the target qubit indices.
        @return A vector of target qubit indices.
            
        """
    @overload
    def __lshift__(self, arg0: QGate) -> QCircuit:
        """__lshift__(*args, **kwargs)
        Overloaded function.

        1. __lshift__(self: core.QCircuit, arg0: core.QGate) -> core.QCircuit

        Use << to append a node to the circuit.

        2. __lshift__(self: core.QCircuit, arg0: core.QCircuit) -> core.QCircuit

        Use << to append a node to the circuit.
        """
    @overload
    def __lshift__(self, arg0: QCircuit) -> QCircuit:
        """__lshift__(*args, **kwargs)
        Overloaded function.

        1. __lshift__(self: core.QCircuit, arg0: core.QGate) -> core.QCircuit

        Use << to append a node to the circuit.

        2. __lshift__(self: core.QCircuit, arg0: core.QCircuit) -> core.QCircuit

        Use << to append a node to the circuit.
        """

class QGate(Operation):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def clear_control(self) -> None:
        """clear_control(self: core.QGate) -> None


          @brief Clear all control qubits from this gate.
             
        """
    @overload
    def control(self, qubit: int) -> QGate:
        """control(*args, **kwargs)
        Overloaded function.

        1. control(self: core.QGate, qubit: int) -> core.QGate


          @brief Add a control qubit.
          @param qubit The control qubit index to add.
          @return Reference to this modified QGate.
             

        2. control(self: core.QGate, qubits: list[int]) -> core.QGate


          @brief Add control qubits.
          @param qubit The control qubit index to add.
          @return Reference to this modified QGate.
             
        """
    @overload
    def control(self, qubits: list[int]) -> QGate:
        """control(*args, **kwargs)
        Overloaded function.

        1. control(self: core.QGate, qubit: int) -> core.QGate


          @brief Add a control qubit.
          @param qubit The control qubit index to add.
          @return Reference to this modified QGate.
             

        2. control(self: core.QGate, qubits: list[int]) -> core.QGate


          @brief Add control qubits.
          @param qubit The control qubit index to add.
          @return Reference to this modified QGate.
             
        """
    def control_qubits(self) -> list[int]:
        """control_qubits(self: core.QGate) -> list[int]


          @brief Get the control qubits for this gate.
          @return A vector of control qubit indices.
             
        """
    def dagger(self) -> QGate:
        """dagger(self: core.QGate) -> core.QGate


          @brief Get the adjoint (dagger) of this gate.
          @return A new QGate instance representing the dagger.
             
        """
    def gate_type(self) -> GateType:
        """gate_type(self: core.QGate) -> core.GateType


          @brief Get the type of this gate.
          @return The GateType of this gate.
             
        """
    def is_dagger(self) -> bool:
        """is_dagger(self: core.QGate) -> bool


          @brief Check if this gate is a dagger.
          @return True if this gate is a dagger, false otherwise.
             
        """
    def matrix(self, expanded: bool = ...) -> numpy.ndarray[numpy.complex128[m, n]]:
        """matrix(self: core.QGate, expanded: bool = False) -> numpy.ndarray[numpy.complex128[m, n]]


          @brief Get the matrix representation of this gate.
          @param expanded Whether to return the expanded matrix.
          @return The matrix representation as a matrixXcd.
             
        """
    def name(self) -> str:
        """name(self: core.QGate) -> str


          @brief Get the name of this gate.
          @return The name as a string.
             
        """
    def parameters(self) -> list[float]:
        """parameters(self: core.QGate) -> list[float]


          @brief Get the parameters of this gate.
          @return A vector of parameters.
             
        """
    def power(self, k: float) -> QGate:
        """power(self: core.QGate, k: float) -> core.QGate


          @brief Get this gate raised to a power.
          @param k The exponent to raise this gate to.
          @return A new QGate instance representing the power.
             
        """
    def qubits(self) -> list[int]:
        """qubits(self: core.QGate) -> list[int]


          @brief Get the target qubits.
          @return A vector of target qubit indices.
             
        """
    def qubits_num(self) -> int:
        """qubits_num(self: core.QGate) -> int


          @brief Get the number of qubits that this gate acts on.
          @return Number of qubits.
             
        """
    def remap(self, arg0: list[int]) -> QGate:
        """remap(self: core.QGate, arg0: list[int]) -> core.QGate


                      @brief remap the qubits of this gate.
                      @return gate.
             
        """
    def set_parameters(self, params: list[float]) -> None:
        """set_parameters(self: core.QGate, params: list[float]) -> None


          @brief Set the parameters for this gate.
          @param params A vector of parameters to set.
             
        """
    def target_qubits(self) -> list[int]:
        """target_qubits(self: core.QGate) -> list[int]


          @brief Get the target qubits for this gate.
          @return A vector of target qubit indices.
             
        """

class QProg:
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: core.QProg) -> None


        @brief Default constructor for QProg.
            

        2. __init__(self: core.QProg, qubits_num: int) -> None


        @brief Constructor for QProg with a specified number of qubits.
        @param qubits_num Number of qubits in the program.
            

        3. __init__(self: core.QProg, arg0: core.QProg) -> None


        @brief Copy constructor for QProg.
        @param prog The QProg instance to copy.
            

        4. __init__(self: core.QProg, originir_src: str, is_file: bool = False) -> None


        @brief Constructor for QProg from a source string or file.
        @param originir_src The source string or file path.
        @param is_file Boolean indicating if the source is a file.
            

        5. __init__(self: core.QProg, node: core.QCircuit) -> None


        @brief Constructor for QProg from a QCircuit.
        @param node The QCircuit instance to append to the program.
            
        """
    @overload
    def __init__(self, qubits_num: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: core.QProg) -> None


        @brief Default constructor for QProg.
            

        2. __init__(self: core.QProg, qubits_num: int) -> None


        @brief Constructor for QProg with a specified number of qubits.
        @param qubits_num Number of qubits in the program.
            

        3. __init__(self: core.QProg, arg0: core.QProg) -> None


        @brief Copy constructor for QProg.
        @param prog The QProg instance to copy.
            

        4. __init__(self: core.QProg, originir_src: str, is_file: bool = False) -> None


        @brief Constructor for QProg from a source string or file.
        @param originir_src The source string or file path.
        @param is_file Boolean indicating if the source is a file.
            

        5. __init__(self: core.QProg, node: core.QCircuit) -> None


        @brief Constructor for QProg from a QCircuit.
        @param node The QCircuit instance to append to the program.
            
        """
    @overload
    def __init__(self, arg0: QProg) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: core.QProg) -> None


        @brief Default constructor for QProg.
            

        2. __init__(self: core.QProg, qubits_num: int) -> None


        @brief Constructor for QProg with a specified number of qubits.
        @param qubits_num Number of qubits in the program.
            

        3. __init__(self: core.QProg, arg0: core.QProg) -> None


        @brief Copy constructor for QProg.
        @param prog The QProg instance to copy.
            

        4. __init__(self: core.QProg, originir_src: str, is_file: bool = False) -> None


        @brief Constructor for QProg from a source string or file.
        @param originir_src The source string or file path.
        @param is_file Boolean indicating if the source is a file.
            

        5. __init__(self: core.QProg, node: core.QCircuit) -> None


        @brief Constructor for QProg from a QCircuit.
        @param node The QCircuit instance to append to the program.
            
        """
    @overload
    def __init__(self, originir_src: str, is_file: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: core.QProg) -> None


        @brief Default constructor for QProg.
            

        2. __init__(self: core.QProg, qubits_num: int) -> None


        @brief Constructor for QProg with a specified number of qubits.
        @param qubits_num Number of qubits in the program.
            

        3. __init__(self: core.QProg, arg0: core.QProg) -> None


        @brief Copy constructor for QProg.
        @param prog The QProg instance to copy.
            

        4. __init__(self: core.QProg, originir_src: str, is_file: bool = False) -> None


        @brief Constructor for QProg from a source string or file.
        @param originir_src The source string or file path.
        @param is_file Boolean indicating if the source is a file.
            

        5. __init__(self: core.QProg, node: core.QCircuit) -> None


        @brief Constructor for QProg from a QCircuit.
        @param node The QCircuit instance to append to the program.
            
        """
    @overload
    def __init__(self, node: QCircuit) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: core.QProg) -> None


        @brief Default constructor for QProg.
            

        2. __init__(self: core.QProg, qubits_num: int) -> None


        @brief Constructor for QProg with a specified number of qubits.
        @param qubits_num Number of qubits in the program.
            

        3. __init__(self: core.QProg, arg0: core.QProg) -> None


        @brief Copy constructor for QProg.
        @param prog The QProg instance to copy.
            

        4. __init__(self: core.QProg, originir_src: str, is_file: bool = False) -> None


        @brief Constructor for QProg from a source string or file.
        @param originir_src The source string or file path.
        @param is_file Boolean indicating if the source is a file.
            

        5. __init__(self: core.QProg, node: core.QCircuit) -> None


        @brief Constructor for QProg from a QCircuit.
        @param node The QCircuit instance to append to the program.
            
        """
    @overload
    def append(self, gate: QGate) -> None:
        """append(*args, **kwargs)
        Overloaded function.

        1. append(self: core.QProg, gate: core.QGate) -> None

        2. append(self: core.QProg, circuit: core.QCircuit) -> None

        3. append(self: core.QProg, prog: core.QProg) -> None

        4. append(self: core.QProg, measure: QPanda3::QMeasure) -> None

        5. append(self: core.QProg, arg0: list[core.QGate]) -> core.QProg

        Append QGate objects to the prog.

        6. append(self: core.QProg, arg0: list[core.QCircuit]) -> core.QProg

        Append QCircuit objects to the prog.

        7. append(self: core.QProg, arg0: list[core.QProg]) -> core.QProg

        Append QProg objects to the prog.

        8. append(self: core.QProg, arg0: list[QPanda3::QMeasure]) -> core.QProg

        Append QMeausre objects(MeasureNode s) to the prog.
        """
    @overload
    def append(self, circuit: QCircuit) -> None:
        """append(*args, **kwargs)
        Overloaded function.

        1. append(self: core.QProg, gate: core.QGate) -> None

        2. append(self: core.QProg, circuit: core.QCircuit) -> None

        3. append(self: core.QProg, prog: core.QProg) -> None

        4. append(self: core.QProg, measure: QPanda3::QMeasure) -> None

        5. append(self: core.QProg, arg0: list[core.QGate]) -> core.QProg

        Append QGate objects to the prog.

        6. append(self: core.QProg, arg0: list[core.QCircuit]) -> core.QProg

        Append QCircuit objects to the prog.

        7. append(self: core.QProg, arg0: list[core.QProg]) -> core.QProg

        Append QProg objects to the prog.

        8. append(self: core.QProg, arg0: list[QPanda3::QMeasure]) -> core.QProg

        Append QMeausre objects(MeasureNode s) to the prog.
        """
    @overload
    def append(self, prog: QProg) -> None:
        """append(*args, **kwargs)
        Overloaded function.

        1. append(self: core.QProg, gate: core.QGate) -> None

        2. append(self: core.QProg, circuit: core.QCircuit) -> None

        3. append(self: core.QProg, prog: core.QProg) -> None

        4. append(self: core.QProg, measure: QPanda3::QMeasure) -> None

        5. append(self: core.QProg, arg0: list[core.QGate]) -> core.QProg

        Append QGate objects to the prog.

        6. append(self: core.QProg, arg0: list[core.QCircuit]) -> core.QProg

        Append QCircuit objects to the prog.

        7. append(self: core.QProg, arg0: list[core.QProg]) -> core.QProg

        Append QProg objects to the prog.

        8. append(self: core.QProg, arg0: list[QPanda3::QMeasure]) -> core.QProg

        Append QMeausre objects(MeasureNode s) to the prog.
        """
    @overload
    def append(self, measure) -> None:
        """append(*args, **kwargs)
        Overloaded function.

        1. append(self: core.QProg, gate: core.QGate) -> None

        2. append(self: core.QProg, circuit: core.QCircuit) -> None

        3. append(self: core.QProg, prog: core.QProg) -> None

        4. append(self: core.QProg, measure: QPanda3::QMeasure) -> None

        5. append(self: core.QProg, arg0: list[core.QGate]) -> core.QProg

        Append QGate objects to the prog.

        6. append(self: core.QProg, arg0: list[core.QCircuit]) -> core.QProg

        Append QCircuit objects to the prog.

        7. append(self: core.QProg, arg0: list[core.QProg]) -> core.QProg

        Append QProg objects to the prog.

        8. append(self: core.QProg, arg0: list[QPanda3::QMeasure]) -> core.QProg

        Append QMeausre objects(MeasureNode s) to the prog.
        """
    @overload
    def append(self, arg0: list[QGate]) -> QProg:
        """append(*args, **kwargs)
        Overloaded function.

        1. append(self: core.QProg, gate: core.QGate) -> None

        2. append(self: core.QProg, circuit: core.QCircuit) -> None

        3. append(self: core.QProg, prog: core.QProg) -> None

        4. append(self: core.QProg, measure: QPanda3::QMeasure) -> None

        5. append(self: core.QProg, arg0: list[core.QGate]) -> core.QProg

        Append QGate objects to the prog.

        6. append(self: core.QProg, arg0: list[core.QCircuit]) -> core.QProg

        Append QCircuit objects to the prog.

        7. append(self: core.QProg, arg0: list[core.QProg]) -> core.QProg

        Append QProg objects to the prog.

        8. append(self: core.QProg, arg0: list[QPanda3::QMeasure]) -> core.QProg

        Append QMeausre objects(MeasureNode s) to the prog.
        """
    @overload
    def append(self, arg0: list[QCircuit]) -> QProg:
        """append(*args, **kwargs)
        Overloaded function.

        1. append(self: core.QProg, gate: core.QGate) -> None

        2. append(self: core.QProg, circuit: core.QCircuit) -> None

        3. append(self: core.QProg, prog: core.QProg) -> None

        4. append(self: core.QProg, measure: QPanda3::QMeasure) -> None

        5. append(self: core.QProg, arg0: list[core.QGate]) -> core.QProg

        Append QGate objects to the prog.

        6. append(self: core.QProg, arg0: list[core.QCircuit]) -> core.QProg

        Append QCircuit objects to the prog.

        7. append(self: core.QProg, arg0: list[core.QProg]) -> core.QProg

        Append QProg objects to the prog.

        8. append(self: core.QProg, arg0: list[QPanda3::QMeasure]) -> core.QProg

        Append QMeausre objects(MeasureNode s) to the prog.
        """
    @overload
    def append(self, arg0: list[QProg]) -> QProg:
        """append(*args, **kwargs)
        Overloaded function.

        1. append(self: core.QProg, gate: core.QGate) -> None

        2. append(self: core.QProg, circuit: core.QCircuit) -> None

        3. append(self: core.QProg, prog: core.QProg) -> None

        4. append(self: core.QProg, measure: QPanda3::QMeasure) -> None

        5. append(self: core.QProg, arg0: list[core.QGate]) -> core.QProg

        Append QGate objects to the prog.

        6. append(self: core.QProg, arg0: list[core.QCircuit]) -> core.QProg

        Append QCircuit objects to the prog.

        7. append(self: core.QProg, arg0: list[core.QProg]) -> core.QProg

        Append QProg objects to the prog.

        8. append(self: core.QProg, arg0: list[QPanda3::QMeasure]) -> core.QProg

        Append QMeausre objects(MeasureNode s) to the prog.
        """
    @overload
    def append(self, arg0) -> QProg:
        """append(*args, **kwargs)
        Overloaded function.

        1. append(self: core.QProg, gate: core.QGate) -> None

        2. append(self: core.QProg, circuit: core.QCircuit) -> None

        3. append(self: core.QProg, prog: core.QProg) -> None

        4. append(self: core.QProg, measure: QPanda3::QMeasure) -> None

        5. append(self: core.QProg, arg0: list[core.QGate]) -> core.QProg

        Append QGate objects to the prog.

        6. append(self: core.QProg, arg0: list[core.QCircuit]) -> core.QProg

        Append QCircuit objects to the prog.

        7. append(self: core.QProg, arg0: list[core.QProg]) -> core.QProg

        Append QProg objects to the prog.

        8. append(self: core.QProg, arg0: list[QPanda3::QMeasure]) -> core.QProg

        Append QMeausre objects(MeasureNode s) to the prog.
        """
    def cbits(self) -> list[int]:
        """cbits(self: core.QProg) -> list[int]


        @brief Get the classical bit indices used in the program.
        @return A vector of classical bit indices.
            
        """
    def cbits_num(self) -> int:
        """cbits_num(self: core.QProg) -> int


        @brief Get the number of classical bits used in the program.
        @return The number of classical bits.
            
        """
    def clear(self) -> None:
        """clear(self: core.QProg) -> None


        @brief Clear all operations in the program.
            
        """
    def count_ops(self, only_q2: bool = ...) -> dict[str, int]:
        """count_ops(self: core.QProg, only_q2: bool = False) -> dict[str, int]


        @brief Count the operations in the program.
        @param only_q2 Boolean to consider only 2-qubit gates.
        @return A map of operation counts by name.
            
        """
    def depth(self, only_q2: bool = ...) -> int:
        """depth(self: core.QProg, only_q2: bool = False) -> int


        @brief Get the depth of the program.
        @param only_q2 Boolean to consider only 2-qubit gates.
        @return The depth of the program.
            
        """
    def flatten(self) -> QProg:
        """flatten(self: core.QProg) -> core.QProg


        @brief Flatten the program into a linear representation.
        @return A new QProg instance representing the flattened program.
            
        """
    def gate_operations(self, only_q2: bool = ...) -> list[QGate]:
        """gate_operations(self: core.QProg, only_q2: bool = False) -> list[core.QGate]


        @brief Get all gate operations in the program.
        @param only_q2 Boolean to filter only 2-qubit gates.
        @return A vector of QGate instances.
            
        """
    def get_measure_nodes(self, *args, **kwargs):
        """get_measure_nodes(self: core.QProg) -> list[Union[core.QGate, core.QCircuit, QPanda3::Karus, QPanda3::QMeasure, core.QProg]]


        @brief Get all measurement nodes in the program.
        @return A vector of measurement nodes (QProgNode).
            
        """
    def name(self) -> str:
        """name(self: core.QProg) -> str


        @brief Get the name of the program.
        @return The name as a string.
            
        """
    def operations(self, QProgNode) -> Any:
        """operations(self: core.QProg) -> list[Union[core.QGate, core.QCircuit, QPanda3::Karus, QPanda3::QMeasure, core.QProg]]


        @brief Get all operations in the program.
        @return A vector of operations (QProgNode).
            
        """
    def originir(self, precision: int = ...) -> str:
        """originir(self: core.QProg, precision: int = 8) -> str


                        @brief get originir str.
                        @param precision.
                        @return originir str.
            
        """
    def qubits(self) -> list[int]:
        """qubits(self: core.QProg) -> list[int]


        @brief Get the qubit indices used in the program.
        @return A vector of qubit indices.
            
        """
    def qubits_num(self) -> int:
        """qubits_num(self: core.QProg) -> int


        @brief Get the number of qubits used in the program.
        @return The number of qubits.
            
        """
    @overload
    def remap(self, arg0: list[int], arg1: list[int]) -> QProg:
        """remap(*args, **kwargs)
        Overloaded function.

        1. remap(self: core.QProg, arg0: list[int], arg1: list[int]) -> core.QProg


                @brief remap qubits of this QProg.
                @return The remap QProg.

        2. remap(self: core.QProg, arg0: std::initializer_list<int>, arg1: std::initializer_list<int>) -> core.QProg


                @brief remap qubits of this QProg.
                @return The remap QProg.
        """
    @overload
    def remap(self, arg0, arg1) -> QProg:
        """remap(*args, **kwargs)
        Overloaded function.

        1. remap(self: core.QProg, arg0: list[int], arg1: list[int]) -> core.QProg


                @brief remap qubits of this QProg.
                @return The remap QProg.

        2. remap(self: core.QProg, arg0: std::initializer_list<int>, arg1: std::initializer_list<int>) -> core.QProg


                @brief remap qubits of this QProg.
                @return The remap QProg.
        """
    def to_circuit(self) -> QCircuit:
        """to_circuit(self: core.QProg) -> core.QCircuit


        @brief Convert the program to a QCircuit.
        @return A QCircuit instance representing the program.
            
        """
    def to_instruction(self, backend, offset: int = ..., is_scheduling: bool = ...) -> str:
        """to_instruction(self: core.QProg, backend: QPanda3::ChipBackend, offset: int = 1, is_scheduling: bool = False) -> str


        @brief Converts a quantum program into a JSON instruction string compatible with the specified backend.
        @param[in] backend The chip backend used to determine instruction formatting.
        @param[in] qubit offset.
        @param[in] use scheduling .
        @return A JSON-formatted instruction string.
        """
    @overload
    def __lshift__(self, arg0: QGate) -> QProg:
        """__lshift__(*args, **kwargs)
        Overloaded function.

        1. __lshift__(self: core.QProg, arg0: core.QGate) -> core.QProg

        Use << to append a node to the prog.

        2. __lshift__(self: core.QProg, arg0: core.QCircuit) -> core.QProg

        Use << to append a node to the prog.

        3. __lshift__(self: core.QProg, arg0: core.QProg) -> core.QProg

        Use << to append a node to the prog.

        4. __lshift__(self: core.QProg, arg0: QPanda3::QMeasure) -> core.QProg

        Use << to append a node to the prog.

        5. __lshift__(self: core.QProg, arg0: list[core.QGate]) -> core.QProg

        Use << to append QGate objects to the prog.

        6. __lshift__(self: core.QProg, arg0: list[core.QCircuit]) -> core.QProg

        Use << to append QCircuit objects to the prog.

        7. __lshift__(self: core.QProg, arg0: list[core.QProg]) -> core.QProg

        Use << to append QProg objects to the prog.

        8. __lshift__(self: core.QProg, arg0: list[QPanda3::QMeasure]) -> core.QProg

        Use << to append QMeausre objects(MeasureNode s) to the prog.
        """
    @overload
    def __lshift__(self, arg0: QCircuit) -> QProg:
        """__lshift__(*args, **kwargs)
        Overloaded function.

        1. __lshift__(self: core.QProg, arg0: core.QGate) -> core.QProg

        Use << to append a node to the prog.

        2. __lshift__(self: core.QProg, arg0: core.QCircuit) -> core.QProg

        Use << to append a node to the prog.

        3. __lshift__(self: core.QProg, arg0: core.QProg) -> core.QProg

        Use << to append a node to the prog.

        4. __lshift__(self: core.QProg, arg0: QPanda3::QMeasure) -> core.QProg

        Use << to append a node to the prog.

        5. __lshift__(self: core.QProg, arg0: list[core.QGate]) -> core.QProg

        Use << to append QGate objects to the prog.

        6. __lshift__(self: core.QProg, arg0: list[core.QCircuit]) -> core.QProg

        Use << to append QCircuit objects to the prog.

        7. __lshift__(self: core.QProg, arg0: list[core.QProg]) -> core.QProg

        Use << to append QProg objects to the prog.

        8. __lshift__(self: core.QProg, arg0: list[QPanda3::QMeasure]) -> core.QProg

        Use << to append QMeausre objects(MeasureNode s) to the prog.
        """
    @overload
    def __lshift__(self, arg0: QProg) -> QProg:
        """__lshift__(*args, **kwargs)
        Overloaded function.

        1. __lshift__(self: core.QProg, arg0: core.QGate) -> core.QProg

        Use << to append a node to the prog.

        2. __lshift__(self: core.QProg, arg0: core.QCircuit) -> core.QProg

        Use << to append a node to the prog.

        3. __lshift__(self: core.QProg, arg0: core.QProg) -> core.QProg

        Use << to append a node to the prog.

        4. __lshift__(self: core.QProg, arg0: QPanda3::QMeasure) -> core.QProg

        Use << to append a node to the prog.

        5. __lshift__(self: core.QProg, arg0: list[core.QGate]) -> core.QProg

        Use << to append QGate objects to the prog.

        6. __lshift__(self: core.QProg, arg0: list[core.QCircuit]) -> core.QProg

        Use << to append QCircuit objects to the prog.

        7. __lshift__(self: core.QProg, arg0: list[core.QProg]) -> core.QProg

        Use << to append QProg objects to the prog.

        8. __lshift__(self: core.QProg, arg0: list[QPanda3::QMeasure]) -> core.QProg

        Use << to append QMeausre objects(MeasureNode s) to the prog.
        """
    @overload
    def __lshift__(self, arg0) -> QProg:
        """__lshift__(*args, **kwargs)
        Overloaded function.

        1. __lshift__(self: core.QProg, arg0: core.QGate) -> core.QProg

        Use << to append a node to the prog.

        2. __lshift__(self: core.QProg, arg0: core.QCircuit) -> core.QProg

        Use << to append a node to the prog.

        3. __lshift__(self: core.QProg, arg0: core.QProg) -> core.QProg

        Use << to append a node to the prog.

        4. __lshift__(self: core.QProg, arg0: QPanda3::QMeasure) -> core.QProg

        Use << to append a node to the prog.

        5. __lshift__(self: core.QProg, arg0: list[core.QGate]) -> core.QProg

        Use << to append QGate objects to the prog.

        6. __lshift__(self: core.QProg, arg0: list[core.QCircuit]) -> core.QProg

        Use << to append QCircuit objects to the prog.

        7. __lshift__(self: core.QProg, arg0: list[core.QProg]) -> core.QProg

        Use << to append QProg objects to the prog.

        8. __lshift__(self: core.QProg, arg0: list[QPanda3::QMeasure]) -> core.QProg

        Use << to append QMeausre objects(MeasureNode s) to the prog.
        """
    @overload
    def __lshift__(self, arg0: list[QGate]) -> QProg:
        """__lshift__(*args, **kwargs)
        Overloaded function.

        1. __lshift__(self: core.QProg, arg0: core.QGate) -> core.QProg

        Use << to append a node to the prog.

        2. __lshift__(self: core.QProg, arg0: core.QCircuit) -> core.QProg

        Use << to append a node to the prog.

        3. __lshift__(self: core.QProg, arg0: core.QProg) -> core.QProg

        Use << to append a node to the prog.

        4. __lshift__(self: core.QProg, arg0: QPanda3::QMeasure) -> core.QProg

        Use << to append a node to the prog.

        5. __lshift__(self: core.QProg, arg0: list[core.QGate]) -> core.QProg

        Use << to append QGate objects to the prog.

        6. __lshift__(self: core.QProg, arg0: list[core.QCircuit]) -> core.QProg

        Use << to append QCircuit objects to the prog.

        7. __lshift__(self: core.QProg, arg0: list[core.QProg]) -> core.QProg

        Use << to append QProg objects to the prog.

        8. __lshift__(self: core.QProg, arg0: list[QPanda3::QMeasure]) -> core.QProg

        Use << to append QMeausre objects(MeasureNode s) to the prog.
        """
    @overload
    def __lshift__(self, arg0: list[QCircuit]) -> QProg:
        """__lshift__(*args, **kwargs)
        Overloaded function.

        1. __lshift__(self: core.QProg, arg0: core.QGate) -> core.QProg

        Use << to append a node to the prog.

        2. __lshift__(self: core.QProg, arg0: core.QCircuit) -> core.QProg

        Use << to append a node to the prog.

        3. __lshift__(self: core.QProg, arg0: core.QProg) -> core.QProg

        Use << to append a node to the prog.

        4. __lshift__(self: core.QProg, arg0: QPanda3::QMeasure) -> core.QProg

        Use << to append a node to the prog.

        5. __lshift__(self: core.QProg, arg0: list[core.QGate]) -> core.QProg

        Use << to append QGate objects to the prog.

        6. __lshift__(self: core.QProg, arg0: list[core.QCircuit]) -> core.QProg

        Use << to append QCircuit objects to the prog.

        7. __lshift__(self: core.QProg, arg0: list[core.QProg]) -> core.QProg

        Use << to append QProg objects to the prog.

        8. __lshift__(self: core.QProg, arg0: list[QPanda3::QMeasure]) -> core.QProg

        Use << to append QMeausre objects(MeasureNode s) to the prog.
        """
    @overload
    def __lshift__(self, arg0: list[QProg]) -> QProg:
        """__lshift__(*args, **kwargs)
        Overloaded function.

        1. __lshift__(self: core.QProg, arg0: core.QGate) -> core.QProg

        Use << to append a node to the prog.

        2. __lshift__(self: core.QProg, arg0: core.QCircuit) -> core.QProg

        Use << to append a node to the prog.

        3. __lshift__(self: core.QProg, arg0: core.QProg) -> core.QProg

        Use << to append a node to the prog.

        4. __lshift__(self: core.QProg, arg0: QPanda3::QMeasure) -> core.QProg

        Use << to append a node to the prog.

        5. __lshift__(self: core.QProg, arg0: list[core.QGate]) -> core.QProg

        Use << to append QGate objects to the prog.

        6. __lshift__(self: core.QProg, arg0: list[core.QCircuit]) -> core.QProg

        Use << to append QCircuit objects to the prog.

        7. __lshift__(self: core.QProg, arg0: list[core.QProg]) -> core.QProg

        Use << to append QProg objects to the prog.

        8. __lshift__(self: core.QProg, arg0: list[QPanda3::QMeasure]) -> core.QProg

        Use << to append QMeausre objects(MeasureNode s) to the prog.
        """
    @overload
    def __lshift__(self, arg0) -> QProg:
        """__lshift__(*args, **kwargs)
        Overloaded function.

        1. __lshift__(self: core.QProg, arg0: core.QGate) -> core.QProg

        Use << to append a node to the prog.

        2. __lshift__(self: core.QProg, arg0: core.QCircuit) -> core.QProg

        Use << to append a node to the prog.

        3. __lshift__(self: core.QProg, arg0: core.QProg) -> core.QProg

        Use << to append a node to the prog.

        4. __lshift__(self: core.QProg, arg0: QPanda3::QMeasure) -> core.QProg

        Use << to append a node to the prog.

        5. __lshift__(self: core.QProg, arg0: list[core.QGate]) -> core.QProg

        Use << to append QGate objects to the prog.

        6. __lshift__(self: core.QProg, arg0: list[core.QCircuit]) -> core.QProg

        Use << to append QCircuit objects to the prog.

        7. __lshift__(self: core.QProg, arg0: list[core.QProg]) -> core.QProg

        Use << to append QProg objects to the prog.

        8. __lshift__(self: core.QProg, arg0: list[QPanda3::QMeasure]) -> core.QProg

        Use << to append QMeausre objects(MeasureNode s) to the prog.
        """

class QResult:
    def __init__(self) -> None:
        """__init__(self: core.QResult) -> None"""
    def get_counts(self) -> dict[str, int]:
        """get_counts(self: core.QResult) -> dict[str, int]


        @brief Get the counts of measurement results.
        @return A dictionary of counts for each possible result.
         
        """
    def get_prob_dict(self, qubits: list[int] = ...) -> dict[str, float]:
        """get_prob_dict(self: core.QResult, qubits: list[int] = []) -> dict[str, float]


        @brief Get the dictionary of probabilities for specific qubits.
        @param qubits A list of qubit indices to get the probabilities for.

        @return A dictionary with qubit indices as keys and their probabilities as values.
         
        """
    def get_prob_list(self, qubits: list[int] = ...) -> list[float]:
        """get_prob_list(self: core.QResult, qubits: list[int] = []) -> list[float]


        @brief Get the list of probabilities for specific qubits.
        @param qubits A list of qubit indices to get the probabilities for.

        @return A list of probabilities.
         
        """
    def get_state_vector(self) -> list[complex]:
        """get_state_vector(self: core.QResult) -> list[complex]


        @brief Get the state vector of the quantum system.
        @return A vector representing the state of the quantum system.
         
        """
    def print_results(self) -> None:
        """print_results(self: core.QResult) -> None


        @brief Print the results of the quantum measurements.
        @return None
         
        """
    def shots(self) -> int:
        """shots(self: core.QResult) -> int


        @brief Get the number of shots for the measurement.
        @return The number of shots.
         
        """

class QuantumError:
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: core.QuantumError) -> None

        2. __init__(self: core.QuantumError, arg0: list[list[complex]]) -> None

        3. __init__(self: core.QuantumError, arg0: dict[str, float]) -> None
        """
    @overload
    def __init__(self, arg0: list[list[complex]]) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: core.QuantumError) -> None

        2. __init__(self: core.QuantumError, arg0: list[list[complex]]) -> None

        3. __init__(self: core.QuantumError, arg0: dict[str, float]) -> None
        """
    @overload
    def __init__(self, arg0: dict[str, float]) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: core.QuantumError) -> None

        2. __init__(self: core.QuantumError, arg0: list[list[complex]]) -> None

        3. __init__(self: core.QuantumError, arg0: dict[str, float]) -> None
        """
    def compose(self, arg0: QuantumError) -> QuantumError:
        """compose(self: core.QuantumError, arg0: core.QuantumError) -> core.QuantumError


        @brief Compose the current error with another error.
        @return A new QuantumError instance after composition.
         
        """
    def error_circuit(self, arg0: list[int]) -> QCircuit:
        """error_circuit(self: core.QuantumError, arg0: list[int]) -> core.QCircuit


        @brief Get the error circuit representation.
        @return A QuantumCircuit representing the error.
         
        """
    def error_karus(self, *args, **kwargs):
        """error_karus(self: core.QuantumError, arg0: list[int]) -> QPanda3::Karus


        @brief Get the Karus matrix representation of the error.
        @return A matrix representing the Karus error.
         
        """
    def error_type(self) -> NoiseOpType:
        """error_type(self: core.QuantumError) -> core.NoiseOpType


        @brief Get the type of the quantum error.
        @return The error type.
         
        """
    def expand(self, arg0: QuantumError) -> QuantumError:
        """expand(self: core.QuantumError, arg0: core.QuantumError) -> core.QuantumError


        @brief Expand the quantum error to a larger system.
        @return A new QuantumError instance after expansion.
         
        """
    def qubit_num(self) -> int:
        """qubit_num(self: core.QuantumError) -> int


        @brief Get the number of qubits affected by the error.
        @return The number of qubits.
         
        """
    def tensor(self, arg0: QuantumError) -> QuantumError:
        """tensor(self: core.QuantumError, arg0: core.QuantumError) -> core.QuantumError


        @brief Apply tensor operation to the error.
        @return A new QuantumError instance after applying tensor operation.
         
        """

class Qubit:
    def __init__(self, qubit: int) -> None:
        """__init__(self: core.Qubit, qubit: int) -> None

        Initialize a qubit with an address.
        """
    def get_qubit_addr(self) -> int:
        """get_qubit_addr(self: core.Qubit) -> int

        Get the address of the qubit.
        """
    def __int__(self) -> int:
        """__int__(self: core.Qubit) -> int

        Convert the qubit to its address as an integer.
        """

class Stabilizer:
    def __init__(self) -> None:
        """__init__(self: core.Stabilizer) -> None"""
    def result(self) -> StabilizerResult:
        """result(self: core.Stabilizer) -> core.StabilizerResult


        @brief Get the result after running the program.
        @return The result of the quantum simulation.
         
        """
    def run(self, prog: QProg, shots: int, model: NoiseModel = ...) -> None:
        """run(self: core.Stabilizer, prog: core.QProg, shots: int, model: core.NoiseModel = <core.NoiseModel object at 0x00000218DA5B25B0>) -> None


        @brief Run a quantum program using the Stabilizer simulator.
        @param prog The quantum program to be executed.
        @param shots The number of shots (repetitions) for measurement.
        @param model The noise model to apply (default is NoiseModel()).

        @return None
         
        """

class StabilizerResult(QResult):
    def __init__(self) -> None:
        """__init__(self: core.StabilizerResult) -> None"""
    def get_state_vector(self) -> list[complex]:
        """get_state_vector(self: core.StabilizerResult) -> list[complex]


        @brief Get the state vector of the stabilizer result.
        @return A vector representing the state of the quantum system.
         
        """

class VQGate:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

def BARRIER(qubits: list[int]) -> QGate:
    """BARRIER(qubits: list[int]) -> core.QGate


    Apply the BARRIER operation to input qubits.

    The BARRIER operation prevents any operations from being moved above this point in the circuit.

    Matrix representation:
 
    BARRIER does not have a matrix representation since it does not change the quantum state.
     
    """
def CNOT(qubit1: int, qubit2: int) -> QGate:
    """CNOT(qubit1: int, qubit2: int) -> core.QGate


    Apply the CNOT (controlled-NOT) gate to two qubits.

    Matrix representation:
 
    CNOT = \\begin{bmatrix} 1 & 0 & 0 & 0 \\\\ 0 & 1 & 0 & 0 \\\\ 0 & 0 & 0 & 1 \\\\ 0 & 0 & 1 & 0 \\end{bmatrix}
     
    """
def CP(control: int, target: int, theta: float) -> QGate:
    """CP(*args, **kwargs)
    Overloaded function.

    1. CP(control: int, target: int, theta: float) -> core.QGate


    Apply the CP gate to a qubit.
        
    Matrix representation:
    
    CP = \\begin{bmatrix} 1 & 0 & 0 & 0  \\\\ 0 & 1 & 0 & 0 \\\\ 0 & 0 & 1 & 0 \\\\ 0 & 0 & 0 & \\exp(i\\theta) \\end{bmatrix}
            

    2. CP(control_qbit_idx: int, target_qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the CP gate to a qubit with an angle
    @param control_qbit_idx the idx of qbit which will control the target_qbit_idx
    @param target_qbit_idx the idx of qbit which will be controled by the control_qbit_idx
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is CP
        
    """
def CR(control: int, target: int, theta: float) -> QGate:
    """CR(*args, **kwargs)
    Overloaded function.

    1. CR(control: int, target: int, theta: float) -> core.QGate


    CR is equivalently replaced with CP, Apply the CP gate to a qubit.
        
    Matrix representation:
    
    CR = \\begin{bmatrix} 1 & 0 & 0 & 0  \\\\ 0 & 1 & 0 & 0 \\\\ 0 & 0 & 1 & 0 \\\\ 0 & 0 & 0 & \\exp(i\\theta) \\end{bmatrix}
            

    2. CR(control_qbit_idx: int, target_qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the CR gate to a qubit with an angle.
    @details This gate is same with CP gate. Here, the gate type of it will be same with CP gate.
    @param control_qbit_idx the idx of qbit which will control the target_qbit_idx
    @param target_qbit_idx the idx of qbit which will be controled by the control_qbit_idx
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is CR
        
    """
@overload
def CRX(control: int, target: int, theta: float) -> QGate:
    """CRX(*args, **kwargs)
    Overloaded function.

    1. CRX(control: int, target: int, theta: float) -> core.QGate


    Apply the CRX gate to a qubit.
        
    
            

    2. CRX(control_qbit_idx: int, target_qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the CRX gate to a qubit with an angle
    @param control_qbit_idx the idx of qbit which will control the target_qbit_idx
    @param target_qbit_idx the idx of qbit which will be controled by the control_qbit_idx
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is CRX
        
    """
@overload
def CRX(control_qbit_idx: int, target_qbit_idx: int, param) -> VQGate:
    """CRX(*args, **kwargs)
    Overloaded function.

    1. CRX(control: int, target: int, theta: float) -> core.QGate


    Apply the CRX gate to a qubit.
        
    
            

    2. CRX(control_qbit_idx: int, target_qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the CRX gate to a qubit with an angle
    @param control_qbit_idx the idx of qbit which will control the target_qbit_idx
    @param target_qbit_idx the idx of qbit which will be controled by the control_qbit_idx
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is CRX
        
    """
@overload
def CRY(control: int, target: int, theta: float) -> QGate:
    """CRY(*args, **kwargs)
    Overloaded function.

    1. CRY(control: int, target: int, theta: float) -> core.QGate


    Apply the CRY gate to a qubit.
        
            

    2. CRY(control_qbit_idx: int, target_qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the CRY gate to a qubit with an angle
    @param control_qbit_idx the idx of qbit which will control the target_qbit_idx
    @param target_qbit_idx the idx of qbit which will be controled by the control_qbit_idx
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is CRY
        
    """
@overload
def CRY(control_qbit_idx: int, target_qbit_idx: int, param) -> VQGate:
    """CRY(*args, **kwargs)
    Overloaded function.

    1. CRY(control: int, target: int, theta: float) -> core.QGate


    Apply the CRY gate to a qubit.
        
            

    2. CRY(control_qbit_idx: int, target_qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the CRY gate to a qubit with an angle
    @param control_qbit_idx the idx of qbit which will control the target_qbit_idx
    @param target_qbit_idx the idx of qbit which will be controled by the control_qbit_idx
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is CRY
        
    """
@overload
def CRZ(control: int, target: int, theta: float) -> QGate:
    """CRZ(*args, **kwargs)
    Overloaded function.

    1. CRZ(control: int, target: int, theta: float) -> core.QGate


    Apply the CRZ gate to a qubit.
        
            

    2. CRZ(control_qbit_idx: int, target_qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the CRZ gate to a qubit with an angle
    @param control_qbit_idx the idx of qbit which will control the target_qbit_idx
    @param target_qbit_idx the idx of qbit which will be controled by the control_qbit_idx
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is CRZ
        
    """
@overload
def CRZ(control_qbit_idx: int, target_qbit_idx: int, param) -> VQGate:
    """CRZ(*args, **kwargs)
    Overloaded function.

    1. CRZ(control: int, target: int, theta: float) -> core.QGate


    Apply the CRZ gate to a qubit.
        
            

    2. CRZ(control_qbit_idx: int, target_qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the CRZ gate to a qubit with an angle
    @param control_qbit_idx the idx of qbit which will control the target_qbit_idx
    @param target_qbit_idx the idx of qbit which will be controled by the control_qbit_idx
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is CRZ
        
    """
def CU(control: int, target: int, theta: float, phi: float, _lambda: float, gamma: float) -> QGate:
    """CU(*args, **kwargs)
    Overloaded function.

    1. CU(control: int, target: int, theta: float, phi: float, lambda: float, gamma: float) -> core.QGate


    Apply the CU (controlled-U) gate to two qubits.

    Matrix representation:
 
    CU = \\begin{bmatrix} 1 & 0 & 0 & 0 \\\\ 0 & 1 & 0 & 0 \\\\ 0 & 0 & u_0 & u_1 \\\\ 0 & 0 & u_2 & u_3 \\end{bmatrix}
     

    2. CU(control_qbit_idx: int, target_qbit_idx: int, param1: QPanda3::VQCParamSystem::ParamExpression, param2: Union[float, QPanda3::VQCParamSystem::ParamExpression], param3: Union[float, QPanda3::VQCParamSystem::ParamExpression], param4: Union[float, QPanda3::VQCParamSystem::ParamExpression]) -> core.VQGate


    @brief Apply the CU gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param1 the mutable param's pos in Parameter which will be used to update the val of the angle
    @param param2 the fixed param val or mutable param's pos in Parameter which will be used to ppdate the val of the angle
    @param param3 the fixed param val or mutable param's pos in Parameter which will be used to update the val of the angle
    @param param4 the fixed param val or mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is CU
        

    3. CU(control_qbit_idx: int, target_qbit_idx: int, param1: float, param2: QPanda3::VQCParamSystem::ParamExpression, param3: Union[float, QPanda3::VQCParamSystem::ParamExpression], param4: Union[float, QPanda3::VQCParamSystem::ParamExpression]) -> core.VQGate


    @brief Apply the CU gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param1 the fixed param's val
    @param param2 the mutable param's pos in Parameter which will be used to update the val of the angle
    @param param3 the fixed param val or mutable param's pos in Parameter which will be used to update the val of the angle
    @param param4 the fixed param val or mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is CU
        

    4. CU(control_qbit_idx: int, target_qbit_idx: int, param1: float, param2: float, param3: QPanda3::VQCParamSystem::ParamExpression, param4: Union[float, QPanda3::VQCParamSystem::ParamExpression]) -> core.VQGate


    @brief Apply the CU gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param1 the fixed param's val
    @param param2 the fixed param's val
    @param param3 the mutable param's pos in Parameter which will be used to update the val of the angle
    @param param4 the fixed param val or mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is CU
        

    5. CU(control_qbit_idx: int, target_qbit_idx: int, param1: float, param2: float, param3: float, param4: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the CU gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param1 the fixed param's val
    @param param2 the fixed param's val
    @param param3 the fixed param's val
    @param param4 the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is CU
        
    """
def CZ(qubit1: int, qubit2: int) -> QGate:
    """CZ(qubit1: int, qubit2: int) -> core.QGate


    Apply the CZ (controlled-Z) gate to two qubits.

    Matrix representation:
 
    CZ = \\begin{bmatrix} 1 & 0 & 0 & 0 \\\\ 0 & 1 & 0 & 0 \\\\ 0 & 0 & 1 & 0 \\\\ 0 & 0 & 0 & -1 \\end{bmatrix}
     
    """
def ECHO(qubit: int) -> QGate:
    """ECHO(qubit: int) -> core.QGate


    Apply the ECHO gate to qubit.
     
    """
def H(qubit: int) -> QGate:
    """H(qubit: int) -> core.QGate


    @brief Apply the Hadamard gate to a qubit.

    Matrix representation:
 
    H = \\begin{bmatrix} \\frac{1}{\\sqrt{2}} & \\frac{1}{\\sqrt{2}} \\\\ \\frac{1}{\\sqrt{2}} & -\\frac{1}{\\sqrt{2}} \\end{bmatrix}
     
    """
def I(qubit: int) -> QGate:
    """I(qubit: int) -> core.QGate


    Apply the identity gate to a qubit.

    Matrix representation:
 
    I = \\begin{bmatrix} 1 & 0 \\\\ 0 & 1 \\end{bmatrix}
     
    """
@overload
def IDLE(qubit: int, theta: float) -> QGate:
    """IDLE(*args, **kwargs)
    Overloaded function.

    1. IDLE(qubit: int, theta: float) -> core.QGate


    Apply the IDLE gate to a qubit.
            

    2. IDLE(qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the IDLE gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the IDLE gate
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is P
        
    """
@overload
def IDLE(qbit_idx: int, param) -> VQGate:
    """IDLE(*args, **kwargs)
    Overloaded function.

    1. IDLE(qubit: int, theta: float) -> core.QGate


    Apply the IDLE gate to a qubit.
            

    2. IDLE(qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the IDLE gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the IDLE gate
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is P
        
    """
def ISWAP(qubit1: int, qubit2: int) -> QGate:
    """ISWAP(qubit1: int, qubit2: int) -> core.QGate


    Apply the ISWAP gate to two qubits.

    Matrix representation:
 
    ISWAP = \\begin{bmatrix} 1 & 0 & 0 & 0 \\\\ 0 & \\cos(\\theta) & i\\sin(\\theta) & 0 \\\\ 0 & i\\sin(\\theta) & \\cos(\\theta) & 0 \\\\ 0 & 0 & 0 & 1 \\end{bmatrix}
     
    """
def Oracle(qubits: list[int], matrix: numpy.ndarray[numpy.complex128[m, n]]) -> QGate:
    """Oracle(qubits: list[int], matrix: numpy.ndarray[numpy.complex128[m, n]]) -> core.QGate

    Apply the Oracle gate to qubits.
    """
@overload
def P(qubit: int, theta: float) -> QGate:
    """P(*args, **kwargs)
    Overloaded function.

    1. P(qubit: int, theta: float) -> core.QGate


    Apply the P gate to a qubit.
            

    2. P(qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the P gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is P
        
    """
@overload
def P(qbit_idx: int, param) -> VQGate:
    """P(*args, **kwargs)
    Overloaded function.

    1. P(qubit: int, theta: float) -> core.QGate


    Apply the P gate to a qubit.
            

    2. P(qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the P gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is P
        
    """
def QV(num_qubit: int, depth: int, seed: int) -> QCircuit:
    """QV(num_qubit: int, depth: int, seed: int) -> core.QCircuit


    @brief Perform a quantum volume (QV) test.
    @param num_qubit The number of qubits for the quantum circuit.
    @param depth The depth (number of layers) of the quantum circuit.
    @param seed The random seed to use for the circuit generation.

    @return The computed quantum volume.
         
    """
def RPHI(control: int, theta: float, phi: float) -> QGate:
    """RPHI(control: int, theta: float, phi: float) -> core.QGate


    Apply the RPHI gate to a qubit.
     
    """
def RPhi(qbit_idx: int, param1, param2) -> VQGate:
    """RPhi(*args, **kwargs)
    Overloaded function.

    1. RPhi(qbit_idx: int, param1: QPanda3::VQCParamSystem::ParamExpression, param2: Union[float, QPanda3::VQCParamSystem::ParamExpression]) -> core.VQGate


    @brief Apply the RPhi gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle
    @param param2 the fixed param val or mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is RPhi
        

    2. RPhi(qbit_idx: int, param1: float, param2: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the RPhi gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param the fixed param's val
    @param param2 the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is RPhi
        
    """
def RX(qubit: int, theta: float) -> QGate:
    """RX(*args, **kwargs)
    Overloaded function.

    1. RX(qubit: int, theta: float) -> core.QGate


    Apply the RX rotation gate to a qubit.

    Matrix representation:
 
    RX = \\begin{bmatrix} \\cos\\left(\\frac{\\theta}{2}\\right) & -i\\sin\\left(\\frac{\\theta}{2}\\right) \\\\ -i\\sin\\left(\\frac{\\theta}{2}\\right) & \\cos\\left(\\frac{\\theta}{2}\\right) \\end{bmatrix}
     

    2. RX(qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the RX gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is RX
        
    """
def RXX(control: int, target: int, theta: float) -> QGate:
    """RXX(*args, **kwargs)
    Overloaded function.

    1. RXX(control: int, target: int, theta: float) -> core.QGate


    Apply the RXX gate to two qubits.

    Matrix representation:
 
    RXX = \\begin{bmatrix} \\cos(\\theta/2) & 0 & 0 & -i\\sin(\\theta/2) \\\\ 0 & \\cos(\\theta/2) & -i\\sin(\\theta/2) & 0 \\\\ 0 & -i\\sin(\\theta/2) & \\cos(\\theta/2) & 0 \\\\ -i\\sin(\\theta/2) & 0 & 0 & \\cos(\\theta/2) \\end{bmatrix}
     

    2. RXX(control_qbit_idx: int, target_qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the RXX gate to a qubit with an angle
    @param control_qbit_idx the idx of qbit which will control the target_qbit_idx
    @param target_qbit_idx the idx of qbit which will be controled by the control_qbit_idx
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is RXX
        
    """
def RY(qubit: int, theta: float) -> QGate:
    """RY(*args, **kwargs)
    Overloaded function.

    1. RY(qubit: int, theta: float) -> core.QGate


    Apply the RY rotation gate to a qubit.

    Matrix representation:
 
    RY = \\begin{bmatrix} \\cos\\left(\\frac{\\theta}{2}\\right) & -\\sin\\left(\\frac{\\theta}{2}\\right) \\\\ \\sin\\left(\\frac{\\theta}{2}\\right) & \\cos\\left(\\frac{\\theta}{2}\\right) \\end{bmatrix}
     

    2. RY(qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the RY gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is RY
        
    """
def RYY(control: int, target: int, theta: float) -> QGate:
    """RYY(*args, **kwargs)
    Overloaded function.

    1. RYY(control: int, target: int, theta: float) -> core.QGate


    Apply the RYY gate to two qubits.

    Matrix representation:
 
    RYY = \\begin{bmatrix} \\cos(\\theta/2) & 0 & 0 & i\\sin(\\theta/2) \\\\ 0 & \\cos(\\theta/2) & -i\\sin(\\theta/2) & 0 \\\\ 0 & -i\\sin(\\theta/2) & \\cos(\\theta/2) & 0 \\\\ i\\sin(\\theta/2) & 0 & 0 & \\cos(\\theta/2) \\end{bmatrix}
     

    2. RYY(control_qbit_idx: int, target_qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the RYY gate to a qubit with an angle
    @param control_qbit_idx the idx of qbit which will control the target_qbit_idx
    @param target_qbit_idx the idx of qbit which will be controled by the control_qbit_idx
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is RYY
        
    """
def RZ(qubit: int, theta: float) -> QGate:
    """RZ(*args, **kwargs)
    Overloaded function.

    1. RZ(qubit: int, theta: float) -> core.QGate


    Apply the RZ rotation gate to a qubit.

    Matrix representation:
 
    RZ = \\begin{bmatrix} \\exp\\left(-\\frac{i\\theta}{2}\\right) & 0 \\\\ 0 & \\exp\\left(\\frac{i\\theta}{2}\\right) \\end{bmatrix}
     

    2. RZ(qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the RZ gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is RZ
        
    """
def RZX(control: int, target: int, theta: float) -> QGate:
    """RZX(*args, **kwargs)
    Overloaded function.

    1. RZX(control: int, target: int, theta: float) -> core.QGate


    Apply the RZX gate to two qubits.

    Matrix representation:
 
    RZX = \\begin{bmatrix} \\cos(\\theta/2) & 0 & -i\\sin(\\theta/2) & 0 \\\\ 0 & \\cos(\\theta/2) & 0 & i\\sin(\\theta/2) \\\\ -i\\sin(\\theta/2) & 0 & \\cos(\\theta/2) & 0 \\\\ 0 & i\\sin(\\theta/2) & 0 & \\cos(\\theta/2) \\end{bmatrix}
     

    2. RZX(control_qbit_idx: int, target_qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the RZX gate to a qubit with an angle
    @param control_qbit_idx the idx of qbit which will control the target_qbit_idx
    @param target_qbit_idx the idx of qbit which will be controled by the control_qbit_idx
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is RZX
        
    """
def RZZ(control: int, target: int, theta: float) -> QGate:
    """RZZ(*args, **kwargs)
    Overloaded function.

    1. RZZ(control: int, target: int, theta: float) -> core.QGate


    Apply the RZZ gate to two qubits.

    Matrix representation:
 
    RZZ = \\begin{bmatrix} \\exp(-i\\theta/2) & 0 & 0 & 0 \\\\ 0 & \\exp(i\\theta/2) & 0 & 0 \\\\ 0 & 0 & \\exp(i\\theta/2) & 0 \\\\ 0 & 0 & 0 & \\exp(-i\\theta/2) \\end{bmatrix}
     

    2. RZZ(control_qbit_idx: int, target_qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the RZZ gate to a qubit with an angle
    @param control_qbit_idx the idx of qbit which will control the target_qbit_idx
    @param target_qbit_idx the idx of qbit which will be controled by the control_qbit_idx
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is RZZ
        
    """
def S(qubit: int) -> QGate:
    """S(qubit: int) -> core.QGate


    Apply the S gate to a qubit.

    Matrix representation:
 
    S = \\begin{bmatrix} 1 & 0 \\\\ 0 & i \\end{bmatrix}
     
    """
def SQISWAP(qubit1: int, qubit2: int) -> QGate:
    """SQISWAP(qubit1: int, qubit2: int) -> core.QGate


    Apply the SQISWAP gate to two qubits.
     
    """
def SWAP(qubit1: int, qubit2: int) -> QGate:
    """SWAP(qubit1: int, qubit2: int) -> core.QGate


    Apply the SWAP gate to two qubits.

    Matrix representation:
 
    SWAP = \\begin{bmatrix} 1 & 0 & 0 & 0 \\\\ 0 & 0 & 1 & 0 \\\\ 0 & 1 & 0 & 0 \\\\ 0 & 0 & 0 & 1 \\end{bmatrix}
     
    """
def T(qubit: int) -> QGate:
    """T(qubit: int) -> core.QGate


    Apply the T gate to a qubit.

    Matrix representation:
 
    T = \\begin{bmatrix} 1 & 0 \\\\ 0 & \\exp\\left(\\frac{i\\pi}{4}\\right) \\end{bmatrix}
     
    """
def TOFFOLI(qubit1: int, qubit2: int, qubit3: int) -> QGate:
    """TOFFOLI(qubit1: int, qubit2: int, qubit3: int) -> core.QGate


    Apply the TOFFOLI gate (controlled-controlled-NOT) to three qubits.

    Matrix representation:
 
    TOFFOLI = \\begin{bmatrix} 1 & 0 & 0 & 0 & 0 & 0 & 0 & 0 \\\\ 0 & 1 & 0 & 0 & 0 & 0 & 0 & 0 \\\\ 0 & 0 & 1 & 0 & 0 & 0 & 0 & 0 \\\\ 0 & 0 & 0 & 1 & 0 & 0 & 0 & 0 \\\\ 0 & 0 & 0 & 0 & 1 & 0 & 0 & 0 \\\\ 0 & 0 & 0 & 0 & 0 & 1 & 0 & 0 \\\\ 0 & 0 & 0 & 0 & 0 & 0 & 1 & 0 \\\\ 0 & 0 & 0 & 0 & 0 & 0 & 0 & 1 \\end{bmatrix}
     
    """
def U1(qubit: int, theta: float) -> QGate:
    """U1(*args, **kwargs)
    Overloaded function.

    1. U1(qubit: int, theta: float) -> core.QGate


    Apply the U1 gate to a qubit.

    Matrix representation:
 
    U1 = \\begin{bmatrix} 1 & 0 \\\\ 0 & \\exp(i\\theta) \\end{bmatrix}
     

    2. U1(qbit_idx: int, param: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the U1 gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is U1
        
    """
def U2(qubit: int, theta: float, phi: float) -> QGate:
    """U2(*args, **kwargs)
    Overloaded function.

    1. U2(qubit: int, theta: float, phi: float) -> core.QGate


    Apply the U2 gate to a qubit.

    Matrix representation:
 
    U2 = \\begin{bmatrix} \\frac{1}{\\sqrt{2}} & -\\frac{\\exp(i\\lambda)}{\\sqrt{2}} \\\\ \\frac{\\exp(i\\phi)}{\\sqrt{2}} & \\frac{\\exp(i\\lambda + i\\phi)}{\\sqrt{2}} \\end{bmatrix}
     

    2. U2(qbit_idx: int, param1: QPanda3::VQCParamSystem::ParamExpression, param2: Union[float, QPanda3::VQCParamSystem::ParamExpression]) -> core.VQGate


    @brief Apply the U2 gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param the mutable param's pos in Parameter which will be used to update the val of the angle
    @param param2 the fixed param val or mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is U2
        

    3. U2(qbit_idx: int, param1: float, param2: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the U2 gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param the fixed param's val
    @param param2 the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is U2
        
    """
def U3(qubit: int, theta: float, phi: float, _lambda: float) -> QGate:
    """U3(*args, **kwargs)
    Overloaded function.

    1. U3(qubit: int, theta: float, phi: float, lambda: float) -> core.QGate


    Apply the U3 gate to a qubit.

    Matrix representation:
 
    U3 = \\begin{bmatrix} \\cos\\left(\\frac{\\theta}{2}\\right) & -\\exp(i\\lambda)\\sin\\left(\\frac{\\theta}{2}\\right) \\\\ \\exp(i\\phi)\\sin\\left(\\frac{\\theta}{2}\\right) & \\exp(i\\lambda + i\\phi)\\cos\\left(\\frac{\\theta}{2}\\right) \\end{bmatrix}
     

    2. U3(qbit_idx: int, param1: QPanda3::VQCParamSystem::ParamExpression, param2: Union[float, QPanda3::VQCParamSystem::ParamExpression], param3: Union[float, QPanda3::VQCParamSystem::ParamExpression]) -> core.VQGate


    @brief Apply the U3 gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param1 the mutable param's pos in Parameter which will be used to update the val of the angle
    @param param2 the fixed param val or mutable param's pos in Parameter which will be used to update the val of the angle
    @param param3 the fixed param val or mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is U3
        

    3. U3(qbit_idx: int, param1: float, param2: QPanda3::VQCParamSystem::ParamExpression, param3: Union[float, QPanda3::VQCParamSystem::ParamExpression]) -> core.VQGate


    @brief Apply the U3 gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param1 the fixed param's val
    @param param2 the mutable param's pos in Parameter which will be used to update the val of the angle
    @param param3 the fixed param val or mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is U3
        

    4. U3(qbit_idx: int, param1: float, param2: float, param3: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the U3 gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param1 the fixed param's val
    @param param2 the fixed param's val
    @param param3 the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is U3
        
    """
def U4(qubit: int, theta: float, phi: float, _lambda: float, gamma: float) -> QGate:
    """U4(*args, **kwargs)
    Overloaded function.

    1. U4(qubit: int, theta: float, phi: float, lambda: float, gamma: float) -> core.QGate


    Apply the U4 gate to a qubit.

    Matrix representation:
 
    U4 = \\begin{bmatrix} u_0 & u_1 \\\\ u_2 & u_3 \\end{bmatrix}
     

    2. U4(qbit_idx: int, param1: QPanda3::VQCParamSystem::ParamExpression, param2: Union[float, QPanda3::VQCParamSystem::ParamExpression], param3: Union[float, QPanda3::VQCParamSystem::ParamExpression], param4: Union[float, QPanda3::VQCParamSystem::ParamExpression]) -> core.VQGate


    @brief Apply the U4 gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param1 the mutable param's pos in Parameter which will be used to update the val of the angle
    @param param2 the fixed param val or mutable param's pos in Parameter which will be used to update the val of the angle
    @param param3 the fixed param val or mutable param's pos in Parameter which will be used to update the val of the angle
    @param param4 the fixed param val or mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is U4
        

    3. U4(qbit_idx: int, param1: float, param2: QPanda3::VQCParamSystem::ParamExpression, param3: Union[float, QPanda3::VQCParamSystem::ParamExpression], param4: Union[float, QPanda3::VQCParamSystem::ParamExpression]) -> core.VQGate


    @brief Apply the U4 gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param1 the fixed param's val
    @param param2 the mutable param's pos in Parameter which will be used to update the val of the angle
    @param param3 the fixed param val or mutable param's pos in Parameter which will be used to update the val of the angle
    @param param4 the fixed param val or mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is U4
        

    4. U4(qbit_idx: int, param1: float, param2: float, param3: QPanda3::VQCParamSystem::ParamExpression, param4: Union[float, QPanda3::VQCParamSystem::ParamExpression]) -> core.VQGate


    @brief Apply the U4 gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param1 the fixed param's val
    @param param2 the fixed param's val
    @param param3 the mutable param's pos in Parameter which will be used to update the val of the angle
    @param param4 the fixed param val or mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is U4
        

    5. U4(qbit_idx: int, param1: float, param2: float, param3: float, param4: QPanda3::VQCParamSystem::ParamExpression) -> core.VQGate


    @brief Apply the U4 gate to a qubit with an angle
    @param qbit_idx the idx of qbit which will be appled the P gate
    @param param1 the fixed param's val
    @param param2 the fixed param's val
    @param param3 the fixed param's val
    @param param4 the mutable param's pos in Parameter which will be used to update the val of the angle

    @return return a VQGate which gate type is U4
        
    """
def X(qubit: int) -> QGate:
    """X(qubit: int) -> core.QGate


    Apply the X gate to a qubit.

    Matrix representation:
 
    X = \\begin{bmatrix} 0 & 1 \\\\ 1 & 0 \\end{bmatrix}
     
    """
def X1(qubit: int) -> QGate:
    """X1(qubit: int) -> core.QGate


    Apply the X1 gate to a qubit.

    Matrix representation:
 
    X1 = \\begin{bmatrix} \\frac{1}{\\sqrt{2}} & -\\frac{i}{\\sqrt{2}} \\\\ -\\frac{i}{\\sqrt{2}} & \\frac{1}{\\sqrt{2}} \\end{bmatrix}
     
    """
def Y(qubit: int) -> QGate:
    """Y(qubit: int) -> core.QGate


    Apply the Y gate to a qubit.

    Matrix representation:
 
    Y = \\begin{bmatrix} 0 & -i \\\\ i & 0 \\end{bmatrix}
     
    """
def Y1(qubit: int) -> QGate:
    """Y1(qubit: int) -> core.QGate


    Apply the Y1 gate to a qubit.

    Matrix representation:
 
    Y1 = \\begin{bmatrix} \\frac{1}{\\sqrt{2}} & -\\frac{1}{\\sqrt{2}} \\\\ \\frac{1}{\\sqrt{2}} & \\frac{1}{\\sqrt{2}} \\end{bmatrix}
     
    """
def Z(qubit: int) -> QGate:
    """Z(qubit: int) -> core.QGate


    Apply the Z gate to a qubit.

    Matrix representation:
 
    Z = \\begin{bmatrix} 1 & 0 \\\\ 0 & -1 \\end{bmatrix}
     
    """
def Z1(qubit: int) -> QGate:
    """Z1(qubit: int) -> core.QGate


    Apply the Z1 gate to a qubit.

    Matrix representation:
 
    Z1 = \\begin{bmatrix} \\exp\\left(-\\frac{i\\pi}{4}\\right) & 0 \\\\ 0 & \\exp\\left(\\frac{i\\pi}{4}\\right) \\end{bmatrix}
     
    """
def amplitude_damping_error(prob: float) -> QuantumError:
    """amplitude_damping_error(prob: float) -> core.QuantumError


    @brief Create an amplitude damping error.
    @return A QuantumError representing an amplitude damping error.
      
    """
def create_gate(gate_name: str, qubits: list[int], params: list[float]) -> QGate:
    """create_gate(gate_name: str, qubits: list[int], params: list[float]) -> core.QGate"""
def decoherence_error(arg0: float, arg1: float, arg2: float) -> QuantumError:
    """decoherence_error(arg0: float, arg1: float, arg2: float) -> core.QuantumError


    @brief Create a decoherence error.
    @return A QuantumError representing a decoherence error.
      
    """
def depolarizing_error(prob: float) -> QuantumError:
    """depolarizing_error(prob: float) -> core.QuantumError


    @brief Create a depolarizing error.
    @return A QuantumError representing a depolarizing error.
      
    """
def direct_twirl(arg0: QProg, arg1: str, arg2: int) -> QProg:
    """direct_twirl(arg0: core.QProg, arg1: str, arg2: int) -> core.QProg


    @brief Perform direct twirling on a quantum circuit.
    @param input_circ The input quantum circuit to twirl.
    @param twirled_gate The gate to use for the twirling operation (default is 'CNOT').
    @param seed The random seed to use for the twirling (default is 0).

    @return The twirled quantum circuit.
         
    """
@overload
def draw_qprog(qprog: QProg, p: PIC_TYPE = ..., expend_map: dict[str, int] = ..., param_show: bool = ..., with_logo: bool = ..., line_length: int = ..., output_file: str = ..., encode: str = ...) -> str:
    '''draw_qprog(*args, **kwargs)
    Overloaded function.

    1. draw_qprog(qprog: core.QProg, p: core.PIC_TYPE = <PIC_TYPE.TEXT: 0>, expend_map: dict[str, int] = {\'all\': 1}, param_show: bool = False, with_logo: bool = False, line_length: int = 100, output_file: str = \'\', encode: str = \'utf-8\') -> str


    @brief Draws a quantum program (QProg) graphically.
    This function generates a graphical representation of the given quantum program object.

    @param circuit A reference to the quantum program object of type QProg that needs to be drawn.
    @param p The drawing type, defaulting to PIC_TYPE::TEXT, which means to draw in text format.
    @param expend_map A map used to control drawing expansion options, defaulting to { {"all", 1} }.
                      This parameter can specify whether to expand all subprograms.
    @param param_show A boolean indicating whether to show parameters, defaulting to false.
    @param with_logo A boolean indicating whether to include a logo in the output, defaulting to false.
    @param line_length The maximum character length per line, defaulting to 100.
    @param output_file The path for the output file, defaulting to an empty string, which means do not write to a file.

    @return A string representing the generated graphical representation.
        

    2. draw_qprog(circuit: core.QCircuit, p: core.PIC_TYPE = <PIC_TYPE.TEXT: 0>, expend_map: dict[str, int] = {\'all\': 1}, param_show: bool = False, with_logo: bool = False, line_length: int = 100, output_file: str = \'\', encode: str = \'utf-8\') -> str


    @brief Draws a QCircuit graphically.
    This function generates a graphical representation of the given quantum program object.

    @param circuit A reference to the quantum program object of type QProg that needs to be drawn.
    @param p The drawing type, defaulting to PIC_TYPE::TEXT, which means to draw in text format.
    @param expend_map A map used to control drawing expansion options, defaulting to { {"all", 1} }.
                      This parameter can specify whether to expand all subprograms.
    @param param_show A boolean indicating whether to show parameters, defaulting to false.
    @param with_logo A boolean indicating whether to include a logo in the output, defaulting to false.
    @param line_length The maximum character length per line, defaulting to 100.
    @param output_file The path for the output file, defaulting to an empty string, which means do not write to a file.

    @return A string representing the generated graphical representation.
        
    '''
@overload
def draw_qprog(circuit: QCircuit, p: PIC_TYPE = ..., expend_map: dict[str, int] = ..., param_show: bool = ..., with_logo: bool = ..., line_length: int = ..., output_file: str = ..., encode: str = ...) -> str:
    '''draw_qprog(*args, **kwargs)
    Overloaded function.

    1. draw_qprog(qprog: core.QProg, p: core.PIC_TYPE = <PIC_TYPE.TEXT: 0>, expend_map: dict[str, int] = {\'all\': 1}, param_show: bool = False, with_logo: bool = False, line_length: int = 100, output_file: str = \'\', encode: str = \'utf-8\') -> str


    @brief Draws a quantum program (QProg) graphically.
    This function generates a graphical representation of the given quantum program object.

    @param circuit A reference to the quantum program object of type QProg that needs to be drawn.
    @param p The drawing type, defaulting to PIC_TYPE::TEXT, which means to draw in text format.
    @param expend_map A map used to control drawing expansion options, defaulting to { {"all", 1} }.
                      This parameter can specify whether to expand all subprograms.
    @param param_show A boolean indicating whether to show parameters, defaulting to false.
    @param with_logo A boolean indicating whether to include a logo in the output, defaulting to false.
    @param line_length The maximum character length per line, defaulting to 100.
    @param output_file The path for the output file, defaulting to an empty string, which means do not write to a file.

    @return A string representing the generated graphical representation.
        

    2. draw_qprog(circuit: core.QCircuit, p: core.PIC_TYPE = <PIC_TYPE.TEXT: 0>, expend_map: dict[str, int] = {\'all\': 1}, param_show: bool = False, with_logo: bool = False, line_length: int = 100, output_file: str = \'\', encode: str = \'utf-8\') -> str


    @brief Draws a QCircuit graphically.
    This function generates a graphical representation of the given quantum program object.

    @param circuit A reference to the quantum program object of type QProg that needs to be drawn.
    @param p The drawing type, defaulting to PIC_TYPE::TEXT, which means to draw in text format.
    @param expend_map A map used to control drawing expansion options, defaulting to { {"all", 1} }.
                      This parameter can specify whether to expand all subprograms.
    @param param_show A boolean indicating whether to show parameters, defaulting to false.
    @param with_logo A boolean indicating whether to include a logo in the output, defaulting to false.
    @param line_length The maximum character length per line, defaulting to 100.
    @param output_file The path for the output file, defaulting to an empty string, which means do not write to a file.

    @return A string representing the generated graphical representation.
        
    '''
def expval_hamiltonian(node: QProg, hamiltonian, shots: int = ..., model: NoiseModel = ..., used_threads: int = ..., backend: str = ...) -> float:
    '''expval_hamiltonian(node: core.QProg, hamiltonian: QPanda3::Hamiltonian, shots: int = 1, model: core.NoiseModel = <core.NoiseModel object at 0x00000218DA6E79B0>, used_threads: int = 4, backend: str = \'CPU\') -> float


    @brief Calculates the expectation value of a given Hamiltonian with respect to a quantum program.

    @details This function evaluates the expectation value of a Hamiltonian on a quantum state prepared by
    a quantum program (QProg). The calculation can be performed with optional noise modeling and
    parallelization.

    @param node The quantum program (QProg) that prepares the state for which the expectation value is calculated.
    @param hamiltonian The Hamiltonian operator for which the expectation value is to be computed.
    @param shots The number of measurements to perform. Default is 1.
    @param model The noise model to apply during the simulation. Default is an empty (ideal) NoiseModel.
    @param used_threads The number of threads to use for parallel computation. Default is 4.
    @param backend Specifies the backend for computation ("CPU" by default,but you can select "GPU").

    @return The expectation value of the Hamiltonian with respect to the state prepared by the quantum program.
        
    '''
def expval_pauli_operator(node: QProg, pauli_operator, shots: int = ..., model: NoiseModel = ..., used_threads: int = ..., backend: str = ...) -> float:
    '''expval_pauli_operator(node: core.QProg, pauli_operator: QPanda3::PauliOperator, shots: int = 1, model: core.NoiseModel = <core.NoiseModel object at 0x00000218DA6F36B0>, used_threads: int = 4, backend: str = \'CPU\') -> float


    @brief Calculates the expectation value of a given Pauli operator with respect to a quantum program.

    @details This function evaluates the expectation value of a Pauli operator on a quantum state prepared by
    a quantum program (QProg). The calculation can be performed with optional noise modeling and
    parallelization.

    @param node The quantum program (QProg) that prepares the state for which the expectation value is calculated.
    @param pauli_operator The Pauli operator for which the expectation value is to be computed.
    @param shots The number of measurements to perform. Default is 1.
    @param model The noise model to apply during the simulation. Default is an empty (ideal) NoiseModel.
    @param used_threads The number of threads to use for parallel computation. Default is 4.
    @param backend Specifies the backend for computation ("CPU" by default,but you can select "GPU").

    @return The expectation value of the Pauli operator with respect to the state prepared by the quantum program.
        
    '''
@overload
def measure(qubit: int, cbit: int) -> MeasureNode:
    """measure(*args, **kwargs)
    Overloaded function.

    1. measure(qubit: int, cbit: int) -> core.MeasureNode


    Create a measure node.
     

    2. measure(qubits: list[int], cbits: list[int]) -> list[core.MeasureNode]


    Create the measure nodes.
     
    """
@overload
def measure(qubits: list[int], cbits: list[int]) -> list[MeasureNode]:
    """measure(*args, **kwargs)
    Overloaded function.

    1. measure(qubit: int, cbit: int) -> core.MeasureNode


    Create a measure node.
     

    2. measure(qubits: list[int], cbits: list[int]) -> list[core.MeasureNode]


    Create the measure nodes.
     
    """
def pauli_x_error(prob: float) -> QuantumError:
    """pauli_x_error(prob: float) -> core.QuantumError


    @brief Create a Pauli-X error.
    @return A QuantumError representing a Pauli-X error.
      
    """
def pauli_y_error(prob: float) -> QuantumError:
    """pauli_y_error(prob: float) -> core.QuantumError


    @brief Create a Pauli-Y error.
    @return A QuantumError representing a Pauli-Y error.
      
    """
def pauli_z_error(prob: float) -> QuantumError:
    """pauli_z_error(prob: float) -> core.QuantumError


    @brief Create a Pauli-Z error.
    @return A QuantumError representing a Pauli-Z error.
      
    """
def phase_damping_error(prob: float) -> QuantumError:
    """phase_damping_error(prob: float) -> core.QuantumError


    @brief Create a phase damping error.
    @return A QuantumError representing a phase damping error.
      
    """
def random_qcircuit(qubits: list[int], depth: int, gate_type: list[str]) -> QCircuit:
    """random_qcircuit(qubits: list[int], depth: int, gate_type: list[str]) -> core.QCircuit


    @brief Generate a random quantum circuit.
    @param qubits The number of qubits in the circuit.
    @param depth The depth (number of layers) of the quantum circuit.
    @param gate_type The type of gates to use in the circuit.

    @return A random quantum circuit.
         
    """
def set_print_options(precision: int = ..., param_show: int = ..., linewidth: int = ...) -> None:
    """set_print_options(precision: int = 8, param_show: int = True, linewidth: int = 100) -> None

    Set the print options
    """
