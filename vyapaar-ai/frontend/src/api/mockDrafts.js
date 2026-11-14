// Mock-mode only: mirrors the text templates in doc 02 section 6.4 so the UI can be built before M4's backend lands.
import { dmon } from "../lib/format.js";

const grp = new Intl.NumberFormat("en-IN");
const waLink = (phone, text) => `https://wa.me/91${phone}?text=${encodeURIComponent(text)}`;

export function buildDrafts(type, ids, lang, { alertsMock, khataMock }) {
  if (type === "purchase_order") {
    const items = alertsMock.items.filter((a) => ids.includes(a.sku));
    const bySupplier = {};
    items.forEach((a) => (bySupplier[a.supplier] ??= []).push(a));
    return Object.entries(bySupplier).map(([supplier, list]) => {
      const lines = list.map((a) => `- ${a.name} x ${a.suggested_qty}`).join("\n");
      const text = `Namaste ${supplier} ji, order for Sharma General Store:\n${lines}\nPlease deliver by tomorrow. Dhanyavaad.`;
      return { to: supplier, text, wa_link: waLink("9000000000", text) };
    });
  }
  return khataMock.customers
    .filter((c) => ids.includes(c.id))
    .map((c) => {
      const first = c.name.split(" ")[0];
      const text =
        lang === "en"
          ? `Hello ${first} ji, a gentle reminder from Sharma General Store: Rs ${grp.format(c.balance)} is pending (last payment ${dmon(c.last_payment_date)}). Please pay by UPI when convenient. Thank you.`
          : `Namaste ${first} ji, Sharma General Store se yaad dilana tha: Rs ${grp.format(c.balance)} baaki hai (aakhri payment ${dmon(c.last_payment_date)}). Jab suvidha ho UPI kar dijiye. Dhanyavaad.`;
      return { to: c.name, text, wa_link: waLink(c.phone, text) };
    });
}
