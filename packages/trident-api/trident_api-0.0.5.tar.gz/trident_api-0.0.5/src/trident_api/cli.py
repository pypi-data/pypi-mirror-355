import sys
import os
import logging
import time
import json
import argparse
from logging import basicConfig, getLogger, Logger

from dotenv import load_dotenv
import docker

from .client import TridentClient

logger = getLogger(__name__)

def init_logger(log_level: int) -> Logger:
    basicConfig(level=log_level, style="{", format="{asctime} {levelname:7} {message}")
    return getLogger(__name__)

def init_dotenv(env_file='.env'):
    if os.path.exists(env_file):
        load_dotenv(env_file)
        logger.debug(f"Loaded environment variables from {env_file}")
    else:
        logger.warning(f"{env_file} not found; skipping loading of environment variables")

def init_argparse():
    """Initializes argparse with subparsers for the CLI commands."""
    parser = argparse.ArgumentParser(
        description="A command-line interface for the Trident service."
    )
    parser.add_argument(
        '--log',
        default='INFO',
        help='Set the logging level. Options: DEBUG, INFO, WARNING, ERROR, CRITICAL'
    )
    parser.add_argument(
        '--env',
        default='.env',
        help='Set the environment file path.'
    )
    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')

    parser_publish = subparsers.add_parser('publish', help='Publish an asset (algorithm or dataset).')
    parser_publish.add_argument('--bucket', required=True, help='Name of the bucket to upload to.')
    parser_publish.add_argument('--filename', required=False, help='Name of the file after upload.')
    parser_publish.add_argument('--filepath', required=True, help='Filepath for the file to upload.')
    parser_publish.add_argument('--metafilepath', required=True, help='Filepath to the metadatafile for publishing.')
    parser_publish.add_argument('--compute', action='store_true', help='Set if the asset is a compute to data asset.')
    parser_publish.add_argument('--trusted', required=False, help='Add a trusted DID.')
    
    parser_delete = subparsers.add_parser('delete', help='Delete an asset by its DID.')
    parser_delete.add_argument('--did', required=True, help='The DID of the asset to delete.')

    parser_compute = subparsers.add_parser('compute', help='Start a compute job.')
    parser_compute.add_argument('--asset_did', required=True, help='The DID of the dataset asset.')
    parser_compute.add_argument('--algorithm_did', required=True, help='The DID of the algorithm to run.')
    
    return parser.parse_args()


def get_image_checksum(image_name: str) -> str | None:
    logger.info(f"Attempting to get checksum for image: {image_name}")
    try:
        client = docker.from_env()
        
        try:
            image = client.images.get(image_name)
            logger.info("Image found locally.")
        except docker.errors.ImageNotFound:
            logger.info(f"Image not found locally. Pulling '{image_name}'...")
            image = client.images.pull(image_name)
            logger.info("Image pulled successfully.")

        digests = image.attrs.get('RepoDigests')
        
        if not digests:
            logger.warning(
                f"Image '{image_name}' has no RepoDigests. This usually means "
                f"it's a locally built image that hasn't been pushed to a "
                f"registry. Using the image ID as a fallback."
            )
            return image.id

        checksum = digests[0].split('@')[-1]
        logger.info(f"Found checksum: {checksum}")
        return checksum

    except docker.errors.APIError as e:
        logger.error(
            f"Docker API error: Could not find or pull image '{image_name}'. "
            f"Please ensure the image name and tag are correct. Details: {e}"
        )
        return None
    except docker.errors.DockerException as e:
        logger.error(
            f"Could not connect to the Docker daemon. Is Docker running? Details: {e}"
        )
        logger.error("Maybe add your user to docker group: 'sudo usermod -aG docker $USER & newgrp docker'")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None


def handle_publish(client: TridentClient, args):
    logger.info(f"Publishing from file: {args.filepath} with metadata: {args.metafilepath}")
        
    # 1. Upload file to S3
    name = os.path.basename(args.filepath) if not args.filename else args.filename
    with open(args.filepath, "rb") as f:
        response = client.request("POST", "/s3/upload", files={"file": f}, data={"bucket": args.bucket, "key": name})
        
    if response.status_code != 201:
        logger.error(f"Failed to upload file to S3: {response.text}")
        return

    # 2. Updating metadata   
    with open(args.metafilepath, "rb") as f:
        metadata = json.load(f)        

    metadata['url'] = response.json()['presignedUrl']
    logger.info(f"File uploaded successfully ({response.status_code}). URL: {metadata['url']}")
    access_method = "compute" if args.compute else "access"
    asset_type = "algorithm" if "entrypoint" in metadata.keys() else "dataset"
    
    if asset_type == "dataset" and args.trusted:
        metadata['trustedAlgorithms'].append(args.trusted)

    # 3. Publish metadata
    logger.info(f"Publishing new {asset_type} asset ({access_method}) to Trident...")
       
    if asset_type == "algorithm" and metadata['checksum'] == "":
        metadata['checksum'] = get_image_checksum(f"{metadata['image']}:{metadata['tag']}") 
    
    response = client.post(f'/nautilus/{asset_type}/{access_method}', metadata)
    
    if response.status_code == 201:
        did = response.json()["ddo"]["id"]
        logger.info(f"Successfully created {asset_type} asset ({access_method}) with DID: {did}")
        print(f"{did}")
    else:
        logger.error(f"Failed to create algorithm: {response.text}")

def handle_delete(client: TridentClient, args):
    logger.info(f"Attempting to delete asset with DID: {args.did}")
    response = client.delete('/nautilus/delete', {"did": args.did})
    if response.status_code == 200:
        logger.info(f"Successfully initiated deletion for DID: {args.did}")
        print(f"Deletion request sent for {args.did}.")
    else:
        logger.error(f"Failed to delete asset {args.did}: {response.text}")


def handle_compute(client: TridentClient, args):
    logger.info(f"Starting compute job on dataset {args.asset_did} with algorithm {args.algorithm_did}")
    response = client.post('/nautilus/compute', {"assetDid": args.asset_did, "algorithmDid": args.algorithm_did})
    
    if response.status_code != 200:
        logger.error(f"Failed to start compute job: {response.text}")
        return

    res = response.json()
    job_id = res.get("jobId")
    if not job_id:
        logger.error(f"Could not get Job ID from response: {res}")
        return
        
    logger.info(f"Started compute job {job_id} with status '{res.get('statusText', 'N/A')}'")

    # Polling for status
    status = 0
    while status < 70: # Loop until 'AlgorithmFinished' or failure
        time.sleep(10)
        try:
            response = client.get('/nautilus/compute/status', {"jobId": job_id})
            res = response.json()
            status = res.get("status", 0)
            logger.info(f"Job '{job_id}' status {status}: '{res.get('statusText', 'N/A')}'")
            if status > 70: # Any status > 70 is a failure state
                logger.error(f"Job failed with status: {res.get('statusText')}")
                break
        except Exception as e:
            logger.warning(f"Error occurred during status query: {e}")
            pass

    # Fetch result if successful
    if status == 70: # Status for AlgorithmFinished
        response = client.get('/nautilus/compute/result', {"jobId": job_id})
        result_url = response.text
        logger.info(f"Compute job finished. Result URL: {result_url}")
        print(f"Result URL: {result_url}")


def main():
    args = init_argparse()
    
    log_level = os.getenv("LOG_LEVEL") or args.log.upper()
    init_logger(getattr(logging, log_level, logging.INFO))
    init_dotenv(args.env)

    trident_service = os.getenv('TRIDENT_SERVICE')
    trident_username = os.getenv('TRIDENT_USERNAME')
    trident_password = os.getenv('TRIDENT_PASSWORD')

    if not all([trident_service, trident_username, trident_password]):
        logger.error("TRIDENT_SERVICE, TRIDENT_USERNAME, or TRIDENT_PASSWORD not set in environment or .env file.")
        sys.exit(1)

    client = TridentClient(trident_service, trident_username, trident_password)
    logger.info(f"Client initialized for service: {trident_service}/api")

    if args.command == 'publish':
        handle_publish(client, args)
    elif args.command == 'delete':
        handle_delete(client, args)
    elif args.command == 'compute':
        handle_compute(client, args)
    else:
        logger.error(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()