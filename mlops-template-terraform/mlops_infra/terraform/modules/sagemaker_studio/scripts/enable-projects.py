import os
import boto3
from botocore.exceptions import ClientError

client = boto3.client('sagemaker')
sc_client = boto3.client('servicecatalog')

STUDIO_ROLE_ARN = os.environ.get('STUDIO_ROLE_ARN')

def enable_sm_projects():
    # enable Project on account level (accepts portfolio share)
    response = client.enable_sagemaker_servicecatalog_portfolio()

    # associate studio role with portfolio
    response = sc_client.list_accepted_portfolio_shares()
    portfolio_id = ''
    for portfolio in response['PortfolioDetails']:
        if portfolio['ProviderName'] == 'Amazon SageMaker':
            portfolio_id = portfolio['Id']

    response = sc_client.associate_principal_with_portfolio(
        PortfolioId=portfolio_id,
        PrincipalARN=STUDIO_ROLE_ARN,
        PrincipalType='IAM'
    )
if __name__ == "__main__":
    print(f"Enabling SM Projects using STUDIO_ROLE_ARN: {STUDIO_ROLE_ARN}")
    enable_sm_projects()