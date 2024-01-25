# Copyright (c) Microsoft Corporation.
# SPDX-License-Identifier: Apache-2.0

# DeepSpeed Team

import pytest
import os
import torch
from deepspeed.accelerator import get_accelerator

@pytest.mark.evaluation
@pytest.mark.parametrize("model_name", ["facebook/opt-6.7b"])
def test_human_eval(model_name):
    import mii
    import numpy
    from transformers import pipeline
    from human_eval.data import write_jsonl, read_problems
    from human_eval.evaluation import evaluate_functional_correctness

    def generate_base_completion(problem_prompt: str) -> str:
        return base_pipe(problem_prompt, do_sample=True)[0]["generated_text"]

    def generate_mii_completion(problem_prompt: str) -> str:
        return mii_pipe(problem_prompt, max_new_tokens=256)[0].generated_text

    def generate_samples(generation_function):
        samples = [
            dict(task_id=task_id, completion=generation_function(problems[task_id]["prompt"])) for task_id in problems
            for _ in range(num_samples_per_task)
        ]
        return samples

    # Initializing HuggingFace Pipeline
    local_rank = os.getenv("LOCAL_RANK", "0")
    device = torch.device(get_accelerator().device_name(local_rank))
    base_pipe = pipeline(model=model_name,
                         device=torch.device(get_accelerator().device_name(local_rank)),
                         max_length=256,
                         return_full_text=False)

    # Initializing DeepSpeed-MII Pipeline
    mii_pipe = mii.pipeline(model_name)

    # Loading Problems
    problems = read_problems("../../human-eval/data/HumanEvalTest.jsonl.gz")

    # Generating Base Samples
    num_samples_per_task = 1
    base_samples = generate_samples(generate_base_completion)

    # Generating MII Samples
    mii_samples = generate_samples(generate_mii_completion)

    # Writing Samples
    write_jsonl("base_samples.jsonl", base_samples)
    write_jsonl("mii_samples.jsonl", mii_samples)

    # Evaluating Samples
    # TODO: use code execution container
    base_results = evaluate_functional_correctness("base_samples.jsonl")
    mii_results = evaluate_functional_correctness("mii_samples.jsonl")

    # Executing Assertions
    for key in base_results.keys():
        assert numpy.allclose(base_results[key], mii_results[key], rtol=0.2), \
            f"Base result: {base_results[key]}, MII result: {mii_results[key]}, outside of rtol."

    # Teardown MII Pipeline
    mii_pipe.destroy()