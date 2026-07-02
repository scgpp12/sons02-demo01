#!/usr/bin/env node
// CDK アプリのエントリポイント
// 個人検証環境（603319838936 / 東京リージョン）に B案アーキテクチャを構築する
import * as cdk from "aws-cdk-lib";
import { DemoStack } from "../lib/demo-stack";

const app = new cdk.App();

new DemoStack(app, "Sons02Demo01", {
  env: {
    account: "603319838936",
    region: "ap-northeast-1",
  },
  description: "SBR B-plan practice: CloudFront+S3(SPA) + API GW + VPC Link + Fargate(FastAPI+PG)",
});
