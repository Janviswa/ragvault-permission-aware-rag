import { Fragment, ReactNode } from "react";

// Tiny Markdown subset for model answers: paragraphs, - / * bullets, 1. numbered lists,
// # headings, **bold**, *italic*, `code`. Builds React elements only (never raw HTML).

const INLINE = /(\*\*[^*\n]+\*\*|`[^`\n]+`|(?<![*\w])\*[^*\s][^*\n]*?\*(?![*\w]))/g;

function inline(text: string, keyBase: string): ReactNode[] {
  const out: ReactNode[] = [];
  let last = 0;
  let i = 0;
  for (const match of text.matchAll(INLINE)) {
    const index = match.index ?? 0;
    if (index > last) out.push(text.slice(last, index));
    const token = match[0];
    const key = `${keyBase}-${i++}`;
    if (token.startsWith("**")) out.push(<strong key={key} className="font-semibold">{token.slice(2, -2)}</strong>);
    else if (token.startsWith("`")) out.push(<code key={key} className="rounded bg-mist px-1 py-0.5 font-mono text-[12.5px]">{token.slice(1, -1)}</code>);
    else out.push(<em key={key}>{token.slice(1, -1)}</em>);
    last = index + token.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

type Block =
  | { kind: "p"; lines: string[] }
  | { kind: "h"; text: string }
  | { kind: "ul"; items: string[] }
  | { kind: "ol"; start: number; items: string[] };

function parse(source: string): Block[] {
  const blocks: Block[] = [];
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  for (const raw of lines) {
    const line = raw.trimEnd();
    const bullet = line.match(/^\s*[-*•]\s+(.*)$/);
    const numbered = line.match(/^\s*(\d+)[.)]\s+(.*)$/);
    const heading = line.match(/^\s*#{1,6}\s+(.*)$/);
    const prev = blocks[blocks.length - 1];

    if (!line.trim()) {
      blocks.push({ kind: "p", lines: [] }); // paragraph break marker (empty paragraphs are dropped below)
    } else if (heading) {
      blocks.push({ kind: "h", text: heading[1] });
    } else if (bullet) {
      if (prev?.kind === "ul") prev.items.push(bullet[1]);
      else blocks.push({ kind: "ul", items: [bullet[1]] });
    } else if (numbered) {
      if (prev?.kind === "ol") prev.items.push(numbered[2]);
      else blocks.push({ kind: "ol", start: Number(numbered[1]), items: [numbered[2]] });
    } else if (prev?.kind === "p" && prev.lines.length > 0) {
      prev.lines.push(line);
    } else {
      blocks.push({ kind: "p", lines: [line] });
    }
  }
  return blocks.filter((b) => b.kind !== "p" || b.lines.length > 0);
}

export function Markdown({ text, className = "" }: { text: string; className?: string }) {
  const blocks = parse(text);
  return (
    <div className={`space-y-2.5 break-words ${className}`}>
      {blocks.map((block, index) => {
        const key = `b${index}`;
        if (block.kind === "h") return <p key={key} className="font-bold">{inline(block.text, key)}</p>;
        if (block.kind === "ul")
          return (
            <ul key={key} className="list-disc space-y-1 pl-5 marker:text-accent">
              {block.items.map((item, i) => <li key={i}>{inline(item, `${key}-${i}`)}</li>)}
            </ul>
          );
        if (block.kind === "ol")
          return (
            <ol key={key} start={block.start} className="list-decimal space-y-1 pl-5 marker:font-semibold marker:text-accent">
              {block.items.map((item, i) => <li key={i}>{inline(item, `${key}-${i}`)}</li>)}
            </ol>
          );
        return (
          <p key={key}>
            {block.lines.map((line, i) => (
              <Fragment key={i}>
                {i > 0 && <br />}
                {inline(line, `${key}-${i}`)}
              </Fragment>
            ))}
          </p>
        );
      })}
    </div>
  );
}
