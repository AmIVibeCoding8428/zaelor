// Minimal markdown renderer for the Claude-generated memo — handles just enough
// (headings, bold, hr, lists, tables, paragraphs) to render Claude's prose readably
// without pulling in a full markdown dependency.

import { CheckCircle2 } from "lucide-react";

function renderInline(text, keyPrefix) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={`${keyPrefix}-${i}`} className="text-text font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <span key={`${keyPrefix}-${i}`}>{part}</span>;
  });
}

function isTableRow(line) {
  return line.trim().startsWith("|") || (line.includes("|") && line.trim().length > 0);
}

function isTableSeparator(line) {
  return /^\|?[\s:|-]+\|?$/.test(line.trim()) && line.includes("-");
}

function parseTableRow(line) {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

export function renderMarkdownLite(markdown) {
  const lines = (markdown || "").split("\n");
  const blocks = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.trim() === "") {
      i += 1;
      continue;
    }

    if (line.trim() === "---") {
      blocks.push({ type: "hr" });
      i += 1;
      continue;
    }

    const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      blocks.push({ type: "heading", level: headingMatch[1].length, text: headingMatch[2] });
      i += 1;
      continue;
    }

    if (isTableRow(line) && i + 1 < lines.length && isTableSeparator(lines[i + 1])) {
      const header = parseTableRow(line);
      const rows = [];
      i += 2;
      while (i < lines.length && isTableRow(lines[i]) && lines[i].trim() !== "") {
        rows.push(parseTableRow(lines[i]));
        i += 1;
      }
      blocks.push({ type: "table", header, rows });
      continue;
    }

    if (/^\s*[-*]\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*]\s+/, ""));
        i += 1;
      }
      blocks.push({ type: "ul", items });
      continue;
    }

    if (/^\s*\d+\.\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, ""));
        i += 1;
      }
      blocks.push({ type: "ol", items });
      continue;
    }

    const paragraphLines = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      lines[i].trim() !== "---" &&
      !/^(#{1,6})\s+/.test(lines[i]) &&
      !/^\s*[-*]\s+/.test(lines[i]) &&
      !/^\s*\d+\.\s+/.test(lines[i])
    ) {
      paragraphLines.push(lines[i]);
      i += 1;
    }
    blocks.push({ type: "p", text: paragraphLines.join(" ") });
  }

  const HEADING_STYLES = {
    1: "text-xl font-semibold text-gold mt-6 mb-3",
    2: "text-lg font-semibold text-gold mt-6 mb-3",
    3: "text-base font-semibold text-text mt-5 mb-2",
    4: "text-sm font-semibold text-text mt-4 mb-2",
    5: "text-sm font-semibold text-secondary mt-4 mb-2",
    6: "text-sm font-semibold text-secondary mt-4 mb-2",
  };

  return blocks.map((block, index) => {
    const key = `block-${index}`;

    switch (block.type) {
      case "heading":
        return (
          <p key={key} className={HEADING_STYLES[block.level] || HEADING_STYLES[6]}>
            {renderInline(block.text, key)}
          </p>
        );
      case "hr":
        return <hr key={key} className="border-white/10 my-6" />;
      case "ul":
        return (
          <ul key={key} className="space-y-2.5 mb-5">
            {block.items.map((item, itemIndex) => (
              <li key={`${key}-${itemIndex}`} className="flex items-start gap-2.5 text-secondary leading-relaxed">
                <CheckCircle2 size={15} className="text-gold shrink-0 mt-0.5" />
                <span>{renderInline(item, `${key}-${itemIndex}`)}</span>
              </li>
            ))}
          </ul>
        );
      case "ol":
        return (
          <ol key={key} className="list-decimal list-inside space-y-1.5 mb-4 text-secondary">
            {block.items.map((item, itemIndex) => (
              <li key={`${key}-${itemIndex}`} className="leading-relaxed">
                {renderInline(item, `${key}-${itemIndex}`)}
              </li>
            ))}
          </ol>
        );
      case "table":
        // Rendered as scannable advisory cards (checkmark + title + label/value
        // facts) instead of a literal table — see CLAUDE.md Reports section note.
        return (
          <div key={key} className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5">
            {block.rows.map((row, rowIndex) => (
              <div
                key={`${key}-r-${rowIndex}`}
                className="rounded-xl border border-white/10 bg-background/40 px-4 py-3.5 transition-colors duration-300 ease-out hover:border-gold/20"
              >
                <div className="flex items-start gap-2.5 mb-2">
                  <CheckCircle2 size={15} className="text-gold shrink-0 mt-0.5" />
                  <span className="text-sm font-semibold text-text leading-snug">
                    {renderInline(row[0] ?? "", `${key}-r-${rowIndex}-title`)}
                  </span>
                </div>
                {row.length > 1 && (
                  <dl className="space-y-1 pl-[26px]">
                    {row.slice(1).map((cell, cellIndex) => (
                      <div key={`${key}-r-${rowIndex}-${cellIndex}`} className="flex justify-between gap-3 text-xs">
                        <dt className="text-secondary">{block.header[cellIndex + 1] ?? ""}</dt>
                        <dd className="text-text text-right">
                          {renderInline(cell, `${key}-r-${rowIndex}-c-${cellIndex}`)}
                        </dd>
                      </div>
                    ))}
                  </dl>
                )}
              </div>
            ))}
          </div>
        );
      case "p":
      default:
        return (
          <p key={key} className="mb-4 leading-relaxed text-secondary">
            {renderInline(block.text, key)}
          </p>
        );
    }
  });
}
