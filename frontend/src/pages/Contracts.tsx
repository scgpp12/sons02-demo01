import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { errMessage } from "@/api/client";
import {
  clientsApi,
  contractsApi,
  engineersApi,
  fetchGrossProfit,
  fetchUpperContracts,
  projectsApi,
} from "@/api/endpoints";
import { Field } from "@/components/Field";
import { PageHeader } from "@/components/PageHeader";
import { Pagination } from "@/components/Pagination";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import {
  contractStatusOptions,
  contractTypeOptions,
  statusVariant,
} from "@/lib/options";
import { fmtDate, fmtMonth, percent, thisMonthStart, yen } from "@/lib/utils";
import type { Contract } from "@/types";

const PAGE_SIZE = 20;

type FormState = {
  engineer_id: string;
  contract_type: string;
  counterparty_client_id: string;
  parent_contract_id: string;
  project_id: string;
  unit_price: string;
  settlement_lower: string;
  settlement_upper: string;
  overtime_rate: string;
  deduction_rate: string;
  start_date: string;
  end_date: string;
  auto_renew: boolean;
  status: string;
};

const emptyForm: FormState = {
  engineer_id: "",
  contract_type: "上位",
  counterparty_client_id: "",
  parent_contract_id: "",
  project_id: "",
  unit_price: "",
  settlement_lower: "140",
  settlement_upper: "180",
  overtime_rate: "0",
  deduction_rate: "0",
  start_date: "",
  end_date: "",
  auto_renew: false,
  status: "契約中",
};

export function ContractsPage() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [type, setType] = useState("");
  const [status, setStatus] = useState("");
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Contract | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [error, setError] = useState("");
  const [gpMonth, setGpMonth] = useState(thisMonthStart().slice(0, 7));

  const params = {
    page,
    page_size: PAGE_SIZE,
    contract_type: type || undefined,
    status: status || undefined,
  };
  const { data, isLoading } = useQuery({
    queryKey: ["contracts", params],
    queryFn: () => contractsApi.list(params),
  });
  const { data: engineers } = useQuery({
    queryKey: ["engineers", "all"],
    queryFn: () => engineersApi.list({ page: 1, page_size: 200 }),
  });
  const { data: clients } = useQuery({
    queryKey: ["clients", "all"],
    queryFn: () => clientsApi.list({ page: 1, page_size: 200 }),
  });
  const { data: projects } = useQuery({
    queryKey: ["projects", "all"],
    queryFn: () => projectsApi.list({ page: 1, page_size: 200 }),
  });
  const { data: uppers } = useQuery({
    queryKey: ["contracts", "uppers"],
    queryFn: fetchUpperContracts,
  });
  const { data: grossProfit } = useQuery({
    queryKey: ["gross-profit", gpMonth],
    queryFn: () => fetchGrossProfit(`${gpMonth}-01`),
  });

  const engineerOptions =
    engineers?.items.map((e) => ({ value: String(e.id), label: e.name })) ?? [];
  const clientOptions =
    clients?.items.map((c) => ({ value: String(c.id), label: c.company_name })) ?? [];
  const projectOptions =
    projects?.items.map((p) => ({ value: String(p.id), label: p.title })) ?? [];
  const upperOptions =
    uppers?.map((u) => ({
      value: String(u.id),
      label: `#${u.id} ${u.engineer_name ?? ""} / ${u.counterparty_name ?? ""}`,
    })) ?? [];

  const save = useMutation({
    mutationFn: async () => {
      const payload = {
        engineer_id: Number(form.engineer_id),
        contract_type: form.contract_type,
        counterparty_client_id: form.counterparty_client_id
          ? Number(form.counterparty_client_id)
          : null,
        parent_contract_id:
          form.contract_type === "下位" && form.parent_contract_id
            ? Number(form.parent_contract_id)
            : null,
        project_id: form.project_id ? Number(form.project_id) : null,
        unit_price: Number(form.unit_price),
        settlement_lower: form.settlement_lower ? Number(form.settlement_lower) : null,
        settlement_upper: form.settlement_upper ? Number(form.settlement_upper) : null,
        overtime_rate: Number(form.overtime_rate) || 0,
        deduction_rate: Number(form.deduction_rate) || 0,
        start_date: form.start_date,
        end_date: form.end_date,
        auto_renew: form.auto_renew,
        status: form.status,
      };
      return editing ? contractsApi.update(editing.id, payload) : contractsApi.create(payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["contracts"] });
      qc.invalidateQueries({ queryKey: ["gross-profit"] });
      setOpen(false);
    },
    onError: (e) => setError(errMessage(e)),
  });

  const del = useMutation({
    mutationFn: (id: number) => contractsApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["contracts"] }),
    onError: (e) => alert(errMessage(e)),
  });

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setError("");
    setOpen(true);
  };
  const openEdit = (c: Contract) => {
    setEditing(c);
    setForm({
      engineer_id: String(c.engineer_id),
      contract_type: c.contract_type,
      counterparty_client_id: c.counterparty_client_id?.toString() ?? "",
      parent_contract_id: c.parent_contract_id?.toString() ?? "",
      project_id: c.project_id?.toString() ?? "",
      unit_price: String(c.unit_price),
      settlement_lower: c.settlement_lower?.toString() ?? "",
      settlement_upper: c.settlement_upper?.toString() ?? "",
      overtime_rate: String(c.overtime_rate),
      deduction_rate: String(c.deduction_rate),
      start_date: c.start_date,
      end_date: c.end_date,
      auto_renew: c.auto_renew,
      status: c.status,
    });
    setError("");
    setOpen(true);
  };

  return (
    <div className="space-y-6">
      <div>
        <PageHeader
          title="契約"
          action={
            <Button onClick={openCreate}>
              <Plus className="h-4 w-4" /> 新規登録
            </Button>
          }
        />

        <div className="mb-3 flex flex-wrap gap-2">
          <Select
            options={contractTypeOptions}
            placeholder="種別（全て）"
            value={type}
            onChange={(e) => {
              setType(e.target.value);
              setPage(1);
            }}
            className="max-w-[180px]"
          />
          <Select
            options={contractStatusOptions}
            placeholder="ステータス（全て）"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="max-w-[180px]"
          />
        </div>

        <div className="rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>種別</TableHead>
                <TableHead>技術者</TableHead>
                <TableHead>契約相手</TableHead>
                <TableHead>単価</TableHead>
                <TableHead>精算幅</TableHead>
                <TableHead>期間</TableHead>
                <TableHead>紐づけ</TableHead>
                <TableHead>ステータス</TableHead>
                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={10} className="py-8 text-center text-muted-foreground">
                    読み込み中...
                  </TableCell>
                </TableRow>
              ) : data && data.items.length > 0 ? (
                data.items.map((c) => (
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
                    <TableCell className="text-xs">
                      {fmtDate(c.start_date)}〜{fmtDate(c.end_date)}
                    </TableCell>
                    <TableCell className="text-xs">
                      {c.parent_contract_id ? `上位 #${c.parent_contract_id}` : "-"}
                    </TableCell>
                    <TableCell>
                      <Badge variant={statusVariant(c.status)}>{c.status}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="icon" onClick={() => openEdit(c)}>
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => {
                          if (confirm(`契約 #${c.id} を削除しますか？`)) del.mutate(c.id);
                        }}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={10} className="py-8 text-center text-muted-foreground">
                    該当する契約がありません
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        {data && (
          <Pagination page={page} pageSize={PAGE_SIZE} total={data.total} onPageChange={setPage} />
        )}
      </div>

      {/* 粗利パネル */}
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle>粗利（技術者×対象月）</CardTitle>
          <Input
            type="month"
            value={gpMonth}
            onChange={(e) => setGpMonth(e.target.value)}
            className="max-w-[160px]"
          />
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>技術者</TableHead>
                <TableHead>対象月</TableHead>
                <TableHead>上位請求</TableHead>
                <TableHead>下位支払</TableHead>
                <TableHead>粗利</TableHead>
                <TableHead>粗利率</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {grossProfit && grossProfit.length > 0 ? (
                grossProfit.map((g) => (
                  <TableRow key={g.upper_contract_id}>
                    <TableCell className="font-medium">{g.engineer_name}</TableCell>
                    <TableCell>{fmtMonth(g.year_month)}</TableCell>
                    <TableCell>{yen(g.upper_billed)}</TableCell>
                    <TableCell>
                      {yen(g.lower_paid)}
                      {g.lower_count > 1 && (
                        <span className="ml-1 text-xs text-muted-foreground">
                          （下位{g.lower_count}件合算）
                        </span>
                      )}
                    </TableCell>
                    <TableCell className={g.gross_profit < 0 ? "text-destructive" : "text-green-700"}>
                      {yen(g.gross_profit)}
                    </TableCell>
                    <TableCell>{percent(g.gross_margin)}</TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={6} className="py-6 text-center text-muted-foreground">
                    対象月の上位契約がありません
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 契約フォーム */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? "契約を編集" : "契約を登録"}</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4">
            <Field label="技術者" required>
              <Select
                options={engineerOptions}
                placeholder="選択してください"
                value={form.engineer_id}
                onChange={(e) => setForm({ ...form, engineer_id: e.target.value })}
              />
            </Field>
            <Field label="種別" required>
              <Select
                options={contractTypeOptions}
                value={form.contract_type}
                onChange={(e) => setForm({ ...form, contract_type: e.target.value })}
              />
            </Field>
            <Field label="契約相手（取引先）">
              <Select
                options={clientOptions}
                placeholder="選択してください"
                value={form.counterparty_client_id}
                onChange={(e) => setForm({ ...form, counterparty_client_id: e.target.value })}
              />
            </Field>
            <Field label="案件（任意）">
              <Select
                options={projectOptions}
                placeholder="選択してください"
                value={form.project_id}
                onChange={(e) => setForm({ ...form, project_id: e.target.value })}
              />
            </Field>
            {form.contract_type === "下位" && (
              <Field label="紐づく上位契約" className="col-span-2 space-y-1.5">
                <Select
                  options={upperOptions}
                  placeholder="上位契約を選択（粗利算出に使用）"
                  value={form.parent_contract_id}
                  onChange={(e) => setForm({ ...form, parent_contract_id: e.target.value })}
                />
              </Field>
            )}
            <Field label="月額単価(円)" required>
              <Input
                type="number"
                value={form.unit_price}
                onChange={(e) => setForm({ ...form, unit_price: e.target.value })}
              />
            </Field>
            <Field label="ステータス">
              <Select
                options={contractStatusOptions}
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
              />
            </Field>
            <Field label="精算下限(h)">
              <Input
                type="number"
                value={form.settlement_lower}
                onChange={(e) => setForm({ ...form, settlement_lower: e.target.value })}
              />
            </Field>
            <Field label="精算上限(h)">
              <Input
                type="number"
                value={form.settlement_upper}
                onChange={(e) => setForm({ ...form, settlement_upper: e.target.value })}
              />
            </Field>
            <Field label="超過単価(円/h)">
              <Input
                type="number"
                value={form.overtime_rate}
                onChange={(e) => setForm({ ...form, overtime_rate: e.target.value })}
              />
            </Field>
            <Field label="控除単価(円/h)">
              <Input
                type="number"
                value={form.deduction_rate}
                onChange={(e) => setForm({ ...form, deduction_rate: e.target.value })}
              />
            </Field>
            <Field label="開始日" required>
              <Input
                type="date"
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
              />
            </Field>
            <Field label="終了日" required>
              <Input
                type="date"
                value={form.end_date}
                onChange={(e) => setForm({ ...form, end_date: e.target.value })}
              />
            </Field>
            <Field label="自動更新">
              <label className="flex h-9 items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.auto_renew}
                  onChange={(e) => setForm({ ...form, auto_renew: e.target.checked })}
                />
                自動更新する
              </label>
            </Field>
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)} type="button">
              キャンセル
            </Button>
            <Button
              onClick={() => save.mutate()}
              disabled={
                save.isPending ||
                !form.engineer_id ||
                !form.unit_price ||
                !form.start_date ||
                !form.end_date
              }
            >
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
