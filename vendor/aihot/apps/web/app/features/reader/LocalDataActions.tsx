import { useRef, useState } from "react";
import { SITE } from "@aihot/industry/site";
import { exportBundle, importBundle } from "../../lib/local-state";

export function LocalDataActions() {
  const file = useRef<HTMLInputElement>(null);
  const [notice, setNotice] = useState("");
  const download = () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(exportBundle(), null, 2)], { type: "application/json" }));
    const link = document.createElement("a"); link.href = url;
    link.download = `${SITE.mcpPrefix}-local-data-${new Date().toISOString().slice(0, 10)}.json`;
    link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  return <div>
    <div className="flex flex-wrap gap-4 text-[13px] text-accent">
      <button type="button" onClick={download}>导出本机数据</button>
      <button type="button" onClick={() => file.current?.click()}>导入文件</button>
      <input ref={file} aria-label="导入本机数据" type="file" accept="application/json,.json" className="sr-only" onChange={async (event) => {
        const selected = event.target.files?.[0]; event.target.value = "";
        if (!selected) return;
        try {
          const r = importBundle(await selected.text());
          setNotice(`新增收藏 ${r.starredAdded} 条、已读标记 ${r.readAdded} 条、个人记录 ${r.personalAdded} 条。${r.starredSkipped + r.readSkipped + r.personalSkipped ? `跳过无效或超限记录 ${r.starredSkipped + r.readSkipped + r.personalSkipped} 条。` : ""}${r.readFailed || r.personalFailed ? "部分记录未能保存，请检查浏览器存储。" : "已有记录已保留。"}`);
        } catch (error) { setNotice(error instanceof Error ? error.message : "导入失败。"); }
      }} />
    </div>
    {notice && <p role="status" className="mt-2 text-[13px] text-ink-3">{notice}</p>}
  </div>;
}
