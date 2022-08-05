# Advanced topics
The topics defined here assume you have already deployed the solution once following the steps in the main [README](README.md)

- [Advanced topics](#advanced-topics)
  - [Setup CodeCommit with this repository](#setup-codecommit-with-this-repository)


## Setup CodeCommit with this repository
You would wonder after you have cloned this repository and deployed the solution how would you then start to interact with your deployed CodeCommit repository and start using it as a main repository and push changes to it. You have 2 options for this:
1. Clone the created CodeCommit repository and start treating it seperately from this repository
2. Just use this folder as a repository

For the second option, you can do the following (while you are in the folder `mlops-infra`):
```
git init
```
this will create a local git for this folder which would be separate from the main so you can treat it as any git repo and it would not impact the main repository git. So, add the CodeCommit Repository as a remote source:
```
git remote add origin https://git-codecommit.eu-west-1.amazonaws.com/v1/repos/mlops-infra
```
Ensure you have configured your machine to connect to CodeCommit and make `git push` or `git pull` commands to it; follow [Step 3 from the AWS documentation](https://docs.aws.amazon.com/codecommit/latest/userguide/setting-up-https-unixes.html).

Now you can interact with the CodeCommit repository as normal. You will need to do the following for the first commit:
```
git add -A
git commit -m "first commit"
export AWS_PROFILE=mlops-governance
git push origin main
make init   # this will enable precommit which will now block any further pushes to the main branch
```

Ensure that your git uses the branch name **main** by default, otherwise the push command might fail and you will need to create a main branch then push changes through it.

If you want to push the changes you made back to the main repository this folder belongs to you can just run this command:
```
rm -fr .git
```
This will remove the git settings from this folder so it would go back to the main repository settings. You can then raise a PR to include your changes to the main repository in GitHub.

