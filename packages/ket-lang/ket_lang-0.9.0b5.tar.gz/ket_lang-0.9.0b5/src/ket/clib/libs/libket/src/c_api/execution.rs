// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
// SPDX-FileCopyrightText: 2024 2024 Otávio Augusto de Santana Jatobá <otavio.jatoba@grad.ufsc.br>
//
// SPDX-License-Identifier: Apache-2.0

use crate::{execution::*, ir::instructions::Instruction};

#[repr(C)]
#[derive(Debug, Clone)]
pub struct BatchCExecution {
    submit_execution: fn(*const u8, usize, *const f64, usize),
    get_results: fn(data: &mut *const u8, len: &mut usize),
    clear: fn(),
}

impl BatchExecution for BatchCExecution {
    fn submit_execution(&mut self, circuit: &[Instruction<usize>], parameters: &[f64]) {
        let circuit = serde_json::to_vec(circuit).unwrap();
        (self.submit_execution)(
            circuit.as_ptr(),
            circuit.len(),
            parameters.as_ptr(),
            parameters.len(),
        );
    }

    fn get_results(&mut self) -> ResultData {
        let mut buffer = std::ptr::null();
        let mut len: usize = 0;
        (self.get_results)(&mut buffer, &mut len);
        let buffer = unsafe { std::slice::from_raw_parts(buffer, len) };
        serde_json::from_slice(buffer).unwrap()
    }

    fn clear(&mut self) {
        (self.clear)();
    }
}

#[no_mangle]
/// # Safety
pub unsafe extern "C" fn ket_make_configuration(
    execution_target_json: *const u8,
    execution_target_size: usize,
    batch_execution: *const BatchCExecution,
    result: &mut *mut (ExecutionTarget, Option<QuantumExecution>),
) -> i32 {
    let execution: Option<QuantumExecution> = if batch_execution.is_null() {
        None
    } else {
        Some(QuantumExecution::Batch(Box::new(unsafe {
            (*batch_execution).clone()
        })))
    };

    let execution_target =
        unsafe { std::slice::from_raw_parts(execution_target_json, execution_target_size) };
    let execution_target = serde_json::from_slice(execution_target).unwrap();

    *result = Box::into_raw(Box::new((execution_target, execution)));

    0
}
