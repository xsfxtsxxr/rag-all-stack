/** AI 服务地址（宿主机直连） */
export function aiUrl(): string {
  return process.env.AI_SERVICE_URL ?? 'http://localhost:8008'
}

/** 报价变更后通知 AI 服务重建报价向量索引（尽力而为，失败不阻塞业务） */
export function refreshQuoteIndex(): void {
  fetch(`${aiUrl()}/api/reindex-quotes`, { method: 'POST' }).catch(() => {
    // 索引刷新失败不影响报价 CRUD 结果，下次全量重索引时会兜底
  })
}
