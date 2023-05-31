'''
loop through CDK generated assets and upload to s3

'''
from os import path, listdir, getenv
import boto3, shutil

import logging
logging.basicConfig()

logger = logging.getLogger(__file__.split('/')[-1])
logger.setLevel(getenv("LOGLEVEL", "INFO"))

def upload_assets_to_s3(account_id):
    '''
    loop through cdk.out folder, identified generated assests, compress if needed, and then upload to s3
    '''

    # assume role cdk-hnb659fds-deploy-role-870955006425-eu-west-1
    role_arn = f"arn:aws:iam::{account_id}:role/cdk-hnb659fds-file-publishing-role-{account_id}-eu-west-1"
    sts_client = boto3.client('sts')
    assumed_role_object = sts_client.assume_role(RoleArn = role_arn, RoleSessionName = 'AssumeRoleSession1')
    assumed_credentials=assumed_role_object['Credentials']

    _s3 = boto3.resource('s3', aws_access_key_id=assumed_credentials['AccessKeyId'],
            aws_secret_access_key=assumed_credentials['SecretAccessKey'],
            aws_session_token=assumed_credentials['SessionToken'])

    destination_bucket=f"cdk-hnb659fds-assets-{account_id}-eu-west-1"
    logger.info(f"----------upload assets to s3 bucket: {destination_bucket}")
    i_count = 0
    cdk_root = f'{path.dirname(path.realpath(__file__))}/cdk.out'
    for item in listdir(cdk_root):
        if item.startswith('asset.') and item.endswith('.zip'):
            upload_one_file_to_s3(_s3, f'{cdk_root}/{item}', destination_bucket)
            i_count += 1
        elif item.startswith('asset.'):
            zip_path = compress_folder(f'{cdk_root}/{item}')
            upload_one_file_to_s3(_s3, zip_path, destination_bucket)
            i_count += 1
        else:
            pass

    logger.info(f"----------uploaded {i_count} assets to s3 bucket: {destination_bucket}")


def compress_folder(folder_path):
    '''
    compress the folder and return the path of the compressed file
    '''
    logger.info(f"----------compressing folder: {folder_path}")
    zip_file_path = shutil.make_archive(base_name=f'tmp/{folder_path}',
                                        format='zip',
                                        root_dir=folder_path,
                                        base_dir=None)
    logger.info(f"----------compressed folder: {folder_path}")
    return zip_file_path


def upload_one_file_to_s3(s3, zip_path, destination_bucket):
    '''
    upload one file to s3
    '''
    logger.info(f"----------uploading file: {zip_path} to s3 bucket: {destination_bucket}")
    base_name = path.basename(zip_path)
    assert base_name.startswith('asset.') and base_name.endswith('.zip')
    # s3 = boto3.resource('s3')
    s3.Bucket(destination_bucket).upload_file(zip_path, base_name[6:])
    logger.info(f"----------uploaded file: {zip_path} to s3 bucket: {destination_bucket}")
