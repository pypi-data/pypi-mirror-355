import os
import boto3
import base64
from typing import Dict, Any, Optional
from loguru import logger


def _setup_environment(session: Optional[boto3.Session] = None) -> Dict[str, Any]:
    """Initialize AWS environment and clients."""
    session = session or boto3.Session()
    credentials = session.get_credentials()

    required_env = {
        "UMD_AH_CREDSTORE_TABLENAME": "table name",
        "UMD_AH_ENVIRONMENT": "environment",
        "UMD_AH_PRODUCTSUITE": "product suite",
        "UMD_AH_PRODUCT": "product"
    }

    missing = [var for var, desc in required_env.items() if not os.getenv(var)]
    if missing:
        raise RuntimeError(f"Missing required credential store {required_env[missing[0]]}: {missing[0]}")

    aws_region = 'us-east-1'
    os.environ['AWS_DEFAULT_REGION'] = aws_region
    env = os.getenv('UMD_AH_ENVIRONMENT').lower()
    product_suite = os.getenv('UMD_AH_PRODUCTSUITE')
    product = os.getenv('UMD_AH_PRODUCT')

    return {
        'dynamodb': session.client('dynamodb', region_name=aws_region),
        'kms': session.client('kms', region_name=aws_region),
        'product_id': f"{product_suite}-{product}",
        'table_name': os.getenv('UMD_AH_CREDSTORE_TABLENAME'),
        '.env': 'sandbox' if 'sandbox' in env else env,
        'product_suite': product_suite,
        'product': product
    }


def _get_kms_key_id(session: Optional[boto3.Session] = None) -> str:
    """Retrieve KMS key ID from CloudFormation stack outputs."""
    try:
        cf = (session or boto3.Session()).client('cloudformation')
        response = cf.describe_stacks(StackName="UmdCredentialStoreStack")

        for stack in response.get("Stacks", []):
            for output in stack.get("Outputs", []):
                if output.get("OutputKey") == "CredStoreKmsKeyId":
                    return output["OutputValue"]

        raise RuntimeError("KMS key ID not found in CloudFormation stack outputs")

    except Exception as e:
        raise RuntimeError(f"Failed to retrieve KMS key ID from CloudFormation: {str(e)}")


def get_credential(key: str, session: Optional[boto3.Session] = None) -> str:
    """Retrieve and decrypt a credential from the store."""
    if os.getenv('TESTING'):
        return os.getenv(f'TEST_{key.upper()}_KEY', 'test-key')

    setup = _setup_environment(session)

    try:
        response = setup['dynamodb'].get_item(
            TableName=setup['table_name'],
            Key={
                "ProductId": {"S": setup['product_id']},
                "CredentialKey": {"S": key}
            }
        )

        item = response.get('Item')
        if not item:
            raise ValueError(f"No credential found for key: {key}")

        if 'EncryptedCredential' not in item:
            raise ValueError(f"No encrypted credential found for key: {key}")

        ciphertext = base64.b64decode(item['EncryptedCredential']['S'])
        decrypt_response = setup['kms'].decrypt(
            CiphertextBlob=ciphertext,
            EncryptionContext={
                'Environment': setup['.env'],
                'CredentialKey': key,
                'ProductSuite': setup['product_suite'],
                'Product': setup['product']
            }
        )

        plaintext = decrypt_response.get('Plaintext')
        if not plaintext:
            raise RuntimeError(f"KMS decryption failed for key: {key}")

        return plaintext.decode('utf-8')

    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error retrieving credential '{key}': {str(e)}")


def add_credential(key: str, credential: str, force: bool = False, session: Optional[boto3.Session] = None) -> None:
    """Encrypt and store a credential."""
    setup = _setup_environment(session)

    # Check if credential exists and force flag
    if not force:
        try:
            existing = setup['dynamodb'].get_item(
                TableName=setup['table_name'],
                Key={
                    "ProductId": {"S": setup['product_id']},
                    "CredentialKey": {"S": key}
                }
            )
            if existing.get('Item'):
                raise RuntimeError(f"Credential '{key}' already exists. Use force=True to overwrite.")
        except Exception as e:
            if "already exists" in str(e):
                raise
            # If error is something else (like credential not found), continue

    try:
        encrypt_response = setup['kms'].encrypt(
            KeyId=_get_kms_key_id(session),
            Plaintext=credential,
            EncryptionContext={
                'Environment': setup['.env'],
                'CredentialKey': key,
                'ProductSuite': setup['product_suite'],
                'Product': setup['product']
            }
        )

        encrypted = base64.b64encode(encrypt_response['CiphertextBlob']).decode('utf-8')
        setup['dynamodb'].put_item(
            TableName=setup['table_name'],
            Item={
                'ProductId': {'S': setup['product_id']},
                'CredentialKey': {'S': key},
                'EncryptedCredential': {'S': encrypted}
            }
        )

        logger.info(f"Successfully stored credential: {key}")

    except Exception as e:
        raise RuntimeError(f"Failed to store credential '{key}': {str(e)}")


def delete_credential(key: str, session: Optional[boto3.Session] = None) -> None:
    """Delete a credential from the store."""
    setup = _setup_environment(session)

    try:
        setup['dynamodb'].delete_item(
            TableName=setup['table_name'],
            Key={
                "ProductId": {"S": setup['product_id']},
                "CredentialKey": {"S": key}
            }
        )
        logger.info(f"Successfully deleted credential: {key}")

    except Exception as e:
        raise RuntimeError(f"Failed to delete credential '{key}': {str(e)}")