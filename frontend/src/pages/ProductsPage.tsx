import { useEffect, useState } from "react";
import { api } from "../api/client";
type P = { id: number; name: string; ferment_min: number; bake_min: number; proof_off_oven: boolean };
export default function ProductsPage() {
  const [rows, setRows] = useState<P[]>([]);
  const [err, setErr] = useState("");
  useEffect(() => { api<P[]>("/products").then(setRows); }, []);
  async function toggle(p: P, checked: boolean) {
    setErr("");
    // 先本地生效，失败再回滚
    setRows(rs => rs.map(r => r.id === p.id ? { ...r, proof_off_oven: checked } : r));
    try {
      await api<P>(`/products/${p.id}`, { method: "PATCH", body: JSON.stringify({ proof_off_oven: checked }) });
    } catch (e) {
      setRows(rs => rs.map(r => r.id === p.id ? { ...r, proof_off_oven: p.proof_off_oven } : r));
      setErr(e instanceof Error ? e.message : String(e));
    }
  }
  return (<>
    <h2>产品（配方时长）</h2>
    {err && <div className="err">{err}</div>}
    <table className="table"><thead><tr><th>名称</th><th>发酵 min</th><th>烘烤 min</th><th>合计</th><th>离炉醒发</th><th>占炉 min</th></tr></thead>
    <tbody>{rows.map(p => <tr key={p.id}><td>{p.name}</td><td className="mono">{p.ferment_min}</td><td className="mono">{p.bake_min}</td><td className="mono">{p.ferment_min + p.bake_min}</td>
      <td><label className="proof-toggle"><input type="checkbox" checked={p.proof_off_oven} onChange={e => toggle(p, e.target.checked)} /> 醒发不占炉</label></td>
      <td className="mono">{p.proof_off_oven ? p.bake_min : p.ferment_min + p.bake_min}</td></tr>)}</tbody></table>
  </>);
}
