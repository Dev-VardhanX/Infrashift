import test from "node:test";
import assert from "node:assert/strict";
import { inr, inrCompact, dmon, addDays } from "./format.js";

test("inr uses Indian grouping", () => {
  assert.equal(inr(1432103), "Rs 14,32,103");
  assert.equal(inr(35248), "Rs 35,248");
  assert.equal(inr(-9685), "-Rs 9,685");
});
test("inrCompact uses lakh and crore", () => {
  assert.equal(inrCompact(1432103), "Rs 14.3 lakh");
  assert.equal(inrCompact(25000000), "Rs 2.5 crore");
  assert.equal(inrCompact(45556), "Rs 45,556");
});
test("dates", () => {
  assert.equal(dmon("2026-11-08"), "08 Nov");
  assert.equal(addDays("2026-11-13", -29), "2026-10-15");
});
