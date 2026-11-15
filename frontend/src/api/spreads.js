import { request } from "./client.js";

export const listSpreads = () => request("/spreads");
