import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Link } from "react-router-dom";

import { fetchDashboard } from "@/api/endpoints";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { statusVariant } from "@/lib/options";
import { fmtDate, fmtMonth, percent, yen } from "@/lib/utils";

function Kpi({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="text-sm text-muted-foreground">{label}</div>
        <div className="mt-1 text-2xl font-bold">{value}</div>
        {sub && <div className="mt-0.5 text-xs text-muted-foreground">{sub}</div>}
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: fetchDashboard });

  if (isLoading || !data) {
    return (
      <div>
        <PageHeader title="ダッシュボード" />
        <p className="text-muted-foreground">読み込み中...</p>
      </div>
    );
  }

  const chartData = data.monthly_trend.map((m) => ({
    month: fmtMonth(m.year_month),
    売上: m.revenue,
    原価: m.cost,
    粗利: m.gross_profit,
  }));

  return (
    <div className="space-y-6">
      <PageHeader title="ダッシュボード" />

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Kpi
          label="稼働率"
          value={percent(data.utilization_rate)}
          sub={`稼働中 ${data.working_count} / 全 ${data.total_engineers} 名`}
        />
        <Kpi label="待機人数" value={`${data.waiting_count} 名`} />
        <Kpi label="今月売上" value={yen(data.this_month_revenue)} />
        <Kpi
          label="今月粗利"
          value={yen(data.this_month_gross_profit)}
          sub={`粗利率 ${percent(data.this_month_gross_margin)}`}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>月次売上・粗利</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="month" fontSize={12} />
                <YAxis fontSize={12} tickFormatter={(v) => `${v / 10000}万`} />
                <Tooltip formatter={(v: number) => yen(v)} />
                <Legend />
                <Bar dataKey="売上" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="原価" fill="#94a3b8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="粗利" fill="#22c55e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>技術者ステータス</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {data.engineer_status_breakdown.map((s) => (
              <div key={s.status} className="flex items-center justify-between">
                <Badge variant={statusVariant(s.status)}>{s.status}</Badge>
                <span className="font-medium">{s.count} 名</span>
              </div>
            ))}
            {data.engineer_status_breakdown.length === 0 && (
              <p className="text-sm text-muted-foreground">データがありません</p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            更新待ち契約アラート（1ヶ月以内に終了）
          </CardTitle>
        </CardHeader>
        <CardContent>
          {data.renewal_alerts.length > 0 ? (
            <ul className="divide-y">
              {data.renewal_alerts.map((a) => (
                <li key={a.contract_id} className="flex items-center justify-between py-2">
                  <div>
                    <Link to="/contracts" className="font-medium hover:underline">
                      #{a.contract_id} {a.engineer_name}
                    </Link>
                    <span className="ml-2 text-sm text-muted-foreground">
                      {a.counterparty_name ?? ""}
                    </span>
                  </div>
                  <div className="text-sm">
                    <span className="text-muted-foreground">終了 {fmtDate(a.end_date)}</span>
                    <Badge variant={a.days_left < 0 ? "danger" : "warning"} className="ml-2">
                      {a.days_left < 0 ? `${-a.days_left}日超過` : `残り${a.days_left}日`}
                    </Badge>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">更新待ちの契約はありません</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
