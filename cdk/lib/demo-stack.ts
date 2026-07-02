// =====================================================================
// B案アーキテクチャ 個人検証スタック
//
//   ブラウザ
//     └─ CloudFront（唯一の入口）
//          ├─ /*      → S3 プライベートバケット + OAC（React SPA）
//          └─ /api/*  → HTTP API Gateway（x-origin-verify ヘッダ付与）
//                          └─ VPC Link → Cloud Map → ECS Fargate
//                               [FastAPI コンテナ + PostgreSQL サイドカー]
//
//   コスト最小化: NATなし / ALBなし / RDSなし（PGはサイドカー・データ揮発）
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
import * as servicediscovery from "aws-cdk-lib/aws-servicediscovery";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import * as logs from "aws-cdk-lib/aws-logs";
import * as path from "path";

export class DemoStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ------------------------------------------------------------
    // 1. VPC（パブリックサブネットのみ・NATなしでコスト0）
    //    Fargate は assignPublicIp でイメージを取得する
    // ------------------------------------------------------------
    const vpc = new ec2.Vpc(this, "Vpc", {
      maxAzs: 2,
      natGateways: 0,
      subnetConfiguration: [
        { name: "public", subnetType: ec2.SubnetType.PUBLIC },
      ],
    });

    // ------------------------------------------------------------
    // 2. ECS クラスタ + Cloud Map 名前空間（VPC Link のターゲット）
    // ------------------------------------------------------------
    const cluster = new ecs.Cluster(this, "Cluster", { vpc });
    const namespace = cluster.addDefaultCloudMapNamespace({
      name: "demo.local",
    });

    // JWT 秘密鍵は Secrets Manager で自動生成（コードに書かない）
    const jwtSecret = new secretsmanager.Secret(this, "JwtSecret", {
      description: "sons02-demo01 JWT secret",
      generateSecretString: { excludePunctuation: true, passwordLength: 48 },
    });

    const logGroup = new logs.LogGroup(this, "Logs", {
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // ------------------------------------------------------------
    // 3. タスク定義: FastAPI + PostgreSQL サイドカー（同一タスク内 = localhost 通信）
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
        POSTGRES_PASSWORD: "ses_pass_demo", // 検証用（タスク内 localhost のみ、外部露出なし）
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

    // バックエンドイメージは sons02 でビルドして ECR に push 済みのものを参照
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
        ADMIN_PASSWORD: "Demo2026!", // 検証用。README 参照
        CORS_ORIGINS: "http://localhost", // 同一オリジン構成のため CORS は実質不使用
      },
      secrets: {
        JWT_SECRET: ecs.Secret.fromSecretsManager(jwtSecret),
      },
      portMappings: [{ containerPort: 8000 }],
      logging: ecs.LogDrivers.awsLogs({ streamPrefix: "api", logGroup }),
    });

    // DB が healthy になってから API を起動（entrypoint.sh の待機と二重の保険）
    apiContainer.addContainerDependencies({
      container: dbContainer,
      condition: ecs.ContainerDependencyCondition.HEALTHY,
    });

    // ------------------------------------------------------------
    // 4. Fargate サービス + Cloud Map(SRV) 登録
    // ------------------------------------------------------------
    const serviceSg = new ec2.SecurityGroup(this, "ServiceSg", {
      vpc,
      description: "Fargate service SG",
      allowAllOutbound: true,
    });

    const service = new ecs.FargateService(this, "Service", {
      cluster,
      taskDefinition: taskDef,
      desiredCount: 1,
      assignPublicIp: true, // NATなしでECR/公開レジストリからpullするため
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      securityGroups: [serviceSg],
      cloudMapOptions: {
        name: "api",
        cloudMapNamespace: namespace,
        dnsRecordType: servicediscovery.DnsRecordType.SRV,
        container: apiContainer,
        containerPort: 8000,
      },
      minHealthyPercent: 0, // 検証用: 1タスク構成なので置き換え時は一旦0でよい
    });

    // ------------------------------------------------------------
    // 5. HTTP API Gateway + VPC Link → Cloud Map（ALB不要でコスト0）
    // ------------------------------------------------------------
    const vpcLinkSg = new ec2.SecurityGroup(this, "VpcLinkSg", {
      vpc,
      description: "API GW VPC Link SG",
      allowAllOutbound: true,
    });
    // SG の連鎖: VPC Link からのみ 8000 を許可（IP直書きしない）
    serviceSg.addIngressRule(vpcLinkSg, ec2.Port.tcp(8000), "from VPC Link");

    const vpcLink = new apigwv2.VpcLink(this, "VpcLink", {
      vpc,
      subnets: { subnetType: ec2.SubnetType.PUBLIC },
      securityGroups: [vpcLinkSg],
    });

    const httpApi = new apigwv2.HttpApi(this, "HttpApi", {
      apiName: "sons02-demo01-api",
    });

    httpApi.addRoutes({
      path: "/api/{proxy+}",
      methods: [apigwv2.HttpMethod.ANY],
      integration: new HttpServiceDiscoveryIntegration(
        "Backend",
        service.cloudMapService!,
        { vpcLink }
      ),
    });

    // ------------------------------------------------------------
    // 6. S3（プライベート + OAC） + CloudFront
    // ------------------------------------------------------------
    const siteBucket = new s3.Bucket(this, "SiteBucket", {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // 検証用: destroy で消す
      autoDeleteObjects: true,
    });

    // API GW のドメイン部分だけ取り出す（https://xxx.execute-api... → xxx.execute-api...）
    const apiDomain = cdk.Fn.select(2, cdk.Fn.split("/", httpApi.apiEndpoint));

    const distribution = new cloudfront.Distribution(this, "Distribution", {
      comment: "sons02-demo01 (B-plan practice)",
      defaultRootObject: "index.html",
      defaultBehavior: {
        // LIST 権限も付与 → 存在しないキーは 403 でなく 404 になり SPA フォールバックが正しく効く
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
            // 本番では API GW 側でこのヘッダを検証して「CloudFront経由以外」を遮断する
            customHeaders: { "x-origin-verify": "demo-secret-change-me" },
          }),
          viewerProtocolPolicy:
            cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
          cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
          originRequestPolicy:
            cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        },
      },
      // SPA ルーティング: 未知パスは index.html を 200 で返す
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
    // 7. フロントエンド資産のデプロイ（frontend/dist を事前ビルドしておくこと）
    // ------------------------------------------------------------
    new s3deploy.BucketDeployment(this, "DeploySite", {
      sources: [s3deploy.Source.asset(path.join(__dirname, "../../frontend/dist"))],
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
      description: "API GW 直エンドポイント（本番では直アクセス遮断対象）",
    });
    new cdk.CfnOutput(this, "AdminLogin", {
      value: "admin@example.com / Demo2026!",
      description: "検証用管理者ログイン",
    });
  }
}
