import { useRef, useState } from "react";
import { loadSample, uploadFiles } from "../api/index.js";
import { PageHeader, DataTable } from "../components/ui.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import Icon from "../components/Icon.jsx";
import { dmon, num } from "../lib/format.js";
import { go } from "../lib/nav.js";
import { useLang } from "../i18n/index.jsx";

const FILES = ["sales.csv", "products.csv", "inventory.csv", "purchases.csv", "expenses.csv", "customers.csv", "khata_payments.csv"];

export default function Upload() {
  const { t, tName } = useLang();
  const [busy, setBusy] = useState(null); // "sample" | "upload"
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null); // { kind: "sample"|"upload", data }
  const [drag, setDrag] = useState(false);
  const input = useRef(null);

  async function run(kind, fn) {
    setBusy(kind);
    setError(null);
    setResult(null);
    try {
      setResult({ kind, data: await fn() });
    } catch (e) {
      setError(e);
    } finally {
      setBusy(null);
    }
  }

  const onFiles = (files) => {
    const list = [...files];
    if (!list.length) return;
    const bad = list.filter((f) => !f.name.toLowerCase().endsWith(".csv"));
    if (bad.length)
      return setError(new Error(t("csv_only_error", { files: bad.map((f) => f.name).join(", ") })));
    run("upload", () => uploadFiles(list));
  };

  return (
    <>
      <PageHeader title={t("your_data_title")} subtitle={t("your_data_subtitle")} />

      <div className="grid gap-4 md:grid-cols-2">
        <section className="card p-5">
          <h2 className="font-semibold">{t("load_sample_store")}</h2>
          <p className="mt-1 text-sm text-ink-500">{t("sample_store_desc")}</p>
          <button className="btn-primary mt-4 w-full" disabled={!!busy} onClick={() => run("sample", loadSample)}>
            {busy === "sample" ? t("loading") : t("load_sample_store")}
          </button>
        </section>

        <section
          className={`card border-2 border-dashed p-5 text-center ${drag ? "border-brand-500 bg-brand-50" : "border-transparent"
            }`}
          onDragOver={(e) => {
            e.preventDefault();
            setDrag(true);
          }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDrag(false);
            onFiles(e.dataTransfer.files);
          }}
        >
          <h2 className="font-semibold">{t("upload_csv_files")}</h2>
          <p className="mt-1 text-sm text-ink-500">{t("upload_csv_desc")}</p>
          <input
            ref={input}
            type="file"
            accept=".csv"
            multiple
            hidden
            onChange={(e) => {
              onFiles(e.target.files);
              e.target.value = "";
            }}
          />
          <button className="btn-ghost mt-4 w-full" disabled={!!busy} onClick={() => input.current?.click()}>
            {busy === "upload" ? t("uploading") : t("choose_files")}
          </button>
          <p className="mt-2 text-xs text-ink-500">{FILES.join(", ")}</p>
        </section>
      </div>

      {busy && <Loading label={busy === "sample" ? t("loading_sample_data") : t("checking_your_files")} />}
      {error && <ErrorState error={error} />}

      {result?.kind === "sample" && (
        <section className="card mt-4 p-5">
          <h2 className="font-semibold text-emerald-700 inline-flex items-center">
            <Icon name="check" className="h-5 w-5 mr-1.5 stroke-[2.5]" />
            <span>{t("sample_store_loaded", { date: dmon(result.data.as_of) })}</span>
          </h2>
          <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
            {Object.entries(result.data.loaded).map(([k, v]) => (
              <div key={k} className="rounded-xl bg-ink-100 p-3">
                <div className="text-xs text-ink-500">{tName(k)}</div>
                <div className="font-bold tabular-nums">{num(v)}</div>
              </div>
            ))}
          </div>
          <button className="btn-primary mt-4" onClick={() => go("dashboard")}>
            {t("open_dashboard")}
          </button>
        </section>
      )}

      {result?.kind === "upload" && <Report data={result.data} />}
    </>
  );
}

function Report({ data }) {
  const { t } = useLang();
  const rejected = data.files.reduce((s, f) => s + f.rows_rejected, 0);
  return (
    <section className="card mt-4 p-5">
      <h2 className="font-semibold">{t("validation_report")}</h2>
      <p className="text-sm text-ink-500">
        {rejected === 0
          ? t("all_rows_accepted")
          : t("rows_rejected_msg", { count: num(rejected) })}{" "}
        {t("data_as_of", { date: dmon(data.as_of) })}
      </p>
      <div className="mt-3">
        <DataTable
          columns={[t("col_file"), t("col_rows_ok"), t("col_rejected")]}
          rows={data.files.map((f) => [f.name, num(f.rows_ok), num(f.rows_rejected)])}
        />
      </div>
      {data.files.map((f) => (
        <div key={f.name} className="mt-4">
          <h3 className="text-sm font-semibold">{f.name}</h3>
          {Object.keys(f.reasons ?? {}).length > 0 && (
            <ul className="mt-1 list-inside list-disc text-sm text-red-700">
              {Object.entries(f.reasons).map(([r, n]) => (
                <li key={r}>
                  {r}: {num(n)} {t("rows_count", { count: num(n) })}
                </li>
              ))}
            </ul>
          )}
          {Object.keys(f.mapping ?? {}).length > 0 && (
            <p className="mt-1 break-words text-xs text-ink-500">
              {t("columns_matched")}{" "}
              {Object.entries(f.mapping)
                .map(([from, to]) => (from === to ? from : `${from} → ${to}`))
                .join(", ")}
            </p>
          )}
        </div>
      ))}
      <button className="btn-primary mt-4" onClick={() => go("dashboard")}>
        {t("open_dashboard")}
      </button>
    </section>
  );
}
