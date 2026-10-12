import { redirect } from "react-router";
import { loader as poolLoader } from "./all";
export { headers, meta, default } from "./all";

// Preserve old search links while categories read the full public pool.
export function loader(args: { request: Request }) {
  const url = new URL(args.request.url);
  if (url.searchParams.get("q")?.trim()) throw redirect(`/all${url.search}`);
  return poolLoader(args);
}
