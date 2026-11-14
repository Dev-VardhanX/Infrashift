import test from "node:test";
import assert from "node:assert/strict";
import en from "../i18n/en.js";
import hi from "../i18n/hi.js";
import { tEntity, ENTITY_MAP } from "../i18n/entities.js";

test("every key in en.js exists in hi.js and vice versa", () => {
  const enKeys = Object.keys(en).sort();
  const hiKeys = Object.keys(hi).sort();

  const missingInHi = enKeys.filter((k) => !hi.hasOwnProperty(k));
  const missingInEn = hiKeys.filter((k) => !en.hasOwnProperty(k));

  assert.deepEqual(missingInHi, [], `Keys in en.js missing in hi.js: ${missingInHi.join(", ")}`);
  assert.deepEqual(missingInEn, [], `Keys in hi.js missing in en.js: ${missingInEn.join(", ")}`);
  assert.deepEqual(enKeys, hiKeys);
});

test("tEntity preserves English when lang is en", () => {
  assert.equal(tEntity("Sugar 1kg", "en"), "Sugar 1kg");
  assert.equal(tEntity("Anil Gupta", "en"), "Anil Gupta");
  assert.equal(tEntity("Gupta Traders", "en"), "Gupta Traders");
});

test("tEntity translates products, customers, suppliers to Hindi with Western Arabic counting digits", () => {
  // Product names in Hindi with Western digits
  assert.equal(tEntity("Sugar 1kg", "hi"), "चीनी 1kg");
  assert.equal(tEntity("Amul Ghee 1L", "hi"), "अमूल घी 1L");
  assert.equal(tEntity("Aashirvaad Atta 5kg", "hi"), "आशीर्वाद आटा 5kg");
  assert.equal(tEntity("Parle-G 800g", "hi"), "पारले-जी 800g");

  // Customer names in Hindi
  assert.equal(tEntity("Anil Gupta", "hi"), "अनिल गुप्ता");
  assert.equal(tEntity("Meena Kohli", "hi"), "मीना कोहली");
  assert.equal(tEntity("Vikas Yadav", "hi"), "विकास यादव");

  // Supplier names in Hindi
  assert.equal(tEntity("Gupta Traders", "hi"), "गुप्ता ट्रेडर्स");
  assert.equal(tEntity("Om Puja Bhandar", "hi"), "ओम पूजा भंडार");

  // Category names in Hindi
  assert.equal(tEntity("Dry Fruits", "hi"), "सूखे मेवे");

  // Dynamic regex phrases
  assert.equal(tEntity("Sold 343 units in last 14 days", "hi"), "पिछले 14 दिनों में 343 यूनिट बिकीं");
  assert.equal(tEntity("2 days", "hi"), "2 दिन");

  // Numbers must not be Devanagari numerals
  const hindiTranslation = tEntity("Sugar 1kg", "hi");
  assert.match(hindiTranslation, /1/);
  assert.doesNotMatch(hindiTranslation, /[०-९]/);
});
