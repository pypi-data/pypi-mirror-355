import os
import re
import json
import logging
import sys
import uuid
from typing import List, Optional
import boto3

import tornado
import tornado.web
from jupyter_server.base.handlers import APIHandler

from pydantic import BaseModel, Field

# Configuring the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a handler for the standard output (stdout)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Log formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(console_handler)


class Summary(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    podName: str
    usage: Optional[float] = None
    cost: Optional[float] = None
    project: str
    lastUpdate: str
    year: int
    month: str
    user_efs_cost: Optional[float] = None
    user_efs_gb: Optional[float] = None
    project_efs_cost: Optional[float] = None
    project_efs_gb: Optional[float] = None


class SummaryList(BaseModel):
    summaries: List[Summary]


class Detail(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    podName: str
    creationTimestamp: str
    deletionTimestamp: str
    cpuLimit: str
    memoryLimit: str
    gpuLimit: str
    volumes: str
    namespace: str
    notebook_duration: str
    session_cost: float
    instance_id: str
    instance_type: str
    region: str
    pricing_type: str
    cost: float
    instanceRAM: int
    instanceCPU: int
    instanceGPU: int
    instanceId: str


class DetailList(BaseModel):
    details: List[Detail]


class LogsHandler(APIHandler):
    @tornado.web.authenticated
    def get(self):
        logger.info("Getting usages and cost stats")
        try:
            # Verify that the required environment variables are set
            required_env_vars = ["OSS_S3_BUCKET_NAME", "OSSPI", "OSSProject"]
            for var in required_env_vars:
                if var not in os.environ:
                    raise EnvironmentError(
                        f"Missing required environment variable: {var}"
                    )

            bucket_path = os.environ["OSS_S3_BUCKET_NAME"]
            osspi = os.environ.get("OSSPI", "No")
            oss_project = os.environ.get("OSSProject", "").strip()

            full_url = self.request.full_url()
            # full_url = "http://localhost:63118/user/yovian/jupyterlab-resource-tracker"
            match = re.search("(\/user\/)(.*)(\/jupyterlab-resource-tracker)", full_url)
            username = match.group(2)

            # Extract bucket name and prefix from a single environment variable
            try:
                bucket_name, prefix = bucket_path.split("/", 1)
                # Ensure prefix ends with a slash for consistent relative-path calculation
                normalized_prefix = prefix if prefix.endswith('/') else prefix + '/'                
            except ValueError:
                raise EnvironmentError(f"Variable OSS_S3_BUCKET_NAME inválida; debe tener formato 'bucket/prefijo': {bucket_path}")

            logs = self.load_logs_from_s3_folder(bucket_name, normalized_prefix, osspi, oss_project, username)
            for log in logs:
                if "cost" in log and log["cost"] is None:
                    log["cost"] = 0.0
                if "usage" in log and log["usage"] is None:
                    log["usage"] = 0.0
                if "user_efs_cost" in log and log["user_efs_cost"] is None:
                    log["user_efs_cost"] = 0.0
                if "user_efs_gb" in log and log["user_efs_gb"] is None:
                    log["user_efs_gb"] = 0.0
                if "project_efs_cost" in log and log["project_efs_cost"] is None:
                    log["project_efs_cost"] = 0.0
                if "project_efs_gb" in log and log["project_efs_gb"] is None:
                    log["project_efs_gb"] = 0.0
            summary_list = SummaryList(summaries=logs)

        except FileNotFoundError as e:
            logger.error("Log file not found: %s", e)
            self.set_status(404)
            self.finish(json.dumps({"error": "Required log file not found."}))
            return
        except EnvironmentError as e:
            logger.error("Environment configuration error: %s", e)
            self.set_status(500)
            self.finish(json.dumps({"error": str(e)}))
            return
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON format in log file: %s", e)
            self.set_status(400)
            self.finish(json.dumps({"error": "Invalid log file format."}))
            return

        self.set_status(200)
        self.finish(
            json.dumps(
                {
                    "summary": [s.model_dump() for s in summary_list.summaries],
                    "details": [],
                }
            )
        )

    def load_logs_from_s3_folder(
            self, bucket: str, normalized_prefix: str, osspi: str, oss_project: str, username: str
    ) -> list:
        """
        List all objects in S3 under the given prefix and process each JSONL file.
        Filter by project and, if OSSPI == "No", filter by podName == jupyter-{username}.
        """
        data = []
        s3_client = boto3.client("s3")
        try:
            # Paginator to list all objects under the prefix
            paginator = s3_client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(Bucket=bucket, Prefix=normalized_prefix)
            
            for page in page_iterator:
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    # Skip any object not directly under the root prefix (no deeper levels)
                    if not key.startswith(normalized_prefix):
                        continue
                    relative_key = key[len(normalized_prefix):]
                    if '/' in relative_key:
                        # This file is in a subfolder; skip it
                        continue
                                        
                    # Only process files ending in .log or .jsonl (if desired)
                    if not key.endswith(".log") and not key.endswith(".jsonl"):
                        continue
                    # Retrieve the full object
                    s3_obj = s3_client.get_object(Bucket=bucket, Key=key)
                    for line in s3_obj["Body"].iter_lines():
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            logger.error("Invalid JSON format in %s: %s", key, line)
                            continue  # Skip malformed lines
                        # Filter by project
                        if record.get("project") != oss_project:
                            continue
                        # Filter by OSSPI / pod name
                        if osspi.lower() == "yes":
                            data.append(record)
                        else:
                            expected_podname = f"jupyter-{username}"
                            if record.get("podName") == expected_podname:
                                data.append(record)
        except Exception as e:
            logger.error("Error al procesar S3 folder %s/%s: %s", bucket, normalized_prefix, e)
            raise FileNotFoundError(f"No se pudo leer archivos en S3 en {bucket}/{normalized_prefix}") from e

        return data