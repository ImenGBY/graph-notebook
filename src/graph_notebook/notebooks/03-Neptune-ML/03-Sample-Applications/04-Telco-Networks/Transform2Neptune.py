{
	"jobConfig": {
		"name": "Transform2Neptune",
		"description": "transfo to neptune format edges and nodes ",
		"role": "arn:aws:iam::134846823987:role/aws-glue-4-telcograph",
		"command": "glueetl",
		"version": "3.0",
		"runtime": null,
		"workerType": "G.4X",
		"numberOfWorkers": 10,
		"maxCapacity": 40,
		"maxRetries": 0,
		"timeout": 2880,
		"maxConcurrentRuns": 1,
		"security": "none",
		"scriptName": "Transform2Neptune.py",
		"scriptLocation": "s3://aws-glue-assets-134846823987-eu-west-1/scripts/",
		"language": "python-3",
		"spark": true,
		"sparkConfiguration": "standard",
		"jobParameters": [],
		"tags": [],
		"jobMode": "DEVELOPER_MODE",
		"createdOn": "2023-05-23T21:27:55.494Z",
		"developerMode": true,
		"connectionsList": [],
		"temporaryDirectory": "s3://aws-glue-assets-134846823987-eu-west-1/temporary/",
		"logging": true,
		"glueHiveMetastore": true,
		"etlAutoTuning": true,
		"metrics": true,
		"bookmark": "job-bookmark-disable",
		"sparkPath": "s3://aws-glue-assets-134846823987-eu-west-1/sparkHistoryLogs/",
		"flexExecution": false,
		"minFlexWorkers": null
	},
	"hasBeenSaved": false,
	"script": "import sys\nfrom awsglue.transforms import *\nfrom awsglue.utils import getResolvedOptions\nfrom pyspark.context import SparkContext\nfrom awsglue.context import GlueContext\nfrom awsglue.job import Job\nimport pyspark.sql.functions as f\n\n\n## @params: [JOB_NAME]\nargs = getResolvedOptions(sys.argv, ['JOB_NAME'])\n\nsc = SparkContext()\nglueContext = GlueContext(sc)\nspark = glueContext.spark_session\n\ndef transform_edges(spark, s3_path: str, s3_dest: str, max_from: int = -1):\n    _, basename = s3_path.rsplit('/', 1)\n    basename = basename.split('.')[0]\n    _, fro, verb, to = basename.split('_')\n\n    df = (\n            spark.read.format(\"com.databricks.spark.csv\")\n            .option(\"header\", \"false\")\n            .option(\"inferSchema\", \"true\")\n            .load(s3_path)\n        )\n    columns = df.columns\n    label = f\"{fro}_{verb}_{to}\"\n    names = [\"~from\", \"~to\"] + [f\"{label}_attr_{i}:Float\" for i in range(len(columns) - 2)]\n    df = df.toDF(*names)\n    if max_from > 0:\n        df = df.where(df[\"~from\"] < f.lit(max_from))\n    df = df.withColumn(\"~label\", f.lit(label))\n    df = df.withColumn(\"~from\",f.concat_ws(\"_\", f.lit(fro), df[\"~from\"]))\n    df = df.withColumn(\"~to\", f.concat_ws(\"_\", f.lit(fro), df[\"~to\"]))\n    df = df.withColumn(\"~id\", f.concat_ws(\"_\", f.lit(label), f.monotonically_increasing_id()))\n    columns = list(df.columns)\n    columns.remove(\"~id\")\n    df = df.select(\"~id\", *columns)\n    df.write.format(\"com.databricks.spark.csv\").option(\"header\", \"true\").save(s3_dest)\n\ndef transform_nodes(spark, s3_path: str, s3_dest: str, max_node: int = -1):\n    _, basename = s3_path.rsplit('/', 1)\n    basename = basename.split('.')[0]\n    _, label = basename.split('_')\n\n    df = (\n            spark.read.format(\"com.databricks.spark.csv\")\n            .option(\"header\", \"false\")\n            .option(\"inferSchema\", \"true\")\n            .load(s3_path)\n        )\n    columns = df.columns\n    names = [\"~id\"] + [f\"{label}_attr_{i}:Float\" for i in range(len(columns) - 1)]\n    df = df.toDF(*names)\n    if max_node > 0:\n        df = df.where(df[\"~id\"] < f.lit(max_node))\n    df = df.withColumn(\"~label\", f.lit(label))\n    df = df.withColumn(\"~id\", f.concat_ws(\"_\", f.lit(label), df[\"~id\"]))\n    df.write.format(\"com.databricks.spark.csv\").option(\"header\", \"true\").save(s3_dest)\n\ntransform_nodes(spark,\"s3://aws-glue-telcograph/node_user.txt\", \"s3://aws-glue-telcograph/node_user.csv\")\ntransform_nodes(spark,\"s3://aws-glue-telcograph/node_cell.txt\", \"s3://aws-glue-telcograph/node_cell.csv\")\n# transform_nodes(spark,\"s3://aws-glue-telcograph/node_app.txt\", \"s3://aws-glue-telcograph/node_app.csv\")\n# transform_nodes(spark,\"s3://aws-glue-telcograph/node_package.txt\", \"s3://aws-glue-telcograph/node_package.csv\")\n\ntransform_edges(spark,\"s3://aws-glue-telcograph/edge_user_live_cell.txt\", \"s3://aws-glue-telcograph/edges_user_live_cell.csv\")\n# transform_edges(spark,\"s3://aws-glue-telcograph/edge_user_use_app.txt\", \"s3://aws-glue-telcograph/edge_user_use_app.csv\")\n# transform_edges(spark,\"s3://aws-glue-telcograph/edge_user_buy_package.txt\", \"s3://aws-glue-telcograph/edge_user_buy_package.csv\")\n\n\n\njob = Job(glueContext)\njob.init(args['JOB_NAME'], args)\njob.commit()"
}