import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Save } from "lucide-react";
import { useEffect, useState } from "react";

import { errMessage } from "@/api/client";
import { contractsApi, listWorkRecords, upsertWorkRecord } from "@/api/endpoints";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { thisMonthStart, yen } from "@/lib/utils";

export function WorkRecordsPage() {
  const qc = useQueryClient();
  const [month, setMonth] = useState(thisMonthStart().slice(0, 7));
  const ym = `${month}-01`;
  const [hours, setHours] = useState<Record<number, string>>({});
  const [savedId, setSavedId] = useState<number | null>(null);

  // 契約中の契約のみ対象
  const { data: contracts } = useQuery({
    queryKey: ["contracts", "active-for-work"],
    queryFn: () => contractsApi.list({ page: 1, page_size: 300, status: "契約中" }),
  });
  const { data: records } = useQuery({
    queryKey: ["work-records", ym],
    queryFn: () => listWorkRecords({ year_month: ym, page: 1, page_size: 300 }),
  });

  // 既存実績をフォームへ流し込み
  useEffect(() => {
    if (!records) return;
    const map: Record<number, string> = {};
    for (const r of records.items) {
      map[r.contract_id] = String(r.worked_hours);
    }
    setHours(map);
  }, [records]);

  const save = useMutation({
    mutationFn: (contractId: number) =>
      upsertWorkRecord({
        contract_id: contractId,
        year_month: ym,
        worked_hours: Number(hours[contractId] ?? 0),
      }),
    onSuccess: (_data, contractId) => {
      setSavedId(contractId);
      setTimeout(() => setSavedId(null), 1500);
      qc.invalidateQueries({ queryKey: ["work-records"] });
    },
    onError: (e) => alert(errMessage(e)),
  });

  return (
    <div>
      <PageHeader title="稼働実績入力" />
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle>契約×対象月で稼働時間を入力</CardTitle>
          <Input
            type="month"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            className="max-w-[160px]"
          />
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>契約</TableHead>
                <TableHead>種別</TableHead>
                <TableHead>技術者</TableHead>
                <TableHead>契約相手</TableHead>
                <TableHead>単価</TableHead>
                <TableHead>精算幅</TableHead>
                <TableHead className="w-40">稼働時間(h)</TableHead>
                <TableHead className="text-right">保存</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {contracts && contracts.items.length > 0 ? (
                contracts.items.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell>#{c.id}</TableCell>
                    <TableCell>
                      <Badge variant={c.contract_type === "上位" ? "default" : "secondary"}>
                        {c.contract_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-medium">{c.engineer_name}</TableCell>
                    <TableCell>{c.counterparty_name ?? "-"}</TableCell>
                    <TableCell>{yen(c.unit_price)}</TableCell>
                    <TableCell className="text-xs">
                      {c.settlement_lower ?? "-"}〜{c.settlement_upper ?? "-"}h
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        step="0.5"
                        value={hours[c.id] ?? ""}
                        onChange={(e) => setHours({ ...hours, [c.id]: e.target.value })}
                      />
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => save.mutate(c.id)}
                        disabled={save.isPending}
                      >
                        <Save className="h-4 w-4" />
                        {savedId === c.id ? "保存済" : "保存"}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                    契約中の契約がありません
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
