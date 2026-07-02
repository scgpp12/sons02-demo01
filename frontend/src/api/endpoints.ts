import { api } from "./client";
import { makeResource } from "./resources";
import type {
  AppUser,
  Client,
  Contract,
  DashboardSummary,
  Employee,
  EmployeeDetail,
  Engineer,
  GrossProfitRow,
  Invoice,
  Token,
  WorkRecord,
} from "@/types";

export const engineersApi = makeResource<Engineer>("/api/engineers");
export const clientsApi = makeResource<Client>("/api/clients");
export const projectsApi = makeResource<import("@/types").Project>("/api/projects");
export const contractsApi = makeResource<Contract>("/api/contracts");
export const usersApi = makeResource<AppUser>("/api/users");

// 認証
export async function login(email: string, password: string): Promise<Token> {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  const { data } = await api.post<Token>("/api/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}
export async function fetchMe() {
  const { data } = await api.get("/api/auth/me");
  return data;
}

// 契約の特殊エンドポイント
export async function fetchRenewals(): Promise<Contract[]> {
  const { data } = await api.get<Contract[]>("/api/contracts/renewals");
  return data;
}
export async function fetchUpperContracts(): Promise<Contract[]> {
  const { data } = await api.get<Contract[]>("/api/contracts/uppers");
  return data;
}
export async function fetchGrossProfit(yearMonth: string): Promise<GrossProfitRow[]> {
  const { data } = await api.get<GrossProfitRow[]>("/api/contracts/gross-profit", {
    params: { year_month: yearMonth },
  });
  return data;
}

// 稼働実績
export async function listWorkRecords(params: Record<string, unknown>) {
  const { data } = await api.get<import("@/types").Page<WorkRecord>>("/api/work-records", {
    params,
  });
  return data;
}
export async function upsertWorkRecord(payload: {
  contract_id: number;
  year_month: string;
  worked_hours: number;
}) {
  const { data } = await api.post<WorkRecord>("/api/work-records", payload);
  return data;
}

// 請求
export async function listInvoices(params: Record<string, unknown>) {
  const { data } = await api.get<import("@/types").Page<Invoice>>("/api/invoices", { params });
  return data;
}
export async function generateInvoices(yearMonth: string): Promise<Invoice[]> {
  const { data } = await api.post<Invoice[]>("/api/invoices/generate", {
    year_month: yearMonth,
  });
  return data;
}
export async function updateInvoice(
  id: number,
  payload: { status?: string; issued_date?: string | null },
) {
  const { data } = await api.put<Invoice>(`/api/invoices/${id}`, payload);
  return data;
}

// ダッシュボード
export async function fetchDashboard(): Promise<DashboardSummary> {
  const { data } = await api.get<DashboardSummary>("/api/dashboard");
  return data;
}

// 社員
export const employeesApi = makeResource<Employee>("/api/employees");
export async function fetchEmployeeDetail(id: number): Promise<EmployeeDetail> {
  const { data } = await api.get<EmployeeDetail>(`/api/employees/${id}`);
  return data;
}
export async function addEmployeeSub(
  employeeId: number,
  sub: string,
  payload: Record<string, unknown>,
) {
  const { data } = await api.post(`/api/employees/${employeeId}/${sub}`, payload);
  return data;
}
export async function deleteEmployeeSub(employeeId: number, sub: string, subId: number) {
  await api.delete(`/api/employees/${employeeId}/${sub}/${subId}`);
}
export async function upsertMyNumber(
  employeeId: number,
  payload: { my_number?: string | null; has_card: boolean; collected_at: string | null },
) {
  const { data } = await api.put(`/api/employees/${employeeId}/my-number`, payload);
  return data;
}
