import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as cloudwatch from "aws-cdk-lib/aws-cloudwatch";

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

    // Fleet dashboard. The control plane's /metrics endpoint is scraped by the
    // CloudWatch agent into the BwSim/Fleet namespace; DKGR metrics arrive via
    // EMF log lines (lambda/dkgr_handler.py emit_emf).
    const fleetMetric = (metricName: string, statistic = "Maximum") =>
      new cloudwatch.Metric({
        namespace: "BwSim/Fleet",
        metricName,
        statistic,
        period: cdk.Duration.minutes(1),
      });

    const dashboard = new cloudwatch.Dashboard(this, "FleetDashboard", {
      dashboardName: "bwsim-fleet",
    });
    dashboard.addWidgets(
      new cloudwatch.SingleValueWidget({
        title: "Fleet",
        metrics: [
          fleetMetric("bwsim_hosts_connected"),
          fleetMetric("bwsim_mitigations_active"),
          fleetMetric("bwsim_drains_total"),
        ],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: "Fragmentation early-warning (min largest_free_block_bytes)",
        left: [fleetMetric("bwsim_host_largest_free_block_bytes", "Minimum")],
        leftAnnotations: [
          { value: 2 * 1024 ** 3, label: "reboot floor (2GB)", color: "#d03b3b" },
        ],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: "Config load latency (max, vs 30s SLA)",
        left: [fleetMetric("bwsim_host_config_load_ms", "Maximum")],
        leftAnnotations: [{ value: 30_000, label: "load SLA", color: "#d03b3b" }],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: "DKGR rotations",
        left: [
          new cloudwatch.Metric({
            namespace: "BwSim/DKGR",
            metricName: "KeysRotated",
            dimensionsMap: { Service: "dkgr" },
            statistic: "Sum",
            period: cdk.Duration.hours(1),
          }),
        ],
        right: [dkgr.metricErrors()],
        width: 12,
      }),
    );

    new cdk.CfnOutput(this, "HostHealthTable", { value: hostHealth.tableName });
    new cdk.CfnOutput(this, "LockTable", { value: locks.tableName });
    new cdk.CfnOutput(this, "KeyTable", { value: keys.tableName });
    new cdk.CfnOutput(this, "ArchiveBucket", { value: archive.bucketName });
  }
}
