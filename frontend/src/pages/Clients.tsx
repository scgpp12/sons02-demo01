import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { errMessage } from "@/api/client";
import { clientsApi } from "@/api/endpoints";
import { Field } from "@/components/Field";
import { PageHeader } from "@/components/PageHeader";
import { Pagination } from "@/components/Pagination";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { businessTypeOptions } from "@/lib/options";
import type { Client } from "@/types";

const PAGE_SIZE = 20;

type FormState = {
  company_name: string;
  business_type: string;
  contact_name: string;
  contact_email: string;
  contact_phone: string;
  can_distribute: boolean;
  note: string;
};

const emptyForm: FormState = {
  company_name: "",
  business_type: "エンド",
  contact_name: "",
  contact_email: "",
  contact_phone: "",
  can_distribute: true,
  note: "",
};

export function ClientsPage() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [bizType, setBizType] = useState("");
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Client | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [error, setError] = useState("");

  const params = {
    page,
    page_size: PAGE_SIZE,
    q: q || undefined,
    business_type: bizType || undefined,
  };
  const { data, isLoading } = useQuery({
    queryKey: ["clients", params],
    queryFn: () => clientsApi.list(params),
  });

  const save = useMutation({
    mutationFn: async () => {
      const payload = {
        company_name: form.company_name,
        business_type: form.business_type,
        contact_name: form.contact_name || null,
        contact_email: form.contact_email || null,
        contact_phone: form.contact_phone || null,
        can_distribute: form.can_distribute,
        note: form.note || null,
      };
      return editing ? clientsApi.update(editing.id, payload) : clientsApi.create(payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["clients"] });
      setOpen(false);
    },
    onError: (e) => setError(errMessage(e)),
  });

  const del = useMutation({
    mutationFn: (id: number) => clientsApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["clients"] }),
    onError: (e) => alert(errMessage(e)),
  });

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setError("");
    setOpen(true);
  };
  const openEdit = (c: Client) => {
    setEditing(c);
    setForm({
      company_name: c.company_name,
      business_type: c.business_type,
      contact_name: c.contact_name ?? "",
      contact_email: c.contact_email ?? "",
      contact_phone: c.contact_phone ?? "",
      can_distribute: c.can_distribute,
      note: c.note ?? "",
    });
    setError("");
    setOpen(true);
  };

  return (
    <div>
      <PageHeader
        title="取引先・BP"
        action={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" /> 新規登録
          </Button>
        }
      />

      <div className="mb-3 flex flex-wrap gap-2">
        <Input
          placeholder="会社名・担当者名で検索"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setPage(1);
          }}
          className="max-w-xs"
        />
        <Select
          options={businessTypeOptions}
          placeholder="区分（全て）"
          value={bizType}
          onChange={(e) => {
            setBizType(e.target.value);
            setPage(1);
          }}
          className="max-w-[180px]"
        />
      </div>

      <div className="rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>会社名</TableHead>
              <TableHead>区分</TableHead>
              <TableHead>担当者</TableHead>
              <TableHead>連絡先</TableHead>
              <TableHead>配信</TableHead>
              <TableHead className="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="py-8 text-center text-muted-foreground">
                  読み込み中...
                </TableCell>
              </TableRow>
            ) : data && data.items.length > 0 ? (
              data.items.map((c) => (
                <TableRow key={c.id}>
                  <TableCell className="font-medium">{c.company_name}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">{c.business_type}</Badge>
                  </TableCell>
                  <TableCell>{c.contact_name ?? "-"}</TableCell>
                  <TableCell className="text-xs">
                    <div>{c.contact_email}</div>
                    <div className="text-muted-foreground">{c.contact_phone}</div>
                  </TableCell>
                  <TableCell>{c.can_distribute ? "可" : "不可"}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon" onClick={() => openEdit(c)}>
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => {
                        if (confirm(`${c.company_name} を削除しますか？`)) del.mutate(c.id);
                      }}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} className="py-8 text-center text-muted-foreground">
                  該当する取引先がいません
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {data && (
        <Pagination page={page} pageSize={PAGE_SIZE} total={data.total} onPageChange={setPage} />
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? "取引先を編集" : "取引先を登録"}</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4">
            <Field label="会社名" required>
              <Input
                value={form.company_name}
                onChange={(e) => setForm({ ...form, company_name: e.target.value })}
              />
            </Field>
            <Field label="区分" required>
              <Select
                options={businessTypeOptions}
                value={form.business_type}
                onChange={(e) => setForm({ ...form, business_type: e.target.value })}
              />
            </Field>
            <Field label="担当者名">
              <Input
                value={form.contact_name}
                onChange={(e) => setForm({ ...form, contact_name: e.target.value })}
              />
            </Field>
            <Field label="担当メール">
              <Input
                value={form.contact_email}
                onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
              />
            </Field>
            <Field label="担当電話">
              <Input
                value={form.contact_phone}
                onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
              />
            </Field>
            <Field label="配信可否">
              <label className="flex h-9 items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.can_distribute}
                  onChange={(e) => setForm({ ...form, can_distribute: e.target.checked })}
                />
                配信可
              </label>
            </Field>
          </div>
          <Field label="備考">
            <Textarea
              value={form.note}
              onChange={(e) => setForm({ ...form, note: e.target.value })}
            />
          </Field>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)} type="button">
              キャンセル
            </Button>
            <Button onClick={() => save.mutate()} disabled={save.isPending || !form.company_name}>
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
