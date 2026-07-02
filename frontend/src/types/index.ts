// ===== 列挙 =====
export type UserRole = "admin" | "manager" | "sales";
export type EngineerStatus = "待機" | "稼働中" | "契約終了予定" | "離脱";
export type BusinessType = "エンド" | "SIer" | "コンサル" | "BP";
export type ProjectStatus = "募集中" | "提案中" | "成約" | "クローズ";
export type ContractType = "上位" | "下位";
export type ContractStatus = "契約中" | "更新待ち" | "終了";
export type InvoiceStatus = "未請求" | "請求済" | "入金済";
export type GenderType = "男" | "女" | "その他" | "未回答";
export type EmployeeStatus = "在籍" | "休職" | "退職";
export type EmergencyContactKind = "母国親族" | "在日緊急連絡" | "その他";
export type DocumentKind =
  | "在留カード表"
  | "在留カード裏"
  | "パスポート"
  | "証明写真"
  | "源泉徴収票"
  | "マイナンバーカード"
  | "その他";

// ===== 共通 =====
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface CurrentUser {
  id: number;
  email: string;
  name: string;
  role: UserRole;
  is_active: boolean;
}

export interface Skill {
  name: string;
  years: number;
}

// ===== 技術者 =====
export interface Engineer {
  id: number;
  name: string;
  name_kana: string | null;
  email: string | null;
  phone: string | null;
  skills: Skill[];
  skill_sheet_path: string | null;
  unit_price: number | null;
  status: EngineerStatus;
  available_from: string | null;
  remote_ok: boolean;
  note: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

// ===== 取引先 =====
export interface Client {
  id: number;
  company_name: string;
  business_type: BusinessType;
  contact_name: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  can_distribute: boolean;
  note: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

// ===== 案件 =====
export interface Project {
  id: number;
  client_id: number;
  client_name: string | null;
  title: string;
  required_skills: Skill[];
  unit_price_min: number | null;
  unit_price_max: number | null;
  headcount: number;
  work_location: string | null;
  remote_ok: boolean;
  start_date: string | null;
  status: ProjectStatus;
  note: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

// ===== 契約 =====
export interface Contract {
  id: number;
  engineer_id: number;
  engineer_name: string | null;
  project_id: number | null;
  project_title: string | null;
  contract_type: ContractType;
  counterparty_client_id: number | null;
  counterparty_name: string | null;
  parent_contract_id: number | null;
  unit_price: number;
  settlement_lower: number | null;
  settlement_upper: number | null;
  overtime_rate: number;
  deduction_rate: number;
  start_date: string;
  end_date: string;
  auto_renew: boolean;
  status: ContractStatus;
  contract_file_path: string | null;
  created_at: string;
  updated_at: string;
}

export interface GrossProfitRow {
  engineer_id: number;
  engineer_name: string;
  year_month: string;
  upper_contract_id: number | null;
  lower_contract_id: number | null;
  lower_count: number;
  upper_billed: number;
  lower_paid: number;
  gross_profit: number;
  gross_margin: number | null;
}

// ===== 稼働実績 =====
export interface WorkRecord {
  id: number;
  contract_id: number;
  engineer_name: string | null;
  year_month: string;
  worked_hours: number;
  created_at: string;
  updated_at: string;
}

// ===== 請求 =====
export interface Invoice {
  id: number;
  contract_id: number;
  engineer_name: string | null;
  counterparty_name: string | null;
  year_month: string;
  billed_amount: number;
  status: InvoiceStatus;
  issued_date: string | null;
  created_at: string;
  updated_at: string;
}

// ===== ダッシュボード =====
export interface StatusCount {
  status: string;
  count: number;
}
export interface MonthlyRevenue {
  year_month: string;
  revenue: number;
  cost: number;
  gross_profit: number;
}
export interface RenewalAlert {
  contract_id: number;
  engineer_name: string;
  counterparty_name: string | null;
  end_date: string;
  days_left: number;
}
export interface DashboardSummary {
  total_engineers: number;
  working_count: number;
  waiting_count: number;
  utilization_rate: number;
  engineer_status_breakdown: StatusCount[];
  this_month_revenue: number;
  this_month_gross_profit: number;
  this_month_gross_margin: number | null;
  monthly_trend: MonthlyRevenue[];
  renewal_alerts: RenewalAlert[];
}

// ===== 社員 =====
export interface ResidenceCard {
  id: number;
  employee_id: number;
  residence_status: string;
  card_number: string;
  period_text: string | null;
  expiry_date: string;
  is_current: boolean;
}
export interface BankAccount {
  id: number;
  employee_id: number;
  bank_code: string | null;
  bank_name: string | null;
  branch_name: string | null;
  branch_code: string | null;
  account_number: string | null;
  account_holder_kana: string | null;
  is_primary: boolean;
}
export interface EmergencyContact {
  id: number;
  employee_id: number;
  kind: EmergencyContactKind;
  contact_name: string;
  relationship: string | null;
  phone: string;
  note: string | null;
}
export interface EmploymentHistory {
  id: number;
  employee_id: number;
  employment_insurance_no: string | null;
  previous_company_name: string | null;
  has_withholding_slip: boolean;
  withholding_year: number | null;
  note: string | null;
}
export interface EmployeeDocumentItem {
  id: number;
  employee_id: number;
  doc_kind: DocumentKind;
  file_path: string;
  original_name: string | null;
  uploaded_by: number | null;
  uploaded_at: string;
}
export interface MyNumber {
  has_card: boolean;
  collected_at: string | null;
  has_number: boolean;
}
export interface Employee {
  id: number;
  user_id: number | null;
  name: string;
  name_romaji: string;
  name_kana: string;
  birth_date: string;
  gender: GenderType | null;
  nationality: string;
  mobile_phone: string | null;
  email: string | null;
  postal_code: string | null;
  address: string | null;
  hire_date: string | null;
  status: EmployeeStatus;
  note: string | null;
  created_at: string;
  updated_at: string;
}
export interface EmployeeDetail extends Employee {
  residence_cards: ResidenceCard[];
  bank_accounts: BankAccount[];
  emergency_contacts: EmergencyContact[];
  employment_history: EmploymentHistory[];
  documents: EmployeeDocumentItem[];
  my_number: MyNumber | null;
}

export interface AppUser {
  id: number;
  email: string;
  name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}
