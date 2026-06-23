const fs = require('fs');
const path = require('path');

// Read the TS file
const tsPath = path.join(__dirname, 'rewardsHelper.ts');
let tsContent = fs.readFileSync(tsPath, 'utf8');

// Strip TypeScript annotations & imports/exports to make it plain JS
tsContent = tsContent.replace(/import\s+[\s\S]*?\s+from\s+['"].*?['"];?/g, '');
tsContent = tsContent.replace(/:\s*any/g, '');
tsContent = tsContent.replace(/:\s*VirtualReward\[\]/g, '');
tsContent = tsContent.replace(/export\s+/g, '');

// Evaluate the JS content in this context
eval(tsContent);

let warnCalled = false;
let lastWarnPayload = null;
const originalWarn = console.warn;
console.warn = (...args) => {
  warnCalled = true;
  lastWarnPayload = args[1];
  originalWarn(...args);
};

function resetMock() {
  warnCalled = false;
  lastWarnPayload = null;
}

console.log("Running getSafeRewards Unit Tests...\n");

// Test 1: rewards undefined
resetMock();
let result = getSafeRewards(undefined);
if (!Array.isArray(result) || result.length !== 0 || !warnCalled) {
  console.error("FAIL: rewards undefined");
  process.exit(1);
}
console.log("PASS: rewards undefined handles safely and warns.");

// Test 2: rewards null
resetMock();
result = getSafeRewards(null);
if (!Array.isArray(result) || result.length !== 0 || !warnCalled) {
  console.error("FAIL: rewards null");
  process.exit(1);
}
console.log("PASS: rewards null handles safely and warns.");

// Test 3: rewards object
resetMock();
result = getSafeRewards({ status: "success", data: [] });
if (!Array.isArray(result) || result.length !== 0 || !warnCalled) {
  console.error("FAIL: rewards object");
  process.exit(1);
}
console.log("PASS: rewards object handles safely and warns.");

// Test 4: rewards empty array
resetMock();
result = getSafeRewards([]);
if (!Array.isArray(result) || result.length !== 0 || warnCalled) {
  console.error("FAIL: rewards empty array");
  process.exit(1);
}
console.log("PASS: rewards empty array handles safely without warning.");

// Test 5: rewards populated array
resetMock();
const mockPayload = [{ id: "eco_avatar", name: "Eco Avatar", cost: 100 }];
result = getSafeRewards(mockPayload);
if (!Array.isArray(result) || result.length !== 1 || result[0].id !== "eco_avatar" || warnCalled) {
  console.error("FAIL: rewards populated array");
  process.exit(1);
}
console.log("PASS: rewards populated array returns correctly without warning.");

console.log("\nAll unit tests passed successfully!");
console.warn = originalWarn;
