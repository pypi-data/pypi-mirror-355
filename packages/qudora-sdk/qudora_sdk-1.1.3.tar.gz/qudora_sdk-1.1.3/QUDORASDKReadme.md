# QUDORA SDK

The QUDORA Software Development Kit (SDK) enables an interaction with quantum devices hosted on the [QUDORA Cloud](https://cloud.qudora.com) from Python code.

The included [Qiskit](https://www.ibm.com/quantum/qiskit)-provider allows direct execution of Qiskit-`QuantumCircuits` on the QUDORA Cloud quantum devices.

## Installation 

To install the latest version of the QUDORA SDK run 

```shell
pip install qudora-sdk
```

## Qiskit-Provider Usage

This section explains the usage of the included Qiskit-provider to access QUDORA Cloud quantum devices.
In order to use the provider an API-Token from the QUDORA Cloud is required. Such a token can be generated [here](https://cloud.qudora.com/main/api-tokens).

### Access to Quantum Devices

To authenticate with the QUDORA Cloud the provider requires the generated API-Token, which is here called `my-example-token`.

```python
from qudora_sdk.qiskit import QUDORAProvider

provider = QUDORAProvider(token="my-example-token")
```
If the authentication was successful, all available quantum devices can be listed.

```python
print(provider.backends())
```

Selecting a particular backend is done with the `get_backend()` function.

```python
backend = provider.get_backend('QVLS Simulator')
```

### Running Qiskit-QuantumCircuits

The quantum devices can execute `QuantumCircuit`-objects written with Qiskit. More information about writing circuits with qiskit can be found [here](https://docs.quantum.ibm.com/build).
Previously created Backend-objects have a `run()`-function to submit circuits to a selected backend.

```python
qc = QuantumCircuit(2,2)
qc.h(0)
qc.cx(0,1)

qc.measure(0,0)
qc.measure(1,1)

job = backend.run(qc, job_name='My example job')
```

The `job` object represents a job in the QUDORA Cloud. Its status can be retrieved by calling `job.status()`.
To obtain the result of a job, the `result()` function can be called. This function will wait until the job finishes and return the measurement results.

```python
result = job.result()
print(result)
```

Mid-circuit measurements and if statements based on [Qiskit's dynamic circuits](https://docs.quantum.ibm.com/guides/classical-feedforward-and-control-flow) are also supported. See below for a simple example:

```python
qc = QuantumCircuit(1,1)

qc.h(0)
qc.measure(0,0)
with qc.if_test((0, 1)):
    qc.x(0)
qc.measure(0,0)
```

### (!) Note about mid-circuit measurements
Mid-circuit measurements are supported, but there is a small caveat.
For our backends, measurements include an implicit reset. That means that the following two circuits are equivalent on our backends:
```python
qc.measure(0, 0)
```
and
```python
qc.measure(0, 0)
qc.reset(0)
```
In other words: qubits do not preserve their state after a measurement. This deviation from the standard rules of quantum mechanics is due to the nature of our trapped-ion qubits and how the measurement process is implemented. 
Should you need access to the post-measurement state, you can manually reset the qubit to the post-measurement state by using the dynamic circuit given in the example above. 

The support of qiskit dynamic circuits allows users to try out sophisticated error-correction schemes and analyse their performance against a realistic noise model.

### Customised Settings

A backend has parameters (mostly used for noise models), which you can modify to your needs.
You can list all available settings using the `show_available_settings()`-method.

```python
backend.show_available_settings()
```

To run a job with custom settings, you can pass a settings dictionary to the `run()` method.

```python
custom_settings = {
    'measurement_error_probability': 0.005,
    'two_qubit_gate_noise_strength': 1.0
}

job = backend.run(qc, job_name='Job with custom settings', backend_settings=custom_settings)
```

# LICENSE 

Copyright (C) 2025  QUDORA GmbH

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

