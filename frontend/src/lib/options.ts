import type { SelectOption } from "@/components/ui/select";

export const engineerStatusOptions: SelectOption[] = [
  { value: "待機", label: "待機" },
  { value: "稼働中", label: "稼働中" },
  { value: "契約終了予定", label: "契約終了予定" },
  { value: "離脱", label: "離脱" },
];

export const businessTypeOptions: SelectOption[] = [
  { value: "エンド", label: "エンド" },
  { value: "SIer", label: "SIer" },
  { value: "コンサル", label: "コンサル" },
  { value: "BP", label: "BP" },
];

export const projectStatusOptions: SelectOption[] = [
  { value: "募集中", label: "募集中" },
  { value: "提案中", label: "提案中" },
  { value: "成約", label: "成約" },
  { value: "クローズ", label: "クローズ" },
];

export const contractTypeOptions: SelectOption[] = [
  { value: "上位", label: "上位（受注）" },
  { value: "下位", label: "下位（発注）" },
];

export const contractStatusOptions: SelectOption[] = [
  { value: "契約中", label: "契約中" },
  { value: "更新待ち", label: "更新待ち" },
  { value: "終了", label: "終了" },
];

export const invoiceStatusOptions: SelectOption[] = [
  { value: "未請求", label: "未請求" },
  { value: "請求済", label: "請求済" },
  { value: "入金済", label: "入金済" },
];

export const genderOptions: SelectOption[] = [
  { value: "男", label: "男" },
  { value: "女", label: "女" },
  { value: "その他", label: "その他" },
  { value: "未回答", label: "未回答" },
];

export const employeeStatusOptions: SelectOption[] = [
  { value: "在籍", label: "在籍" },
  { value: "休職", label: "休職" },
  { value: "退職", label: "退職" },
];

export const emergencyKindOptions: SelectOption[] = [
  { value: "母国親族", label: "母国親族" },
  { value: "在日緊急連絡", label: "在日緊急連絡" },
  { value: "その他", label: "その他" },
];

export const documentKindOptions: SelectOption[] = [
  { value: "在留カード表", label: "在留カード表" },
  { value: "在留カード裏", label: "在留カード裏" },
  { value: "パスポート", label: "パスポート" },
  { value: "証明写真", label: "証明写真" },
  { value: "源泉徴収票", label: "源泉徴収票" },
  { value: "マイナンバーカード", label: "マイナンバーカード" },
  { value: "その他", label: "その他" },
];

export const userRoleOptions: SelectOption[] = [
  { value: "admin", label: "admin（全操作）" },
  { value: "manager", label: "manager（閲覧+編集）" },
  { value: "sales", label: "sales（自分の登録分）" },
];

type BadgeVariant = "default" | "secondary" | "success" | "warning" | "danger" | "muted";

/** ステータス文字列 → バッジ色 */
export function statusVariant(status: string): BadgeVariant {
  switch (status) {
    case "稼働中":
    case "成約":
    case "入金済":
    case "在籍":
    case "契約中":
      return "success";
    case "待機":
    case "募集中":
    case "提案中":
    case "更新待ち":
    case "請求済":
    case "休職":
      return "warning";
    case "離脱":
    case "終了":
    case "クローズ":
    case "退職":
    case "未請求":
      return "muted";
    default:
      return "secondary";
  }
}
