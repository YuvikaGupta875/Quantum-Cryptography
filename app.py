import streamlit as st
import random
import pandas as pd
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import matplotlib.pyplot as plt

# -----------------------------
# Helper functions
# -----------------------------

def generate_random_bits(length):
    return [random.randint(0, 1) for _ in range(length)]

def generate_random_bases(length):
    return [random.choice(['Z', 'X']) for _ in range(length)]

def encode_bits(bits, bases):
    qubits = []
    for bit, base in zip(bits, bases):
        qc = QuantumCircuit(1, 1)
        if bit == 1:
            qc.x(0)
        if base == 'X':
            qc.h(0)
        qubits.append(qc)
    return qubits

def measure_qubits(qubits, bases):
    simulator = AerSimulator()
    bits = []

    for qc, base in zip(qubits, bases):
        qc_copy = qc.copy()

        if base == 'X':
            qc_copy.h(0)

        qc_copy.measure(0, 0)
        compiled = transpile(qc_copy, simulator)
        result = simulator.run(compiled, shots=1).result()
        counts = result.get_counts()
        measured_bit = int(list(counts.keys())[0])
        bits.append(measured_bit)

    return bits

def eve_intercept(qubits):
    eve_bases = generate_random_bases(len(qubits))
    eve_bits = measure_qubits(qubits, eve_bases)
    new_qubits = encode_bits(eve_bits, eve_bases)
    return new_qubits, eve_bases

def sift_keys(alice_bits, bob_bits, alice_bases, bob_bases):
    alice_key = []
    bob_key = []

    for i in range(len(alice_bits)):
        if alice_bases[i] == bob_bases[i]:
            alice_key.append(alice_bits[i])
            bob_key.append(bob_bits[i])

    return alice_key, bob_key

def calculate_qber(alice_key, bob_key):
    if len(alice_key) == 0:
        return 0
    errors = sum(a != b for a, b in zip(alice_key, bob_key))
    return errors / len(alice_key)

# -----------------------------
# Streamlit UI
# -----------------------------

st.title("🔐 BB84 Quantum Key Distribution Demo")

st.markdown("Simulate BB84 protocol with optional eavesdropper (Eve).")

key_length = st.slider("Number of qubits", 10, 200, 50)
use_eve = st.checkbox("Enable Eve (Intercept-Resend Attack)")

if st.button("Run Simulation"):

    # Alice
    alice_bits = generate_random_bits(key_length)
    alice_bases = generate_random_bases(key_length)

    qubits = encode_bits(alice_bits, alice_bases)

    # Eve (optional)
    if use_eve:
        qubits, eve_bases = eve_intercept(qubits)
    else:
        eve_bases = ["-"] * key_length

    # Bob
    bob_bases = generate_random_bases(key_length)
    bob_bits = measure_qubits(qubits, bob_bases)

    # Sift keys
    alice_key, bob_key = sift_keys(
        alice_bits, bob_bits, alice_bases, bob_bases
    )

    qber = calculate_qber(alice_key, bob_key)

    # -----------------------------
    # Display results
    # -----------------------------

    st.subheader("🔑 Keys")
    st.write("Alice Key:", alice_key)
    st.write("Bob Key:  ", bob_key)
    st.write("Keys Match:", alice_key == bob_key)

    st.subheader("📊 QBER (Error Rate)")
    st.write(f"QBER: {qber:.2f}")

    # Table
    st.subheader("📋 Detailed Table")

    df = pd.DataFrame({
        "Alice Bit": alice_bits,
        "Alice Basis": alice_bases,
        "Eve Basis": eve_bases,
        "Bob Basis": bob_bases,
        "Bob Bit": bob_bits,
        "Match": [a == b for a, b in zip(alice_bases, bob_bases)]
    })

    st.dataframe(df)

    # Histogram
    st.subheader("📈 Bob's Sifted Key Distribution")

    if len(bob_key) > 0:
        fig, ax = plt.subplots()
        values = [bob_key.count(0), bob_key.count(1)]
        ax.bar(['0', '1'], values)
        ax.set_xlabel("Bit Value")
        ax.set_ylabel("Frequency")
        st.pyplot(fig)
    else:
        st.write("No matching bases → no key generated.")
