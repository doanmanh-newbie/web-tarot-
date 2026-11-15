import { request } from "./client.js";

export const listCards = () => request("/admin/cards");
export const updateCard = (id, upright_meaning, reversed_meaning) =>
  request(`/admin/cards/${id}`, { method: "PUT", body: { upright_meaning, reversed_meaning } });
