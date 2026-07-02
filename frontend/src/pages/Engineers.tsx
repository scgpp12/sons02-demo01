import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Trash2, X } from "lucide-react";
import { useState } from "react";

import { errMessage } from "@/api/client";
import { engineersApi } from "@/api/endpoints";
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
import { engineerStatusOptions, statusVariant } from "@/lib/options";
import { fmtDate, yen } from "@/lib/utils";
import type { Engineer, Skill } from "@/types";

const PAGE_SIZE = 20;

type FormState = {
  name: string;
  name_kana: string;
  email: string;
  phone: string;
  skills: Skill[];
  unit_price: string;
  status: string;
  available_from: string;
  remote_ok: boolean;
  note: string;
};

const emptyForm: FormState = {
  name: "",
  name_kana: "",
  email: "",
  phone: "",
  skills: [],
  unit_price: "",
  status: "待機",
  available_from: "",
  remote_ok: false,
  note: "",
};

function toForm(e: Engineer): FormState {
  return {
    name: e.name,
    name_kana: e.name_kana ?? "",
    email: e.email ?? "",
    phone: e.phone ?? "",
    skills: e.skills ?? [],
    unit_price: e.unit_price?.toString() ?? "",
    status: e.status,
    available_from: e.available_from ?? "",
    remote_ok: e.remote_ok,
    note: e.note ?? "",
  };
}

export function EngineersPage() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [skill, setSkill] = useState("");
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Engineer | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [error, setError] = useState("");

  const params = {
    page,
    page_size: PAGE_SIZE,
    q: q || undefined,
    status: status || undefined,
    skill: skill || undefined,
  };
  const { data, isLoading } = useQuery({
    queryKey: ["engineers", params],
    queryFn: () => engineersApi.list(params),
  });

  const save = useMutation({
    mutationFn: async () => {
      const payload = {
        name: form.name,
        name_kana: form.name_kana || null,
        email: form.email || null,
        phone: form.phone || null,
        skills: form.skills,
        unit_price: form.unit_price ? Number(form.unit_price) : null,
        status: form.status,
        available_from: form.available_from || null,
        remote_ok: form.remote_ok,
        note: form.note || null,
      };
      return editing ? engineersApi.update(editing.id, payload) : engineersApi.create(payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["engineers"] });
      setOpen(false);
    },
    onError: (e) => setError(errMessage(e)),
  });

  const del = useMutation({
    mutationFn: (id: number) => engineersApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["engineers"] }),
    onError: (e) => alert(errMessage(e)),
  });

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setError("");
    setOpen(true);
  };
  const openEdit = (e: Engineer) => {
    setEditing(e);
    setForm(toForm(e));
    setError("");
    setOpen(true);
  };

  const addSkill = () =>
    setForm((f) => ({ ...f, skills: [...f.skills, { name: "", years: 0 }] }));
  const updateSkill = (i: number, key: keyof Skill, value: string) =>
    setForm((f) => {
      const skills = [...f.skills];
      skills[i] = { ...skills[i], [key]: key === "years" ? Number(value) : value };
      return { ...f, skills };
    });
  const removeSkill = (i: number) =>
    setForm((f) => ({ ...f, skills: f.skills.filter((_, idx) => idx !== i) }));

  return (
    <div>
      <PageHeader
        title="技術者"
        action={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" /> 新規登録
          </Button>
        }
      />

      <div className="mb-3 flex flex-wrap gap-2">
        <Input
          placeholder="氏名・カナ・メールで検索"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setPage(1);
          }}
          className="max-w-xs"
        />
        <Select
          options={engineerStatusOptions}
          placeholder="ステータス（全て）"
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setPage(1);
          }}
          className="max-w-[180px]"
        />
        <Input
          placeholder="スキル名で絞り込み"
          value={skill}
          onChange={(e) => {
            setSkill(e.target.value);
            setPage(1);
          }}
          className="max-w-[180px]"
        />
      </div>

      <div className="rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>氏名</TableHead>
              <TableHead>スキル</TableHead>
              <TableHead>希望単価</TableHead>
              <TableHead>ステータス</TableHead>
              <TableHead>稼働可能</TableHead>
              <TableHead>リモート</TableHead>
              <TableHead className="text-right">操作</TableHead>
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
              data.items.map((e) => (
                <TableRow key={e.id}>
                  <TableCell>
                    <div className="font-medium">{e.name}</div>
                    <div className="text-xs text-muted-foreground">{e.name_kana}</div>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {e.skills.slice(0, 4).map((s, i) => (
                        <Badge key={i} variant="secondary">
                          {s.name} {s.years}年
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>{yen(e.unit_price)}</TableCell>
                  <TableCell>
                    <Badge variant={statusVariant(e.status)}>{e.status}</Badge>
                  </TableCell>
                  <TableCell>{fmtDate(e.available_from)}</TableCell>
                  <TableCell>{e.remote_ok ? "可" : "不可"}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon" onClick={() => openEdit(e)}>
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => {
                        if (confirm(`${e.name} を削除しますか？`)) del.mutate(e.id);
                      }}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                  該当する技術者がいません
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {data && (
        <Pagination
          page={page}
          pageSize={PAGE_SIZE}
          total={data.total}
          onPageChange={setPage}
        />
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? "技術者を編集" : "技術者を登録"}</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4">
            <Field label="氏名" required>
              <Input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </Field>
            <Field label="フリガナ">
              <Input
                value={form.name_kana}
                onChange={(e) => setForm({ ...form, name_kana: e.target.value })}
              />
            </Field>
            <Field label="メール">
              <Input
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </Field>
            <Field label="電話">
              <Input
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </Field>
            <Field label="希望単価(円)">
              <Input
                type="number"
                value={form.unit_price}
                onChange={(e) => setForm({ ...form, unit_price: e.target.value })}
              />
            </Field>
            <Field label="ステータス">
              <Select
                options={engineerStatusOptions}
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
              />
            </Field>
            <Field label="稼働可能時期">
              <Input
                type="date"
                value={form.available_from}
                onChange={(e) => setForm({ ...form, available_from: e.target.value })}
              />
            </Field>
            <Field label="リモート可否">
              <label className="flex h-9 items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.remote_ok}
                  onChange={(e) => setForm({ ...form, remote_ok: e.target.checked })}
                />
                リモート可
              </label>
            </Field>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">スキル</span>
              <Button variant="outline" size="sm" onClick={addSkill} type="button">
                <Plus className="h-3 w-3" /> 追加
              </Button>
            </div>
            {form.skills.map((s, i) => (
              <div key={i} className="flex items-center gap-2">
                <Input
                  placeholder="スキル名"
                  value={s.name}
                  onChange={(e) => updateSkill(i, "name", e.target.value)}
                />
                <Input
                  type="number"
                  placeholder="年数"
                  className="w-24"
                  value={s.years}
                  onChange={(e) => updateSkill(i, "years", e.target.value)}
                />
                <Button variant="ghost" size="icon" type="button" onClick={() => removeSkill(i)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
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
            <Button onClick={() => save.mutate()} disabled={save.isPending || !form.name}>
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
