import argparse
import os

from pyspark.sql import SparkSession, Window, functions as F
from pyspark.sql.types import MapType, StringType, StructField, StructType

RAW_SCHEMA = StructType(
    [
        StructField("tenant_id", StringType(), nullable=False),
        StructField("event_id", StringType(), nullable=False),
        StructField("event_ts", StringType(), nullable=False),
        StructField("event_type", StringType(), nullable=False),
        StructField("payload", MapType(StringType(), StringType()), nullable=True),
    ]
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_date", required=True)  # YYYY-MM-DD
    parser.add_argument("--tenant_id", default=None)
    parser.add_argument("--s3_endpoint", default=os.environ.get("S3_ENDPOINT"))
    parser.add_argument("--bucket", default=os.environ.get("S3_BUCKET", "lake"))
    parser.add_argument("--shuffle_partitions", type=int, default=8)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.s3_endpoint:
        raise ValueError("Missing S3 endpoint. Provide --s3_endpoint or S3_ENDPOINT env var.")

    spark = (
        SparkSession.builder.appName("daily-ingest-job")
        .config("spark.sql.shuffle.partitions", str(args.shuffle_partitions))
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
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
    tenant_filter = f"/tenant_id={args.tenant_id}" if args.tenant_id else ""
    raw_path = f"s3a://{args.bucket}/raw/dt={dt}{tenant_filter}/*.json"
    out_path = f"s3a://{args.bucket}/curated/events/"

    df = spark.read.schema(RAW_SCHEMA).json(raw_path)
    if df.rdd.isEmpty():
        raise ValueError("raw_events is empty")

    df = (
        df.withColumn("event_ts_ts", F.to_timestamp("event_ts"))
        .withColumn("dt", F.to_date("event_ts_ts"))
        .withColumn("payload_json", F.to_json("payload"))
        .drop("payload")
        .filter(
            F.col("tenant_id").isNotNull()
            & F.col("event_id").isNotNull()
            & F.col("event_ts_ts").isNotNull()
        )
        .filter(F.col("dt") == F.to_date(F.lit(dt)))
    )

    window = Window.partitionBy("tenant_id", "event_id").orderBy(
        F.col("event_ts_ts").desc(), F.col("event_type").desc()
    )
    df = df.withColumn("rn", F.row_number().over(window)).filter(F.col("rn") == 1).drop("rn")

    (
        df.repartition("dt", "tenant_id")
        .write.mode("overwrite")
        .partitionBy("dt", "tenant_id")
        .parquet(out_path)
    )

    spark.stop()


if __name__ == "__main__":
    main()
