import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Trash2, X } from "lucide-react";
import { useState } from "react";

import { errMessage } from "@/api/client";
import { clientsApi, projectsApi } from "@/api/endpoints";
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
import { projectStatusOptions, statusVariant } from "@/lib/options";
import { fmtDate, yen } from "@/lib/utils";
import type { Project, Skill } from "@/types";

const PAGE_SIZE = 20;

type FormState = {
  client_id: string;
  title: string;
  required_skills: Skill[];
  unit_price_min: string;
  unit_price_max: string;
  headcount: string;
  work_location: string;
  remote_ok: boolean;
  start_date: string;
  status: string;
  note: string;
};

const emptyForm: FormState = {
  client_id: "",
  title: "",
  required_skills: [],
  unit_price_min: "",
  unit_price_max: "",
  headcount: "1",
  work_location: "",
  remote_ok: false,
  start_date: "",
  status: "募集中",
  note: "",
};

export function ProjectsPage() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Project | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [error, setError] = useState("");

  const params = {
    page,
    page_size: PAGE_SIZE,
    q: q || undefined,
    status: status || undefined,
  };
  const { data, isLoading } = useQuery({
    queryKey: ["projects", params],
    queryFn: () => projectsApi.list(params),
  });
  const { data: clients } = useQuery({
    queryKey: ["clients", "all"],
    queryFn: () => clientsApi.list({ page: 1, page_size: 100 }),
  });
  const clientOptions =
    clients?.items.map((c) => ({ value: String(c.id), label: c.company_name })) ?? [];

  const save = useMutation({
    mutationFn: async () => {
      const payload = {
        client_id: Number(form.client_id),
        title: form.title,
        required_skills: form.required_skills,
        unit_price_min: form.unit_price_min ? Number(form.unit_price_min) : null,
        unit_price_max: form.unit_price_max ? Number(form.unit_price_max) : null,
        headcount: Number(form.headcount) || 1,
        work_location: form.work_location || null,
        remote_ok: form.remote_ok,
        start_date: form.start_date || null,
        status: form.status,
        note: form.note || null,
      };
      return editing ? projectsApi.update(editing.id, payload) : projectsApi.create(payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      setOpen(false);
    },
    onError: (e) => setError(errMessage(e)),
  });

  const del = useMutation({
    mutationFn: (id: number) => projectsApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
    onError: (e) => alert(errMessage(e)),
  });

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setError("");
    setOpen(true);
  };
  const openEdit = (p: Project) => {
    setEditing(p);
    setForm({
      client_id: String(p.client_id),
      title: p.title,
      required_skills: p.required_skills ?? [],
      unit_price_min: p.unit_price_min?.toString() ?? "",
      unit_price_max: p.unit_price_max?.toString() ?? "",
      headcount: String(p.headcount),
      work_location: p.work_location ?? "",
      remote_ok: p.remote_ok,
      start_date: p.start_date ?? "",
      status: p.status,
      note: p.note ?? "",
    });
    setError("");
    setOpen(true);
  };

  const addSkill = () =>
    setForm((f) => ({ ...f, required_skills: [...f.required_skills, { name: "", years: 0 }] }));
  const updateSkill = (i: number, key: keyof Skill, value: string) =>
    setForm((f) => {
      const required_skills = [...f.required_skills];
      required_skills[i] = {
        ...required_skills[i],
        [key]: key === "years" ? Number(value) : value,
      };
      return { ...f, required_skills };
    });
  const removeSkill = (i: number) =>
    setForm((f) => ({ ...f, required_skills: f.required_skills.filter((_, idx) => idx !== i) }));

  return (
    <div>
      <PageHeader
        title="案件"
        action={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" /> 新規登録
          </Button>
        }
      />

      <div className="mb-3 flex flex-wrap gap-2">
        <Input
          placeholder="案件名で検索"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setPage(1);
          }}
          className="max-w-xs"
        />
        <Select
          options={projectStatusOptions}
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
              <TableHead>案件名</TableHead>
              <TableHead>取引先</TableHead>
              <TableHead>単価レンジ</TableHead>
              <TableHead>人数</TableHead>
              <TableHead>開始</TableHead>
              <TableHead>ステータス</TableHead>
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
              data.items.map((p) => (
                <TableRow key={p.id}>
                  <TableCell className="font-medium">{p.title}</TableCell>
                  <TableCell>{p.client_name ?? "-"}</TableCell>
                  <TableCell className="text-xs">
                    {yen(p.unit_price_min)} 〜 {yen(p.unit_price_max)}
                  </TableCell>
                  <TableCell>{p.headcount}名</TableCell>
                  <TableCell>{fmtDate(p.start_date)}</TableCell>
                  <TableCell>
                    <Badge variant={statusVariant(p.status)}>{p.status}</Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon" onClick={() => openEdit(p)}>
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => {
                        if (confirm(`${p.title} を削除しますか？`)) del.mutate(p.id);
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
                  該当する案件がありません
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
            <DialogTitle>{editing ? "案件を編集" : "案件を登録"}</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4">
            <Field label="案件名" required className="col-span-2 space-y-1.5">
              <Input
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
              />
            </Field>
            <Field label="取引先" required>
              <Select
                options={clientOptions}
                placeholder="選択してください"
                value={form.client_id}
                onChange={(e) => setForm({ ...form, client_id: e.target.value })}
              />
            </Field>
            <Field label="ステータス">
              <Select
                options={projectStatusOptions}
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
              />
            </Field>
            <Field label="単価下限(円)">
              <Input
                type="number"
                value={form.unit_price_min}
                onChange={(e) => setForm({ ...form, unit_price_min: e.target.value })}
              />
            </Field>
            <Field label="単価上限(円)">
              <Input
                type="number"
                value={form.unit_price_max}
                onChange={(e) => setForm({ ...form, unit_price_max: e.target.value })}
              />
            </Field>
            <Field label="募集人数">
              <Input
                type="number"
                value={form.headcount}
                onChange={(e) => setForm({ ...form, headcount: e.target.value })}
              />
            </Field>
            <Field label="勤務地">
              <Input
                value={form.work_location}
                onChange={(e) => setForm({ ...form, work_location: e.target.value })}
              />
            </Field>
            <Field label="開始日">
              <Input
                type="date"
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
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
              <span className="text-sm font-medium">必要スキル</span>
              <Button variant="outline" size="sm" onClick={addSkill} type="button">
                <Plus className="h-3 w-3" /> 追加
              </Button>
            </div>
            {form.required_skills.map((s, i) => (
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
            <Button
              onClick={() => save.mutate()}
              disabled={save.isPending || !form.title || !form.client_id}
            >
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
