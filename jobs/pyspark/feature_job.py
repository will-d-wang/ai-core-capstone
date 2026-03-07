import argparse
import os
from collections import defaultdict
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_date", required=True)  # YYYY-MM-DD
    parser.add_argument("--s3_endpoint", default=os.environ.get("S3_ENDPOINT"))
    parser.add_argument("--bucket", default=os.environ.get("S3_BUCKET", "lake"))
    parser.add_argument("--shuffle_partitions", type=int, default=8)
    return parser.parse_args()


def build_feature_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {"event_count": 0, "purchase_count": 0, "click_count": 0}
    )
    for event in events:
        key = (str(event["dt"]), str(event["tenant_id"]))
        grouped[key]["event_count"] += 1
        if event.get("event_type") == "purchase":
            grouped[key]["purchase_count"] += 1
        if event.get("event_type") == "click":
            grouped[key]["click_count"] += 1

    rows: list[dict[str, Any]] = []
    for (dt, tenant_id), metrics in grouped.items():
        rows.append(
            {
                "dt": dt,
                "tenant_id": tenant_id,
                "event_count": metrics["event_count"],
                "purchase_count": metrics["purchase_count"],
                "click_count": metrics["click_count"],
            }
        )
    return sorted(rows, key=lambda row: (row["dt"], row["tenant_id"]))


def main() -> None:
    from pyspark.sql import SparkSession, functions as F

    args = parse_args()
    if not args.s3_endpoint:
        raise ValueError("Missing S3 endpoint. Provide --s3_endpoint or S3_ENDPOINT env var.")

    spark = (
        SparkSession.builder.appName("daily-feature-job")
        .config("spark.sql.shuffle.partitions", str(args.shuffle_partitions))
        .getOrCreate()
    )

    hconf = spark.sparkContext._jsc.hadoopConfiguration()
    hconf.set("fs.s3a.endpoint", args.s3_endpoint.replace("http://", "").replace("https://", ""))
    hconf.set("fs.s3a.path.style.access", "true")
    hconf.set("fs.s3a.connection.ssl.enabled", "false")
    hconf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    hconf.set("fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
    hconf.set("fs.s3a.access.key", os.environ["AWS_ACCESS_KEY_ID"])
    hconf.set("fs.s3a.secret.key", os.environ["AWS_SECRET_ACCESS_KEY"])

    dt = args.run_date
    input_path = f"s3a://{args.bucket}/curated/events/dt={dt}/"
    output_path = f"s3a://{args.bucket}/curated/features/"

    df = spark.read.parquet(input_path)
    if df.rdd.isEmpty():
        raise ValueError("curated_events is empty")

    features = (
        df.groupBy("dt", "tenant_id")
        .agg(
            F.count("*").alias("event_count"),
            F.sum(F.when(F.col("event_type") == "purchase", F.lit(1)).otherwise(F.lit(0))).alias(
                "purchase_count"
            ),
            F.sum(F.when(F.col("event_type") == "click", F.lit(1)).otherwise(F.lit(0))).alias(
                "click_count"
            ),
        )
        .withColumn("purchase_rate", F.col("purchase_count") / F.col("event_count"))
    )

    (
        features.repartition("dt", "tenant_id")
        .write.mode("overwrite")
        .partitionBy("dt", "tenant_id")
        .parquet(output_path)
    )

    spark.stop()


if __name__ == "__main__":
    main()
