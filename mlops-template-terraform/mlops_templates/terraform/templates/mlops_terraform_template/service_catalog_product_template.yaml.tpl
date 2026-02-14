Description: |-
  Sagemaker Projects - MLOps Template using Terraform
Parameters:
  SageMakerProjectName:
    Type: String
    AllowedPattern: ^[a-zA-Z](-*[a-zA-Z0-9])*
    Description: Name of the project
    MaxLength: 32
    MinLength: 1
  SageMakerProjectId:
    Type: String
    Description: Service generated Id of the project.
Resources:
  MlOpsArtifactsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName:
        Fn::Sub: "${artifact_bucket_name}"
    DeletionPolicy: Retain
  MlOpsProjectStateBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName:
        Fn::Sub: "${state_bucket_name}"
    DeletionPolicy: Retain
  ModelBuildCodeCommitRepository:
    Type: AWS::CodeCommit::Repository
    Properties:
      RepositoryName:
        Fn::Sub: "${build_code_repo_name}"
      Code:
        BranchName: ${default_branch}
        S3:
          Bucket: ${seed_code_bucket}
          Key: ${seed_code_build_key}
      RepositoryDescription: Model Build Code
  ModelDeployCodeCommitRepository:
    Type: AWS::CodeCommit::Repository
    Properties:
      RepositoryName:
        Fn::Sub: "${deploy_code_repo_name}"
      Code:
        BranchName: ${default_branch}
        S3:
          Bucket: ${seed_code_bucket}
          Key:  ${seed_code_deploy_key}
      RepositoryDescription: Model Deploy Code
Outputs:
  Prefix:
    Value: "${prefix}"
    Description: Prefix value for infrastructure created by this template
  DefaultBranch:
    Value: "${default_branch}"
    Description: Default branch CodeCommit
  MlOpsProjectStateBucket:
    Value: !Ref MlOpsProjectStateBucket
    Description: Name of State Bucket for Project
  MlOpsArtifactsBucket:
    Value: !Ref MlOpsArtifactsBucket
    Description: Name of Artifacts Bucket for Project
  BucketRegion:
    Value: !Sub "$${AWS::Region}"
    Description: Region on State Bucket for Project
