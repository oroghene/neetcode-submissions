import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as s3 from "aws-cdk-lib/aws-s3";

export class BwsimStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Host health snapshots, TTL-reaped so the table only holds recent state.
    const hostHealth = new dynamodb.Table(this, "HostHealth", {
      partitionKey: { name: "host_id", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "reported_at", type: dynamodb.AttributeType.NUMBER },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: "expires_at",
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Lease locks (orchestrator/locks.py): conditional-write acquired,
    // expired leases stealable, fencing token on the row.
    const locks = new dynamodb.Table(this, "RebootLocks", {
      partitionKey: { name: "scope", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Datapath keys with TTL on retired versions (lambda/dkgr_handler.py).
    const keys = new dynamodb.Table(this, "DatapathKeys", {
      partitionKey: { name: "host_id", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: "expires_at",
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const dkgr = new lambda.Function(this, "DkgrRotator", {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "dkgr_handler.handler",
      code: lambda.Code.fromAsset("../lambda"),
      environment: { KEY_TABLE: keys.tableName },
      timeout: cdk.Duration.minutes(1),
    });
    keys.grantReadWriteData(dkgr);

    new events.Rule(this, "DkgrSchedule", {
      schedule: events.Schedule.rate(cdk.Duration.days(1)),
      targets: [new targets.LambdaFunction(dkgr)],
    });

    // Health archive for offline analysis (Athena/Glue over Parquet).
    const archive = new s3.Bucket(this, "HealthArchive", {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    new cdk.CfnOutput(this, "HostHealthTable", { value: hostHealth.tableName });
    new cdk.CfnOutput(this, "LockTable", { value: locks.tableName });
    new cdk.CfnOutput(this, "KeyTable", { value: keys.tableName });
    new cdk.CfnOutput(this, "ArchiveBucket", { value: archive.bucketName });
  }
}
