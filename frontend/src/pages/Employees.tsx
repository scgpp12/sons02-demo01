import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { errMessage } from "@/api/client";
import { employeesApi } from "@/api/endpoints";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { employeeStatusOptions, genderOptions, statusVariant } from "@/lib/options";
import { fmtDate } from "@/lib/utils";

const PAGE_SIZE = 20;

const emptyForm = {
  name: "",
  name_romaji: "",
  name_kana: "",
  birth_date: "",
  gender: "",
  nationality: "",
  mobile_phone: "",
  email: "",
  postal_code: "",
  address: "",
  hire_date: "",
  status: "在籍",
  note: "",
};

export function EmployeesPage() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ ...emptyForm });
  const [error, setError] = useState("");

  const params = {
    page,
    page_size: PAGE_SIZE,
    q: q || undefined,
    status: status || undefined,
  };
  const { data, isLoading } = useQuery({
    queryKey: ["employees", params],
    queryFn: () => employeesApi.list(params),
  });

  const save = useMutation({
    mutationFn: () =>
      employeesApi.create({
        ...form,
        gender: form.gender || null,
        mobile_phone: form.mobile_phone || null,
        email: form.email || null,
        postal_code: form.postal_code || null,
        address: form.address || null,
        hire_date: form.hire_date || null,
        note: form.note || null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["employees"] });
      setOpen(false);
    },
    onError: (e) => setError(errMessage(e)),
  });

  const del = useMutation({
    mutationFn: (id: number) => employeesApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["employees"] }),
    onError: (e) => alert(errMessage(e)),
  });

  const openCreate = () => {
    setForm({ ...emptyForm });
    setError("");
    setOpen(true);
  };

  return (
    <div>
      <PageHeader
        title="社員管理"
        action={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" /> 新規登録
          </Button>
        }
      />

      <div className="mb-3 flex flex-wrap gap-2">
        <Input
          placeholder="氏名・カナ・ローマ字で検索"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setPage(1);
          }}
          className="max-w-xs"
        />
        <Select
          options={employeeStatusOptions}
          placeholder="在籍状況（全て）"
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
              <TableHead>氏名</TableHead>
              <TableHead>国籍</TableHead>
              <TableHead>生年月日</TableHead>
              <TableHead>入社日</TableHead>
              <TableHead>在籍状況</TableHead>
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
              data.items.map((e) => (
                <TableRow key={e.id}>
                  <TableCell>
                    <div className="font-medium">{e.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {e.name_kana} / {e.name_romaji}
                    </div>
                  </TableCell>
                  <TableCell>{e.nationality}</TableCell>
                  <TableCell>{fmtDate(e.birth_date)}</TableCell>
                  <TableCell>{fmtDate(e.hire_date)}</TableCell>
                  <TableCell>
                    <Badge variant={statusVariant(e.status)}>{e.status}</Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon" onClick={() => navigate(`/employees/${e.id}`)}>
                      <Eye className="h-4 w-4" />
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
                <TableCell colSpan={6} className="py-8 text-center text-muted-foreground">
                  該当する社員がいません
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
            <DialogTitle>社員を登録</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4">
            <Field label="氏名(漢字)" required>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </Field>
            <Field label="氏名(ローマ字)" required>
              <Input
                value={form.name_romaji}
                onChange={(e) => setForm({ ...form, name_romaji: e.target.value })}
              />
            </Field>
            <Field label="フリガナ" required>
              <Input
                value={form.name_kana}
                onChange={(e) => setForm({ ...form, name_kana: e.target.value })}
              />
            </Field>
            <Field label="生年月日" required>
              <Input
                type="date"
                value={form.birth_date}
                onChange={(e) => setForm({ ...form, birth_date: e.target.value })}
              />
            </Field>
            <Field label="性別">
              <Select
                options={genderOptions}
                placeholder="選択"
                value={form.gender}
                onChange={(e) => setForm({ ...form, gender: e.target.value })}
              />
            </Field>
            <Field label="国籍" required>
              <Input
                value={form.nationality}
                onChange={(e) => setForm({ ...form, nationality: e.target.value })}
              />
            </Field>
            <Field label="携帯電話">
              <Input
                value={form.mobile_phone}
                onChange={(e) => setForm({ ...form, mobile_phone: e.target.value })}
              />
            </Field>
            <Field label="メール">
              <Input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </Field>
            <Field label="郵便番号">
              <Input
                value={form.postal_code}
                onChange={(e) => setForm({ ...form, postal_code: e.target.value })}
              />
            </Field>
            <Field label="入社日">
              <Input
                type="date"
                value={form.hire_date}
                onChange={(e) => setForm({ ...form, hire_date: e.target.value })}
              />
            </Field>
            <Field label="住所" className="col-span-2 space-y-1.5">
              <Input
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
              />
            </Field>
            <Field label="在籍状況">
              <Select
                options={employeeStatusOptions}
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
              />
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
                !form.name ||
                !form.name_romaji ||
                !form.name_kana ||
                !form.birth_date ||
                !form.nationality
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
