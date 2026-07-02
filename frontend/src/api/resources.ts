import { api } from "./client";
import type { Page } from "@/types";

// フォームのpayloadは文字列のenum等を含むため、create/updateは緩い型で受ける。
type Payload = Record<string, unknown>;

/** 汎用CRUDクライアント。各マスタはこれを基に使う。 */
export function makeResource<T>(path: string) {
  return {
    list: async (params?: Record<string, unknown>): Promise<Page<T>> => {
      const { data } = await api.get<Page<T>>(path, { params });
      return data;
    },
    get: async (id: number): Promise<T> => {
      const { data } = await api.get<T>(`${path}/${id}`);
      return data;
    },
    create: async (payload: Payload): Promise<T> => {
      const { data } = await api.post<T>(path, payload);
      return data;
    },
    update: async (id: number, payload: Payload): Promise<T> => {
      const { data } = await api.put<T>(`${path}/${id}`, payload);
      return data;
    },
    remove: async (id: number): Promise<void> => {
      await api.delete(`${path}/${id}`);
    },
  };
}
