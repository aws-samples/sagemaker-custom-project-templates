# Multi-Branch MLOps training pipeline

## Purpose

The purpose of this template is to enable multiple data scientists to work in parallel in concurrent experiments without interfering with each other and submitting conflicting changes to the repository.

Much like in the context of software engineering there is the concept of feature branches and GitFlow, this sample introduces the concept of experiment branches.

Each experiment when submitted to the remote repository by using ``git push`` will trigger a training job that will generate a model artifact tagged with the commit hash and a `Pending` status.

When a pull request gets approved from the ``experiment/<experiment_name>`` branch into `main`, the produced model artifact gets automatically changed to `Approved`.

![experiment-branch.jpg](images/experiment-branch.jpg)

## Architecture

There are two architectures available, one using AWS CodePipeline and AWS CodeCommit and another using Jenkins and GitHub.

### AWS CodePipeline and AWS CodeCommit

![codepipeline-codecommit-arch-train-complete.png](images/codepipeline-codecommit-arch-train-complete.png)

### Jenkins and GitHub

![jenkins-arch-train-complete.png](images/jenkins-arch-train-complete.png)

## Usage

For details on how to use the provided code, you can read this blog post.
