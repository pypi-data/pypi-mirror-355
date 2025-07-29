// SPDX-FileCopyrightText: 2025 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use num::Integer;

use crate::{
    ir::qubit::LogicalQubit,
    prelude::{QuantumGate, U4Gate},
};

use super::{
    u2,
    x::{c2to4x, CXMode},
};

pub(crate) fn network(
    u2_gate: QuantumGate,
    control: &[LogicalQubit],
    aux_qubits: &[LogicalQubit],
    target: LogicalQubit,
    u4_gate: U4Gate,
    cx_mode: CXMode,
    approximated: bool,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    let n = control.len();
    let n_cx = match cx_mode {
        CXMode::C2X => 2,
        CXMode::C3X => 3,
    };

    if matches!(u2_gate, QuantumGate::PauliX) && n <= n_cx {
        return c2to4x::c1to4x(control, target, u4_gate, approximated);
    } else if n == 1 {
        return u2::cu2(u2_gate.matrix(), control[0], target, u4_gate);
    } else if n == 2 && matches!(cx_mode, CXMode::C3X) {
        return u4_gate
            .cnot(control[0], aux_qubits[0])
            .into_iter()
            .chain(u2::cu2(u2_gate.matrix(), aux_qubits[0], target, u4_gate))
            .chain(u4_gate.cnot(control[0], aux_qubits[0]))
            .collect();
    }

    let (num_groups, rem) = n.div_rem(&n_cx);

    let left_instructions = (0..num_groups).flat_map(|i| {
        c2to4x::c1to4x(
            &control[n_cx * i..n_cx * i + n_cx],
            aux_qubits[i],
            u4_gate,
            true,
        )
    });

    let new_ctrl = if rem != 0 {
        &control[control.len() - rem..]
            .iter()
            .cloned()
            .chain(aux_qubits[..num_groups].iter().cloned())
            .collect::<Vec<_>>()
    } else {
        &aux_qubits[..num_groups]
    };

    left_instructions
        .clone()
        .chain(network(
            u2_gate,
            new_ctrl,
            &aux_qubits[num_groups..],
            target,
            u4_gate,
            cx_mode,
            approximated,
        ))
        .chain(
            left_instructions
                .rev()
                .map(|(gate, target, control)| (gate.inverse(), target, control)),
        )
        .collect()
}
