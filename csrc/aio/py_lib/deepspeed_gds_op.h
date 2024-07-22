// Copyright (c) Microsoft Corporation.
// SPDX-License-Identifier: Apache-2.0

// DeepSpeed Team

#include <memory>
#include <queue>
#include <fstream>
#include <string>
#include <cstdlib>
#include <set>

#include "deepspeed_aio_op_desc.h"
#ifdef __ENABLE_GDS__
#include "deepspeed_gds_utils.h"
#endif

struct gds_op_desc_t : io_op_desc_t {
    #ifdef __ENABLE_GDS__
        CUfileDescr_t _cf_descr;
        CUfileHandle_t _cf_handle;
    #endif
    void* _base_ptr;

    gds_op_desc_t(const bool read_op,
                  const torch::Tensor& buffer,
                  const int fd,
                  const char* filename,
                  const long long int file_num_bytes,
                  const int num_threads,
                  const bool validate);

    void run(const int tid,
             std::unique_ptr<aio_context>& aio_ctxt,
             deepspeed_aio_config_t* aio_config);

    char* data_ptr() const;

    void validate();

    void fini();

    void _read_file(const int tid);

    void _write_file(const int tid);

    void _report_error(const ssize_t return_code, const int error_num, const off_t offset);
};

int register_buffer(const torch::Tensor& buffer);

int deregister_buffer(const torch::Tensor& buffer);

void init_gds_cufile(const int block_size, const int queue_depth, const int num_threads);

void close_gds();