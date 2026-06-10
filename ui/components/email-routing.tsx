"use client";

import { useEffect, useState } from "react";
import { Mail } from "lucide-react";
import { PanelSection } from "./panel-section";

interface TeamRoute {
  key: string;
  name: string;
  email: string;
  placeholder: string;
}

interface RoutingConfig {
  general_mailbox: string;
  teams: TeamRoute[];
  smtp_configured: boolean;
  test_mode: boolean;
}

export function EmailRouting() {
  const [config, setConfig] = useState<RoutingConfig | null>(null);
  const [generalMailbox, setGeneralMailbox] = useState("");
  const [teamEmails, setTeamEmails] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/admin/routing")
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((data: RoutingConfig) => {
        setConfig(data);
        setGeneralMailbox(data.general_mailbox || "");
        const emails: Record<string, string> = {};
        data.teams.forEach((t) => (emails[t.key] = t.email || ""));
        setTeamEmails(emails);
      })
      .catch(() => setError("Could not load routing config (is the backend running?)"));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const res = await fetch("/admin/routing", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ general_mailbox: generalMailbox, teams: teamEmails }),
      });
      if (!res.ok) throw new Error(`Save failed: ${res.status}`);
      setSavedAt(Date.now());
      setTimeout(() => setSavedAt(null), 3000);
    } catch (e: any) {
      setError(e.message || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <PanelSection
      title="Referral Email Routing"
      icon={<Mail className="h-4 w-4 text-blue-600" />}
    >
      <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
        {config?.test_mode && (
          <div className="mb-3 text-xs rounded-md bg-amber-50 border border-amber-200 text-amber-800 px-3 py-2">
            Test mode — SMTP is not configured, so referrals queue locally in{" "}
            <code>referrals_outbox.jsonl</code> instead of sending email.
          </div>
        )}
        {error && (
          <div className="mb-3 text-xs rounded-md bg-red-50 border border-red-200 text-red-700 px-3 py-2">
            {error}
          </div>
        )}

        <label className="block text-xs font-medium text-zinc-600 mb-1">
          General mailbox (default destination, filtered by subject tag)
        </label>
        <input
          type="email"
          className="w-full mb-3 rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="hcvinbox@yourpha.org"
          value={generalMailbox}
          onChange={(e) => setGeneralMailbox(e.target.value)}
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2 mb-3">
          {(config?.teams ?? []).map((t) => (
            <div key={t.key}>
              <label className="block text-xs font-medium text-zinc-600 mb-1">
                {t.name}
                <span className="ml-1 font-normal text-zinc-400">(optional override)</span>
              </label>
              <input
                type="email"
                className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={t.placeholder}
                value={teamEmails[t.key] ?? ""}
                onChange={(e) =>
                  setTeamEmails((prev) => ({ ...prev, [t.key]: e.target.value }))
                }
              />
            </div>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleSave}
            disabled={saving || !config}
            className="rounded-md bg-blue-600 text-white text-sm px-4 py-1.5 hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
          >
            {saving ? "Saving..." : "Save routing"}
          </button>
          {savedAt && <span className="text-xs text-green-600">Saved ✓</span>}
          <span className="ml-auto text-[11px] text-zinc-400">
            Blank team fields fall back to the general mailbox
          </span>
        </div>
      </div>
    </PanelSection>
  );
}
