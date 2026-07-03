// =====================================================================
// B案アーキテクチャ 個人検証スタック【完全形】
//
//   ブラウザ
//     └─ CloudFront + WAF（唯一の入口）
//          ├─ /*      → S3 プライベートバケット + OAC（React SPA）
//          └─ /api/*  → HTTP API Gateway（x-origin-verify 検証あり / throttling）
//                          └─ VPC Link → Cloud Map → ECS Fargate（プライベートサブネット）
//                               [FastAPI + PostgreSQL サイドカー]
//   機械間: /internal/ping は IAM(SigV4) 認証（API Key は使わない）
//
//   コスト注意: NAT Gateway(~$45/月) + WAF(~$7/月) + Fargate(~$18/月)
//               検証が終わったら必ず destroy すること
// =====================================================================
import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as s3deploy from "aws-cdk-lib/aws-s3-deployment";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import * as apigwv2 from "aws-cdk-lib/aws-apigatewayv2";
import { HttpServiceDiscoveryIntegration } from "aws-cdk-lib/aws-apigatewayv2-integrations";
import {
  HttpIamAuthorizer,
  HttpJwtAuthorizer,
} from "aws-cdk-lib/aws-apigatewayv2-authorizers";
import * as servicediscovery from "aws-cdk-lib/aws-servicediscovery";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import * as logs from "aws-cdk-lib/aws-logs";
import * as path from "path";

export interface DemoStackProps extends cdk.StackProps {
  /** us-east-1 の WafStack が出力する WebACL ARN */
  readonly webAclArn: string;
}

export class DemoStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: DemoStackProps) {
    super(scope, id, props);

    // CloudFront → オリジン検証用の秘密ヘッダ値（cdk.json context で差し替え可能）
    const originVerifySecret: string =
      this.node.tryGetContext("originVerifySecret") ??
      "ov-4f8Zr2Kq9mDempPz71xWcYb3";

    // Okta（個人検証テナント）。本番では SBR の Okta に差し替える
    const OKTA_ISSUER = "https://integrator-2363543.okta.com/oauth2/default";
    const OKTA_AUDIENCE = "api://default";

    // ------------------------------------------------------------
    // 1. VPC: パブリック(NAT/入口用) + プライベート(ECS実行用)
    //    NAT Gateway 1台（~$45/月。検証後は destroy！）
    // ------------------------------------------------------------
    const vpc = new ec2.Vpc(this, "Vpc", {
      maxAzs: 2,
      natGateways: 1,
      subnetConfiguration: [
        { name: "public", subnetType: ec2.SubnetType.PUBLIC },
        { name: "private", subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      ],
    });

    // ------------------------------------------------------------
    // 2. ECS クラスタ + Cloud Map 名前空間
    // ------------------------------------------------------------
    const cluster = new ecs.Cluster(this, "Cluster", { vpc });
    const namespace = cluster.addDefaultCloudMapNamespace({
      name: "demo.local",
    });

    const jwtSecret = new secretsmanager.Secret(this, "JwtSecret", {
      description: "sons02-demo01 JWT secret",
      generateSecretString: { excludePunctuation: true, passwordLength: 48 },
    });

    const logGroup = new logs.LogGroup(this, "Logs", {
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // ------------------------------------------------------------
    // 3. タスク定義: FastAPI + PostgreSQL サイドカー
    // ------------------------------------------------------------
    const taskDef = new ecs.FargateTaskDefinition(this, "TaskDef", {
      cpu: 512,
      memoryLimitMiB: 1024,
    });

    const dbContainer = taskDef.addContainer("db", {
      image: ecs.ContainerImage.fromRegistry(
        "public.ecr.aws/docker/library/postgres:16"
      ),
      environment: {
        POSTGRES_USER: "ses",
        POSTGRES_PASSWORD: "ses_pass_demo",
        POSTGRES_DB: "ses",
      },
      healthCheck: {
        command: ["CMD-SHELL", "pg_isready -U ses"],
        interval: cdk.Duration.seconds(10),
        retries: 5,
        startPeriod: cdk.Duration.seconds(15),
      },
      logging: ecs.LogDrivers.awsLogs({ streamPrefix: "db", logGroup }),
      memoryReservationMiB: 256,
    });

    const repo = ecr.Repository.fromRepositoryName(
      this,
      "BackendRepo",
      "sons02-demo01-backend"
    );

    const apiContainer = taskDef.addContainer("api", {
      image: ecs.ContainerImage.fromEcrRepository(repo, "latest"),
      environment: {
        DATABASE_URL: "postgresql+psycopg://ses:ses_pass_demo@localhost:5432/ses",
        JWT_EXPIRE_MINUTES: "60",
        ADMIN_EMAIL: "admin@example.com",
        ADMIN_PASSWORD: "Demo2026!",
        CORS_ORIGINS: "http://localhost",
        // CloudFront 以外からの直アクセスを 403 にする（main.py のミドルウェアが検証）
        ORIGIN_VERIFY_SECRET: originVerifySecret,
        // Okta トークン検証（バックエンド側の多層防御）
        OKTA_ISSUER: OKTA_ISSUER,
        OKTA_AUDIENCE: OKTA_AUDIENCE,
        // ダッシュボード用のデモデータを投入
        SEED_DEMO: "1",
      },
      secrets: {
        JWT_SECRET: ecs.Secret.fromSecretsManager(jwtSecret),
      },
      portMappings: [{ containerPort: 8000 }],
      logging: ecs.LogDrivers.awsLogs({ streamPrefix: "api", logGroup }),
    });

    apiContainer.addContainerDependencies({
      container: dbContainer,
      condition: ecs.ContainerDependencyCondition.HEALTHY,
    });

    // ------------------------------------------------------------
    // 4. Fargate サービス（プライベートサブネット・公開IPなし）
    // ------------------------------------------------------------
    const serviceSg = new ec2.SecurityGroup(this, "ServiceSg", {
      vpc,
      description: "Fargate service SG",
      allowAllOutbound: true, // ECR pull / Secrets / 将来の Gemini API 呼び出しは NAT 経由
    });

    const service = new ecs.FargateService(this, "Service", {
      cluster,
      taskDefinition: taskDef,
      desiredCount: 1,
      assignPublicIp: false, // プライベート化。外向きは NAT 経由
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [serviceSg],
      cloudMapOptions: {
        name: "api",
        cloudMapNamespace: namespace,
        dnsRecordType: servicediscovery.DnsRecordType.SRV,
        container: apiContainer,
        containerPort: 8000,
      },
      minHealthyPercent: 0,
    });

    // ------------------------------------------------------------
    // 5. HTTP API Gateway + VPC Link（SG は「SG参照」で連鎖させる）
    // ------------------------------------------------------------
    const vpcLinkSg = new ec2.SecurityGroup(this, "VpcLinkSg", {
      vpc,
      description: "API GW VPC Link SG",
      allowAllOutbound: true,
    });
    // SG 連鎖: VPC Link の SG からのみ 8000 を許可（IP 直書きしない）
    serviceSg.addIngressRule(vpcLinkSg, ec2.Port.tcp(8000), "from VPC Link");

    const vpcLink = new apigwv2.VpcLink(this, "VpcLink", {
      vpc,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [vpcLinkSg],
    });

    const httpApi = new apigwv2.HttpApi(this, "HttpApi", {
      apiName: "sons02-demo01-api",
    });

    const backendIntegration = new HttpServiceDiscoveryIntegration(
      "Backend",
      service.cloudMapService!,
      { vpcLink }
    );

    // ユーザー向け API: API GW 層で Okta JWT を検証（「験票」）
    const oktaAuthorizer = new HttpJwtAuthorizer("OktaJwt", OKTA_ISSUER, {
      jwtAudience: [OKTA_AUDIENCE],
    });
    httpApi.addRoutes({
      path: "/api/{proxy+}",
      methods: [apigwv2.HttpMethod.ANY],
      integration: backendIntegration,
      authorizer: oktaAuthorizer,
    });

    // 機械間ルート: IAM(SigV4) 認証。API Key は使わない方針のデモ
    httpApi.addRoutes({
      path: "/internal/ping",
      methods: [apigwv2.HttpMethod.GET],
      integration: backendIntegration,
      authorizer: new HttpIamAuthorizer(),
    });

    // Stage throttling（従量課金 LLM の暴走対策の二層目）
    const defaultStage = httpApi.defaultStage!.node
      .defaultChild as apigwv2.CfnStage;
    defaultStage.defaultRouteSettings = {
      throttlingRateLimit: 50, // 定常 50 req/s
      throttlingBurstLimit: 100, // バースト 100
    };

    // ------------------------------------------------------------
    // 6. S3（プライベート + OAC） + CloudFront + WAF
    // ------------------------------------------------------------
    const siteBucket = new s3.Bucket(this, "SiteBucket", {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED, // L2情報想定の保存時暗号化
      enforceSSL: true, // 転送時暗号化の強制
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    const apiDomain = cdk.Fn.select(2, cdk.Fn.split("/", httpApi.apiEndpoint));

    const distribution = new cloudfront.Distribution(this, "Distribution", {
      comment: "sons02-demo01 (B-plan practice)",
      defaultRootObject: "index.html",
      webAclId: props.webAclArn, // ← us-east-1 の WAF を装着
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessControl(siteBucket, {
          originAccessLevels: [
            cloudfront.AccessLevel.READ,
            cloudfront.AccessLevel.LIST,
          ],
        }),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
      },
      additionalBehaviors: {
        "/api/*": {
          origin: new origins.HttpOrigin(apiDomain, {
            customHeaders: { "x-origin-verify": originVerifySecret },
          }),
          viewerProtocolPolicy:
            cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
          cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
          originRequestPolicy:
            cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        },
      },
      errorResponses: [
        {
          httpStatus: 404,
          responseHttpStatus: 200,
          responsePagePath: "/index.html",
          ttl: cdk.Duration.seconds(0),
        },
        {
          httpStatus: 403,
          responseHttpStatus: 200,
          responsePagePath: "/index.html",
          ttl: cdk.Duration.seconds(0),
        },
      ],
    });

    // ------------------------------------------------------------
    // 7. フロントエンド資産のデプロイ
    // ------------------------------------------------------------
    new s3deploy.BucketDeployment(this, "DeploySite", {
      sources: [
        s3deploy.Source.asset(path.join(__dirname, "../../frontend/dist")),
      ],
      destinationBucket: siteBucket,
      distribution,
      distributionPaths: ["/*"],
    });

    // ------------------------------------------------------------
    // 出力
    // ------------------------------------------------------------
    new cdk.CfnOutput(this, "CloudFrontUrl", {
      value: `https://${distribution.distributionDomainName}`,
      description: "アプリの入口（ここにアクセス）",
    });
    new cdk.CfnOutput(this, "ApiEndpoint", {
      value: httpApi.apiEndpoint,
      description: "API GW 直エンドポイント（直叩きは 403 になる）",
    });
    new cdk.CfnOutput(this, "AdminLogin", {
      value: "admin@example.com / Demo2026!",
      description: "検証用管理者ログイン",
    });
  }
}
