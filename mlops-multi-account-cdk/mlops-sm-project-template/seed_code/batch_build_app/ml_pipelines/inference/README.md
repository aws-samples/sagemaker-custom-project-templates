# Inference SageMaker Pipeline

This SageMaker Pipeline definition creates a workflow that will:
- Preprocess data parsed from the data repository, to extract text content from documents
- Run a SageMaker Batch Transform job to generate example questions from the content of the document and extract the part of content used to generate each question
- (Placeholder) Concatenate different text fields from the output document to be used to create embeddings (currently only using the generated questions from the previous step)
- Run a SageMaker Batch Transform job to generate embeddings
- Postprocess the output document
- Create an OpenSearch index
- Populate an OpenSearch index with the content and associated embeddings
