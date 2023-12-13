# SageMaker Pipelines

This folder contains SageMaker Pipeline definitions and helper scripts to either simply "get" a SageMaker Pipeline definition (JSON dictionnary) with `get_pipeline_definition.py`, or "run" a SageMaker Pipeline from a SageMaker pipeline definition with `run_pipeline.py`.

Those files are generic and can be reused to call any SageMaker Pipeline.

Each SageMaker Pipeline definition should be be treated as a module inside its own folder, for example here the "batch_inference" pipeline, contained inside `batch_inference/`.
