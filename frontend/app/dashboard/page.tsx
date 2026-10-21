import { redirect } from "next/navigation";

// Old entry point. Both areas now live at /admin and /workspace; the root page picks the right one.
export default function LegacyDashboard() {
  redirect("/");
}
