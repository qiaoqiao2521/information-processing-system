import { redirect } from "react-router";
// One reading stream. Preserve bookmarked filters, search, paging and tags.
export function loader({ request }: { request: Request }) {
  return redirect(`/all${new URL(request.url).search}`);
}
export default function Home() { return null; }
