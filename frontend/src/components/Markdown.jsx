import { marked } from "marked";
import { useMemo } from "react";

marked.setOptions({ gfm: true, breaks: true });

function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/** Renders markdown from our own API. Raw HTML is escaped first; [S1] citations become chips. */
export default function Markdown({ text, onCite }) {
  const html = useMemo(() => {
    const safe = escapeHtml(text || "");
    let out = marked.parse(safe);
    out = out.replace(/\[(S\d+)\]/g, '<button type="button" class="cite" data-cite="$1">$1</button>');
    return out;
  }, [text]);
  return (
    <div
      className="md"
      onClick={(e) => {
        const id = e.target?.dataset?.cite;
        if (id && onCite) onCite(id);
      }}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
