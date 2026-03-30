import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


SERVICES = {
    "EC2": {
        "usage_types": [
            "BoxUsage:t3.medium",
            "BoxUsage:m5.large",
            "CPUCredits:t3",
            "DataTransfer-Out-Bytes",
        ],
        "regions": ["us-east-1", "us-west-2", "us-east-2"],
        "cost_range": (0.8, 12.0),
        "resource_prefix": "i-",
    },
    "S3": {
        "usage_types": [
            "TimedStorage-ByteHrs",
            "Requests-Tier1",
            "DataTransfer-Out-Bytes",
        ],
        "regions": ["us-east-1", "us-west-2"],
        "cost_range": (0.001, 0.08),
        "resource_prefix": "bucket-",
    },
    "RDS": {
        "usage_types": [
            "db.t3.micro",
            "db.t3.small",
            "StorageUsage",
            "BackupUsage",
        ],
        "regions": ["us-east-1", "us-east-2"],
        "cost_range": (0.5, 6.0),
        "resource_prefix": "db-",
    },
    "Lambda": {
        "usage_types": [
            "Lambda-GB-Second",
            "Lambda-Requests",
        ],
        "regions": ["us-east-1", "us-west-2"],
        "cost_range": (0.0001, 0.4),
        "resource_prefix": "lambda-",
    },
    "CloudWatch": {
        "usage_types": [
            "Metrics",
            "Logs-Ingested",
            "Logs-Archived",
        ],
        "regions": ["us-east-1", "us-west-2"],
        "cost_range": (0.01, 0.2),
        "resource_prefix": "cw-",
    },
    "NAT Gateway": {
        "usage_types": [
            "NatGateway-Hours",
            "DataProcessed-Bytes",
        ],
        "regions": ["us-east-1", "us-west-2"],
        "cost_range": (0.5, 4.0),
        "resource_prefix": "nat-",
    },
    "EBS": {
        "usage_types": [
            "EBS:VolumeUsage",
            "EBS:SnapshotUsage",
            "EBS:IORequests",
        ],
        "regions": ["us-east-1", "us-west-2"],
        "cost_range": (0.1, 1.5),
        "resource_prefix": "vol-",
    },
}

SERVICE_WEIGHTS = {
    "EC2": 30,
    "RDS": 18,
    "S3": 15,
    "Lambda": 15,
    "EBS": 10,
    "NAT Gateway": 7,
    "CloudWatch": 5,
}


def random_resource_id(prefix: str, service: str) -> str:
    if service == "S3":
        return f"{prefix}{random.choice(['logs', 'assets', 'backup', 'media'])}-{random.randint(100, 999)}"
    if service == "Lambda":
        return f"{prefix}{random.choice(['image-resizer', 'auth-hook', 'billing-job', 'event-worker'])}-{random.randint(10, 99)}"
    return f"{prefix}{random.randint(100000, 999999)}"


def apply_waste_pattern(service: str, usage_type: str, base_cost: float, day_index: int) -> float:
    cost = base_cost

    # Idle EC2 instances: consistently high cost
    if service == "EC2" and "BoxUsage" in usage_type:
        if day_index % 3 == 0:
            cost *= 1.8

    # Spiky Lambda usage
    if service == "Lambda" and day_index in {7, 14, 21, 28}:
        cost *= 4.5

    # NAT Gateway surprise bills
    if service == "NAT Gateway" and "DataProcessed" in usage_type:
        if day_index in {10, 11, 12, 24}:
            cost *= 3.2

    # S3 mostly small, but backup/storage grows slowly
    if service == "S3" and "TimedStorage" in usage_type:
        cost *= 1 + (day_index * 0.02)

    # CloudWatch log accumulation
    if service == "CloudWatch" and "Logs" in usage_type:
        cost *= 1 + (day_index * 0.015)

    # RDS steady but a bit expensive
    if service == "RDS" and usage_type in {"db.t3.micro", "db.t3.small"}:
        cost *= 1.25

    return round(cost, 4) 


def generate_rows(days: int = 30, min_rows_per_day: int = 15, max_rows_per_day: int = 30) -> list[dict]:
    rows = []
    service_names = list(SERVICE_WEIGHTS.keys())
    weights = list(SERVICE_WEIGHTS.values())

    start_date = datetime.today().date() - timedelta(days=days - 1)

    for day_index in range(days):
        current_date = start_date + timedelta(days=day_index)
        daily_rows = random.randint(min_rows_per_day, max_rows_per_day)

        for _ in range(daily_rows):
            service = random.choices(service_names, weights=weights, k=1)[0]
            config = SERVICES[service]

            usage_type = random.choice(config["usage_types"])
            region = random.choice(config["regions"])
            base_cost = random.uniform(*config["cost_range"])
            blended_cost = apply_waste_pattern(service, usage_type, base_cost, day_index)
            resource_id = random_resource_id(config["resource_prefix"], service)

            rows.append(
                {
                    "service": service,
                    "usageType": usage_type,
                    "region": region,
                    "blendedCost": blended_cost,
                    "usageDate": str(current_date),
                    "resourceId": resource_id,
                }
            )

    return rows


def main() -> None:
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    rows = generate_rows(days=30, min_rows_per_day=20, max_rows_per_day=35)
    df = pd.DataFrame(rows)

    output_file = output_dir / "synthetic_aws_costs.csv"
    df.to_csv(output_file, index=False)

    print(f"Generated {len(df)} rows at: {output_file}")
    print("\nTop service totals:")
    print(df.groupby("service")["blendedCost"].sum().sort_values(ascending=False).round(2))


if __name__ == "__main__":
    main()