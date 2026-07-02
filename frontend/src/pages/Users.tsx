import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Navigate } from "react-router-dom";

import { errMessage } from "@/api/client";
import { usersApi } from "@/api/endpoints";
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
import { useAuth } from "@/hooks/useAuth";
import { userRoleOptions } from "@/lib/options";
import type { AppUser } from "@/types";

const PAGE_SIZE = 20;

const emptyForm = { email: "", name: "", role: "sales", password: "", is_active: true };

export function UsersPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<AppUser | null>(null);
  const [form, setForm] = useState({ ...emptyForm });
  const [error, setError] = useState("");

  const params = { page, page_size: PAGE_SIZE };
  const { data, isLoading } = useQuery({
    queryKey: ["users", params],
    queryFn: () => usersApi.list(params),
    enabled: user?.role === "admin",
  });

  const save = useMutation({
    mutationFn: () => {
      if (editing) {
        const payload: Record<string, unknown> = {
          name: form.name,
          role: form.role,
          is_active: form.is_active,
        };
        if (form.password) payload.password = form.password;
        return usersApi.update(editing.id, payload);
      }
      return usersApi.create({
        email: form.email,
        name: form.name,
        role: form.role,
        password: form.password,
        is_active: form.is_active,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      setOpen(false);
    },
    onError: (e) => setError(errMessage(e)),
  });

  const del = useMutation({
    mutationFn: (id: number) => usersApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
    onError: (e) => alert(errMessage(e)),
  });

  if (user && user.role !== "admin") return <Navigate to="/" replace />;

  const openCreate = () => {
    setEditing(null);
    setForm({ ...emptyForm });
    setError("");
    setOpen(true);
  };
  const openEdit = (u: AppUser) => {
    setEditing(u);
    setForm({ email: u.email, name: u.name, role: u.role, password: "", is_active: u.is_active });
    setError("");
    setOpen(true);
  };

  return (
    <div>
      <PageHeader
        title="ユーザー管理"
        action={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" /> 新規登録
          </Button>
        }
      />

      <div className="rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>メール</TableHead>
              <TableHead>氏名</TableHead>
              <TableHead>権限</TableHead>
              <TableHead>状態</TableHead>
              <TableHead className="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
                  読み込み中...
                </TableCell>
              </TableRow>
            ) : data && data.items.length > 0 ? (
              data.items.map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-medium">{u.email}</TableCell>
                  <TableCell>{u.name}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">{u.role}</Badge>
                  </TableCell>
                  <TableCell>
                    {u.is_active ? (
                      <Badge variant="success">有効</Badge>
                    ) : (
                      <Badge variant="muted">無効</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon" onClick={() => openEdit(u)}>
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      disabled={u.id === user?.id}
                      onClick={() => {
                        if (confirm(`${u.email} を削除しますか？`)) del.mutate(u.id);
                      }}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
                  ユーザーがいません
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
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editing ? "ユーザーを編集" : "ユーザーを登録"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <Field label="メール" required>
              <Input
                type="email"
                value={form.email}
                disabled={!!editing}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </Field>
            <Field label="氏名" required>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </Field>
            <Field label="権限">
              <Select
                options={userRoleOptions}
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
              />
            </Field>
            <Field label={editing ? "パスワード（変更時のみ）" : "パスワード"} required={!editing}>
              <Input
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
            </Field>
            <Field label="状態">
              <label className="flex h-9 items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                />
                有効
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
                save.isPending || !form.name || !form.email || (!editing && !form.password)
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
