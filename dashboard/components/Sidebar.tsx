import Link from "next/link";

const links = [
  { href: "/", label: "Overview" },
  { href: "/providers", label: "Providers" },
  { href: "/cost", label: "Cost" },
  { href: "/security", label: "Security" },
  { href: "/traces", label: "Traces" },
  { href: "/prompts", label: "Prompts" },
  { href: "/datasets", label: "Datasets" },
  { href: "/alerts", label: "Alerts" },
  { href: "/settings", label: "Settings" },
];

export function Sidebar() {
  return (
    <aside className="w-56 shrink-0 border-r border-slate-800 bg-panel p-4">
      <div className="mb-6 text-lg font-semibold text-accent">TraceLens</div>
      <nav className="flex flex-col gap-2 text-sm text-slate-200">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="rounded px-2 py-1 hover:bg-slate-800"
          >
            {link.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}