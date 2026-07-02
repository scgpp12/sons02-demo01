// =====================================================================
// WAF スタック
// CloudFront 用の WebACL は「Global (CloudFront) スコープ」= us-east-1 に
// 作る必要があるため、本体スタック（東京）とは別スタックにしている。
// crossRegionReferences で ARN を東京側スタックへ渡す。
//
// ルール構成:
//   0. (任意) IP許可リスト — cdk.json の "allowedIps" に配列を入れると有効化
//   1. AWSManagedRulesCommonRuleSet      (コア保護)
//   2. AWSManagedRulesKnownBadInputsRuleSet (既知の悪性入力)
//   3. レートリミット: 同一IPから 5分間に 2000 リクエスト超で遮断
// =====================================================================
import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as wafv2 from "aws-cdk-lib/aws-wafv2";

export class WafStack extends cdk.Stack {
  public readonly webAclArn: string;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const rules: wafv2.CfnWebACL.RuleProperty[] = [];

    // --- 任意: IP 許可リスト（"開關"）。cdk.json context の allowedIps で ON ---
    const allowedIps: string[] | undefined =
      this.node.tryGetContext("allowedIps");
    if (allowedIps && allowedIps.length > 0) {
      const ipSet = new wafv2.CfnIPSet(this, "AllowedIpSet", {
        scope: "CLOUDFRONT",
        ipAddressVersion: "IPV4",
        addresses: allowedIps, // 例: ["203.0.113.10/32"]
        name: "sons02-demo01-allowed-ips",
      });
      rules.push({
        name: "AllowListedIpsOnly",
        priority: 0,
        statement: {
          notStatement: {
            statement: {
              ipSetReferenceStatement: { arn: ipSet.attrArn },
            },
          },
        },
        action: { block: {} },
        visibilityConfig: {
          cloudWatchMetricsEnabled: true,
          metricName: "AllowListedIpsOnly",
          sampledRequestsEnabled: true,
        },
      });
    }

    // --- AWS マネージドルール（追加料金なしの基本セット） ---
    rules.push(
      {
        name: "AWSManagedRulesCommonRuleSet",
        priority: 1,
        statement: {
          managedRuleGroupStatement: {
            vendorName: "AWS",
            name: "AWSManagedRulesCommonRuleSet",
          },
        },
        overrideAction: { none: {} },
        visibilityConfig: {
          cloudWatchMetricsEnabled: true,
          metricName: "CommonRuleSet",
          sampledRequestsEnabled: true,
        },
      },
      {
        name: "AWSManagedRulesKnownBadInputsRuleSet",
        priority: 2,
        statement: {
          managedRuleGroupStatement: {
            vendorName: "AWS",
            name: "AWSManagedRulesKnownBadInputsRuleSet",
          },
        },
        overrideAction: { none: {} },
        visibilityConfig: {
          cloudWatchMetricsEnabled: true,
          metricName: "KnownBadInputs",
          sampledRequestsEnabled: true,
        },
      },
      // --- レートリミット（Gemini 等の従量課金 API の暴走・悪用対策の一層目） ---
      {
        name: "RateLimitPerIp",
        priority: 3,
        statement: {
          rateBasedStatement: {
            limit: 2000, // 5分間あたり/IP
            aggregateKeyType: "IP",
          },
        },
        action: { block: {} },
        visibilityConfig: {
          cloudWatchMetricsEnabled: true,
          metricName: "RateLimitPerIp",
          sampledRequestsEnabled: true,
        },
      }
    );

    const webAcl = new wafv2.CfnWebACL(this, "WebAcl", {
      scope: "CLOUDFRONT",
      defaultAction: { allow: {} },
      name: "sons02-demo01-waf",
      rules,
      visibilityConfig: {
        cloudWatchMetricsEnabled: true,
        metricName: "sons02Demo01Waf",
        sampledRequestsEnabled: true,
      },
    });

    this.webAclArn = webAcl.attrArn;

    new cdk.CfnOutput(this, "WebAclArn", { value: this.webAclArn });
  }
}
