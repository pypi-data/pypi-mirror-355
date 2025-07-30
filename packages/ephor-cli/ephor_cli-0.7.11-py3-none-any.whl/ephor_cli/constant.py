import os

API_SERVER_URL = os.getenv("API_SERVER_URL", "https://mcp-hive.ti.trilogy.com/api")

EPHOR_SERVER_URL = os.getenv("EPHOR_SERVER_URL", "https://ephor.ti.trilogy.com/api")

AGENT_SERVER_URL = os.getenv("AGENT_SERVER_URL", "https://agents.ti.trilogy.com")

DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "mcp-hive-prod")

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "https://mcp-server.ti.trilogy.com")

AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "mcp-hive")

AWS_OPENSEARCH_ENDPOINT = os.getenv("AWS_OPENSEARCH_ENDPOINT", "https://search-test-ephor-wasj5ovwnv2wix7k76qagdi6w4.aos.us-east-1.on.aws")

AWS_OPENSEARCH_INDEX_NAME=os.getenv("AWS_OPENSEARCH_INDEX_NAME", "conversation-chunks")