# MCP-Agentic-Data-Engineering

```bash
conda create -p venv python==3.11 -y
```

```bash
conda activate venv/
```

```bash
docker compose up
```
- stdio : used for terminal based application
- sse: used for non terminal based application like fastapi, flask etc


### For stdio protocol (MCP-Server)
```bash
python mcp_server/stdio/mcp_server.py
```
### For stdio protocol (MCP-Client)
```bash
python mcp_client/stdio/mcp_client.py
```

### For sse protocol (MCP-Server)
```bash
python mcp_server/sse/mcp_server.py
```

### For sse protocol (MCP-Client)
```bash
uvicorn mcp_client.sse.mcp_client:app --reload --port 3030  
```




### Following Functionalities this Agentic DE can perform
#### 1. Upload & Ingest Data
#### Prompt Example: Upload CSVs to MySQL
```bash
Upload all CSVs from the `data` folder into MySQL. Use filenames as table names.
```
#### Prompt Example: Upload JSON to MongoDB
```bash
Upload `customers.json` from the `data` folder to the `test_data` collection in the `coke` database.

```
#### 2. Modify & Update Data
#### Prompt Example: Update MySQL Tables
```bash
Set `is_active = 0` for users where `age > 60` in the `users` table.
```

#### Prompt Example: Update MongoDB Documents
```bash
Update all documents in the MongoDB database "coke" inside the "coke_collection1" collection where the customer_id is 101. Set the name field to "Manmeet".

```

#### 3. Manage S3-Like Object Stores
#### Prompt Example: Create S3 Buckets (MinIO)
```bash
Create a new S3 bucket for staging reports and log the creation in Jira.
```

#### Prompt Example: Move Files Across Buckets
```bash
Move all data from `raw-bucket/sales/` to `processed-bucket/sales-clean/`.
```


#### 4. Automate Workflows with Airflow
#### Prompt Example: Schedule Python Code as Airflow DAG
```bash
Run this every day at 8 AM:

import pandas as pd
df = pd.read_csv("s3://raw-bucket/sales.csv")
df.to_csv("s3://processed-bucket/cleaned_sales.csv")
```
#### 5. Ticketing & Task Logging
#### Prompt Example: Auto-Create Jira Tickets
```bash
Raise a Jira ticket for uploading sales data and verifying transformation completeness.
```

Enjoy Coding!







