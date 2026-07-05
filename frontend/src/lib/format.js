// Groups a plain digit string using the Indian numbering convention
// (last 3 digits, then pairs of 2): 1000000 -> "10,00,000".
export function groupIndianDigits(digits) {
  if (!digits) return "";
  if (digits.length <= 3) return digits;

  const lastThree = digits.slice(-3);
  let rest = digits.slice(0, -3);
  const parts = [];
  while (rest.length > 2) {
    parts.unshift(rest.slice(-2));
    rest = rest.slice(0, -2);
  }
  if (rest) parts.unshift(rest);
  return `${parts.join(",")},${lastThree}`;
}

export function formatINR(amount) {
  if (amount === null || amount === undefined || Number.isNaN(amount)) return "N/A";
  const rounded = Math.round(Number(amount));
  const sign = rounded < 0 ? "-" : "";
  const digits = String(Math.abs(rounded));

  return `${sign}₹${groupIndianDigits(digits)}`;
}

export function formatCompactINR(amount) {
  if (amount === null || amount === undefined || Number.isNaN(amount)) return "N/A";
  const value = Number(amount);
  const abs = Math.abs(value);

  if (abs >= 1e7) return `₹${(value / 1e7).toFixed(2)} Cr`;
  if (abs >= 1e5) return `₹${(value / 1e5).toFixed(2)} L`;
  return formatINR(value);
}
