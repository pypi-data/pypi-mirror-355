from pprint import pprint

import qiskit.quantum_info as qi
from qiskit import *
from qiskit.ignis.verification.tomography import (
    StateTomographyFitter,
    state_tomography_circuits,
)
from qiskit.visualization import (
    plot_bloch_multivector,
    plot_histogram,
    plot_state_city,
    plot_state_hinton,
    plot_state_paulivec,
    plot_state_qsphere,
)

from tergite.qiskit.providers import Tergite

#
# Note: This code has been used on "Quantum software" PoC hearing
# on January 25, 2022.
# Run with: python -i bell_state.py
#

# Backend ------------------------------------------------------

# Tergite
provider = Tergite.get_provider()
backend = provider.get_backend("pingu")

# Aer simulator
# backend = Aer.get_backend("aer_simulator")

# IBM
# account = IBMQ.load_account()
# backend= account.get_backend("ibmq_belem")


# Circuit ------------------------------------------------------
q = QuantumRegister(3)
circ = QuantumCircuit(q)
circ.h(q[0])
circ.cx(q[0], q[1])

print("Input circuit")
print(circ)

# State tomography circuits ------------------------------------
target_state = qi.Statevector.from_instruction(circ)
tomography_circuits = state_tomography_circuits(circ, [q[0], q[1], q[2]])

print("State tomography circuits")
print(tomography_circuits[0])
print("")
print(tomography_circuits[1])
print("")
print(tomography_circuits[2])


# Execute ------------------------------------------------------
job = execute(tomography_circuits, backend, shots=1000)

input("Executing job, press enter once it's finished")


# Fit  ---------------------------------------------------------
fitter = StateTomographyFitter(job.result(), tomography_circuits)
density_matrix = fitter.fit(method="lstsq")
traced_out = qi.partial_trace(density_matrix, [2])
plot_state_city(traced_out).show()

fidelity = qi.state_fidelity(density_matrix, target_state)
print("State Fidelity: F = {:.5f}".format(fidelity))
