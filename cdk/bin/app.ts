#!/usr/bin/env node
// CDK アプリのエントリポイント
// - WafStack : us-east-1（CloudFront 用 WebACL はグローバルスコープのため）
// - DemoStack: ap-northeast-1（本体）
import * as cdk from "aws-cdk-lib";
import { DemoStack } from "../lib/demo-stack";
import { WafStack } from "../lib/waf-stack";

const app = new cdk.App();
const account = "603319838936";

const wafStack = new WafStack(app, "Sons02Demo01Waf", {
  env: { account, region: "us-east-1" },
  crossRegionReferences: true,
  description: "WAF WebACL (CloudFront scope) for sons02-demo01",
});

new DemoStack(app, "Sons02Demo01", {
  env: { account, region: "ap-northeast-1" },
  crossRegionReferences: true,
  webAclArn: wafStack.webAclArn,
  description:
    "SBR B-plan practice: CloudFront+WAF+S3(SPA) + API GW + VPC Link + Fargate(private) (FastAPI+PG)",
});
