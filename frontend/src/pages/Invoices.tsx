import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Calculator } from "lucide-react";
import { useState } from "react";

import { errMessage } from "@/api/client";
import { generateInvoices, listInvoices, updateInvoice } from "@/api/endpoints";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { invoiceStatusOptions, statusVariant } from "@/lib/options";
import { fmtDate, fmtMonth, thisMonthStart, yen } from "@/lib/utils";

export function InvoicesPage() {
  const qc = useQueryClient();
  const [month, setMonth] = useState(thisMonthStart().slice(0, 7));
  const [statusFilter, setStatusFilter] = useState("");
  const ym = `${month}-01`;

  const { data, isLoading } = useQuery({
    queryKey: ["invoices", ym, statusFilter],
    queryFn: () =>
      listInvoices({
        year_month: ym,
        status: statusFilter || undefined,
        page: 1,
        page_size: 200,
      }),
  });

  const generate = useMutation({
    mutationFn: () => generateInvoices(ym),
    onSuccess: (rows) => {
      qc.invalidateQueries({ queryKey: ["invoices"] });
      alert(`${rows.length}件の請求を生成/再計算しました`);
    },
    onError: (e) => alert(errMessage(e)),
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => {
      const issued =
        status === "請求済" ? { issued_date: thisMonthStart().slice(0, 10) } : {};
      return updateInvoice(id, { status, ...issued });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["invoices"] }),
    onError: (e) => alert(errMessage(e)),
  });

  const total = data?.items.reduce((sum, i) => sum + i.billed_amount, 0) ?? 0;

  return (
    <div>
      <PageHeader title="請求" />
      <Card>
        <CardHeader className="flex-row flex-wrap items-center justify-between gap-2 space-y-0">
          <CardTitle>請求一覧（自動計算）</CardTitle>
          <div className="flex flex-wrap items-center gap-2">
            <Input
              type="month"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              className="max-w-[160px]"
            />
            <Select
              options={invoiceStatusOptions}
              placeholder="ステータス（全て）"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="max-w-[160px]"
            />
            <Button onClick={() => generate.mutate()} disabled={generate.isPending}>
              <Calculator className="h-4 w-4" /> 当月分を自動計算
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>対象月</TableHead>
                <TableHead>技術者</TableHead>
                <TableHead>請求先</TableHead>
                <TableHead>請求額</TableHead>
                <TableHead>発行日</TableHead>
                <TableHead>ステータス</TableHead>
                <TableHead className="text-right">変更</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                    読み込み中...
                  </TableCell>
                </TableRow>
              ) : data && data.items.length > 0 ? (
                data.items.map((inv) => (
                  <TableRow key={inv.id}>
                    <TableCell>{fmtMonth(inv.year_month)}</TableCell>
                    <TableCell className="font-medium">{inv.engineer_name}</TableCell>
                    <TableCell>{inv.counterparty_name ?? "-"}</TableCell>
                    <TableCell className="font-medium">{yen(inv.billed_amount)}</TableCell>
                    <TableCell>{fmtDate(inv.issued_date)}</TableCell>
                    <TableCell>
                      <Badge variant={statusVariant(inv.status)}>{inv.status}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Select
                        options={invoiceStatusOptions}
                        value={inv.status}
                        onChange={(e) =>
                          updateStatus.mutate({ id: inv.id, status: e.target.value })
                        }
                        className="ml-auto max-w-[130px]"
                      />
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                    請求がありません。「当月分を自動計算」で生成してください。
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
          {data && data.items.length > 0 && (
            <div className="flex justify-end pt-3 text-sm">
              <span className="font-medium">合計請求額：{yen(total)}</span>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
