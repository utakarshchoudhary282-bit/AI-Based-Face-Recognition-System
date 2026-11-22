import { useState } from "react";

// Blue sequential ramp (light = few photos, dark = many).
const RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"];

export function ConfusionMatrix({ matrix, classes }) {
  const [hover, setHover] = useState(null);
  if (!matrix?.length) return null;
  const max = Math.max(1, ...matrix.flat());
  const color = (v) => (v === 0 ? "var(--surface-2)" : RAMP[Math.min(RAMP.length - 1, Math.floor((v / max) * (RAMP.length - 1)))]);
  const darkText = (v) => v / max > 0.45;
  return (
    <figure className="viz">
      <figcaption>Confusion matrix - rows: true person, columns: predicted</figcaption>
      <div className="cm-wrap">
        <table className="cm">
          <thead>
            <tr><th></th>{classes.map((c) => <th key={c} scope="col"><span>{c}</span></th>)}</tr>
          </thead>
          <tbody>
            {matrix.map((row, i) => (
              <tr key={classes[i]}>
                <th scope="row">{classes[i]}</th>
                {row.map((v, j) => (
                  <td key={j} style={{ background: color(v), color: darkText(v) ? "#fff" : "var(--text-primary)" }}
                    className={(i === j ? "diag " : "") + (hover && hover[0] === i && hover[1] === j ? "hover" : "")}
                    onMouseEnter={() => setHover([i, j])} onMouseLeave={() => setHover(null)}
                    title={`True ${classes[i]}, predicted ${classes[j]}: ${v}`}>
                    {v || ""}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted small">
        {hover ? `True ${classes[hover[0]]} → predicted ${classes[hover[1]]}: ${matrix[hover[0]][hover[1]]} image(s)` :
          "Diagonal = correct. Off-diagonal cells show which people the model confuses."}
      </p>
    </figure>
  );
}
