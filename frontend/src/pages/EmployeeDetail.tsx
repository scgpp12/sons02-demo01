import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus, ShieldAlert, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { errMessage } from "@/api/client";
import {
  addEmployeeSub,
  deleteEmployeeSub,
  fetchEmployeeDetail,
  upsertMyNumber,
} from "@/api/endpoints";
import { Field } from "@/components/Field";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import {
  documentKindOptions,
  emergencyKindOptions,
  statusVariant,
} from "@/lib/options";
import { fmtDate } from "@/lib/utils";

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex gap-2 py-1 text-sm">
      <span className="w-28 shrink-0 text-muted-foreground">{label}</span>
      <span>{value ?? "-"}</span>
    </div>
  );
}

export function EmployeeDetailPage() {
  const { id } = useParams();
  const employeeId = Number(id);
  const qc = useQueryClient();
  const { data: emp, isLoading } = useQuery({
    queryKey: ["employee", employeeId],
    queryFn: () => fetchEmployeeDetail(employeeId),
  });

  const refresh = () => qc.invalidateQueries({ queryKey: ["employee", employeeId] });

  // 子リソース追加の汎用mutation
  const addSub = useMutation({
    mutationFn: ({ sub, payload }: { sub: string; payload: Record<string, unknown> }) =>
      addEmployeeSub(employeeId, sub, payload),
    onSuccess: refresh,
    onError: (e) => alert(errMessage(e)),
  });
  const delSub = useMutation({
    mutationFn: ({ sub, subId }: { sub: string; subId: number }) =>
      deleteEmployeeSub(employeeId, sub, subId),
    onSuccess: refresh,
    onError: (e) => alert(errMessage(e)),
  });

  // フォーム状態
  const [card, setCard] = useState({
    residence_status: "",
    card_number: "",
    period_text: "",
    expiry_date: "",
  });
  const [bank, setBank] = useState({
    bank_name: "",
    branch_name: "",
    branch_code: "",
    account_number: "",
    account_holder_kana: "",
  });
  const [emg, setEmg] = useState({
    kind: "母国親族",
    contact_name: "",
    relationship: "",
    phone: "",
  });
  const [hist, setHist] = useState({
    employment_insurance_no: "",
    previous_company_name: "",
    has_withholding_slip: false,
    withholding_year: "",
  });
  const [doc, setDoc] = useState({ doc_kind: "在留カード表", file_path: "", original_name: "" });
  const [mn, setMn] = useState({ my_number: "", has_card: false, collected_at: "" });

  const saveMyNumber = useMutation({
    mutationFn: () =>
      upsertMyNumber(employeeId, {
        my_number: mn.my_number || undefined,
        has_card: mn.has_card,
        collected_at: mn.collected_at || null,
      }),
    onSuccess: () => {
      setMn({ my_number: "", has_card: false, collected_at: "" });
      refresh();
      alert("マイナンバー情報を保存しました");
    },
    onError: (e) => alert(errMessage(e)),
  });

  if (isLoading || !emp) {
    return <p className="text-muted-foreground">読み込み中...</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" asChild>
          <Link to="/employees">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <h1 className="text-xl font-bold">{emp.name}</h1>
        <Badge variant={statusVariant(emp.status)}>{emp.status}</Badge>
      </div>

      {/* 基本情報 */}
      <Card>
        <CardHeader>
          <CardTitle>基本情報</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-x-8">
          <div>
            <Row label="ローマ字" value={emp.name_romaji} />
            <Row label="フリガナ" value={emp.name_kana} />
            <Row label="生年月日" value={fmtDate(emp.birth_date)} />
            <Row label="性別" value={emp.gender} />
            <Row label="国籍" value={emp.nationality} />
          </div>
          <div>
            <Row label="携帯" value={emp.mobile_phone} />
            <Row label="メール" value={emp.email} />
            <Row label="郵便番号" value={emp.postal_code} />
            <Row label="住所" value={emp.address} />
            <Row label="入社日" value={fmtDate(emp.hire_date)} />
          </div>
        </CardContent>
      </Card>

      {/* 在留カード */}
      <Card>
        <CardHeader>
          <CardTitle>在留カード</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {emp.residence_cards.map((c) => (
            <div key={c.id} className="flex items-center justify-between rounded border p-2 text-sm">
              <span>
                {c.residence_status} / {c.card_number} / {c.period_text} / 満了 {fmtDate(c.expiry_date)}
                {c.is_current && <Badge className="ml-2">現行</Badge>}
              </span>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => delSub.mutate({ sub: "residence-cards", subId: c.id })}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
          ))}
          <div className="grid grid-cols-5 gap-2">
            <Input
              placeholder="在留資格"
              value={card.residence_status}
              onChange={(e) => setCard({ ...card, residence_status: e.target.value })}
            />
            <Input
              placeholder="カード番号"
              value={card.card_number}
              onChange={(e) => setCard({ ...card, card_number: e.target.value })}
            />
            <Input
              placeholder="期間(例:3年)"
              value={card.period_text}
              onChange={(e) => setCard({ ...card, period_text: e.target.value })}
            />
            <Input
              type="date"
              value={card.expiry_date}
              onChange={(e) => setCard({ ...card, expiry_date: e.target.value })}
            />
            <Button
              variant="outline"
              onClick={() =>
                addSub.mutate({ sub: "residence-cards", payload: { ...card, is_current: true } })
              }
              disabled={!card.residence_status || !card.card_number || !card.expiry_date}
            >
              <Plus className="h-4 w-4" /> 追加
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 銀行口座 */}
      <Card>
        <CardHeader>
          <CardTitle>銀行口座</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {emp.bank_accounts.map((b) => (
            <div key={b.id} className="flex items-center justify-between rounded border p-2 text-sm">
              <span>
                {b.bank_name} {b.branch_name}（{b.branch_code}）{b.account_number} / {b.account_holder_kana}
              </span>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => delSub.mutate({ sub: "bank-accounts", subId: b.id })}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
          ))}
          <div className="grid grid-cols-6 gap-2">
            <Input
              placeholder="銀行名"
              value={bank.bank_name}
              onChange={(e) => setBank({ ...bank, bank_name: e.target.value })}
            />
            <Input
              placeholder="支店名"
              value={bank.branch_name}
              onChange={(e) => setBank({ ...bank, branch_name: e.target.value })}
            />
            <Input
              placeholder="店番"
              value={bank.branch_code}
              onChange={(e) => setBank({ ...bank, branch_code: e.target.value })}
            />
            <Input
              placeholder="口座番号"
              value={bank.account_number}
              onChange={(e) => setBank({ ...bank, account_number: e.target.value })}
            />
            <Input
              placeholder="名義(カナ)"
              value={bank.account_holder_kana}
              onChange={(e) => setBank({ ...bank, account_holder_kana: e.target.value })}
            />
            <Button
              variant="outline"
              onClick={() => addSub.mutate({ sub: "bank-accounts", payload: { ...bank, is_primary: true } })}
              disabled={!bank.bank_name}
            >
              <Plus className="h-4 w-4" /> 追加
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 緊急連絡先 */}
      <Card>
        <CardHeader>
          <CardTitle>緊急連絡先</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {emp.emergency_contacts.map((c) => (
            <div key={c.id} className="flex items-center justify-between rounded border p-2 text-sm">
              <span>
                <Badge variant="secondary">{c.kind}</Badge> {c.contact_name}（{c.relationship}）{c.phone}
              </span>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => delSub.mutate({ sub: "emergency-contacts", subId: c.id })}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
          ))}
          <div className="grid grid-cols-5 gap-2">
            <Select
              options={emergencyKindOptions}
              value={emg.kind}
              onChange={(e) => setEmg({ ...emg, kind: e.target.value })}
            />
            <Input
              placeholder="氏名"
              value={emg.contact_name}
              onChange={(e) => setEmg({ ...emg, contact_name: e.target.value })}
            />
            <Input
              placeholder="続柄"
              value={emg.relationship}
              onChange={(e) => setEmg({ ...emg, relationship: e.target.value })}
            />
            <Input
              placeholder="電話"
              value={emg.phone}
              onChange={(e) => setEmg({ ...emg, phone: e.target.value })}
            />
            <Button
              variant="outline"
              onClick={() => addSub.mutate({ sub: "emergency-contacts", payload: emg })}
              disabled={!emg.contact_name || !emg.phone}
            >
              <Plus className="h-4 w-4" /> 追加
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 転職情報 */}
      <Card>
        <CardHeader>
          <CardTitle>転職情報</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {emp.employment_history.map((h) => (
            <div key={h.id} className="flex items-center justify-between rounded border p-2 text-sm">
              <span>
                前職: {h.previous_company_name ?? "-"} / 雇用保険: {h.employment_insurance_no ?? "-"} /
                源泉徴収票: {h.has_withholding_slip ? `有(${h.withholding_year ?? ""})` : "無"}
              </span>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => delSub.mutate({ sub: "employment-history", subId: h.id })}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
          ))}
          <div className="grid grid-cols-5 gap-2">
            <Input
              placeholder="雇用保険番号"
              value={hist.employment_insurance_no}
              onChange={(e) => setHist({ ...hist, employment_insurance_no: e.target.value })}
            />
            <Input
              placeholder="前職会社名"
              value={hist.previous_company_name}
              onChange={(e) => setHist({ ...hist, previous_company_name: e.target.value })}
            />
            <label className="flex h-9 items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={hist.has_withholding_slip}
                onChange={(e) => setHist({ ...hist, has_withholding_slip: e.target.checked })}
              />
              源泉徴収票
            </label>
            <Input
              type="number"
              placeholder="対象年"
              value={hist.withholding_year}
              onChange={(e) => setHist({ ...hist, withholding_year: e.target.value })}
            />
            <Button
              variant="outline"
              onClick={() =>
                addSub.mutate({
                  sub: "employment-history",
                  payload: {
                    ...hist,
                    withholding_year: hist.withholding_year ? Number(hist.withholding_year) : null,
                  },
                })
              }
            >
              <Plus className="h-4 w-4" /> 追加
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 提出書類 */}
      <Card>
        <CardHeader>
          <CardTitle>提出書類</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {emp.documents.map((d) => (
            <div key={d.id} className="flex items-center justify-between rounded border p-2 text-sm">
              <span>
                <Badge variant="secondary">{d.doc_kind}</Badge> {d.file_path}{" "}
                {d.original_name && `(${d.original_name})`}
              </span>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => delSub.mutate({ sub: "documents", subId: d.id })}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
          ))}
          <div className="grid grid-cols-4 gap-2">
            <Select
              options={documentKindOptions}
              value={doc.doc_kind}
              onChange={(e) => setDoc({ ...doc, doc_kind: e.target.value })}
            />
            <Input
              placeholder="ファイルパス/S3キー"
              value={doc.file_path}
              onChange={(e) => setDoc({ ...doc, file_path: e.target.value })}
            />
            <Input
              placeholder="元ファイル名"
              value={doc.original_name}
              onChange={(e) => setDoc({ ...doc, original_name: e.target.value })}
            />
            <Button
              variant="outline"
              onClick={() => addSub.mutate({ sub: "documents", payload: doc })}
              disabled={!doc.file_path}
            >
              <Plus className="h-4 w-4" /> 追加
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* マイナンバー */}
      <Card className="border-amber-300">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-amber-500" />
            マイナンバー（最高機密・暗号化保存）
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="text-sm text-muted-foreground">
            現在の状態：
            {emp.my_number?.has_number ? (
              <Badge variant="success" className="ml-1">登録済（値は非表示）</Badge>
            ) : (
              <Badge variant="muted" className="ml-1">未登録</Badge>
            )}
            <span className="ml-3">
              カード所持: {emp.my_number?.has_card ? "有" : "無"} / 回収日:{" "}
              {fmtDate(emp.my_number?.collected_at)}
            </span>
          </div>
          <div className="grid grid-cols-4 gap-2">
            <Field label="マイナンバー(12桁)">
              <Input
                placeholder="入力すると暗号化保存"
                value={mn.my_number}
                onChange={(e) => setMn({ ...mn, my_number: e.target.value })}
              />
            </Field>
            <Field label="回収日">
              <Input
                type="date"
                value={mn.collected_at}
                onChange={(e) => setMn({ ...mn, collected_at: e.target.value })}
              />
            </Field>
            <Field label="カード所持">
              <label className="flex h-9 items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={mn.has_card}
                  onChange={(e) => setMn({ ...mn, has_card: e.target.checked })}
                />
                所持している
              </label>
            </Field>
            <div className="flex items-end">
              <Button onClick={() => saveMyNumber.mutate()} disabled={saveMyNumber.isPending}>
                保存
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
