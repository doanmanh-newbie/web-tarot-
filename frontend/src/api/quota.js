import { request } from "./client.js";

export const getQuota = () => request("/me/quota");
