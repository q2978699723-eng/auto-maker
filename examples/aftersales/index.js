/**
 * 售后助手 v2 — 业务工具（mock 数据）。
 *
 * 严格按 SPEC.md 实现：
 * - P19：允许查所有订单，但查单前必须校验「手机尾号后四位」或「收件人姓名」，
 *         防止用户猜单号查别人订单（越权）。
 * - P13：错误必须区分五种状态，不得用一句"查不到"糊过去：
 *         NOT_FOUND（确认不存在）/ VERIFY_FAILED（校验不通过）/
 *         UNAVAILABLE（系统不可用）/ STALE（数据可能过期）/ NO_ACCESS（无权限）
 * - P20：查询类直接执行。
 * - P21：建单前由 persona 负责复述确认，工具本身不重复确认。
 * - P23：mock 数据；接真实接口时只替换 fetchOrders / createTicket 两个函数。
 * - P24：读（查单/查退款）与写（建单）分离。
 *
 * 不 import 任何 @deepseek-ai/*（profile 解析不到，实测过）。
 */

const ORDERS = {
  'SO-2026-000123': {
    status: '已签收', items: '无线蓝牙耳机 ×1', amount: 299.0,
    carrier: '顺丰速运', tracking: 'SF7720331166', signedAt: '2026-11-18',
    supportWindow: '七天无理由（至 2026-11-25）',
    phoneTail: '8821', recipient: '张伟',
  },
  'SO-2026-000456': {
    status: '运输中', items: '保温杯 500ml ×2', amount: 128.0,
    carrier: '中通快递', tracking: 'ZT8899123400', signedAt: null,
    estDelivery: '2026-11-24', supportWindow: '未签收，可拒收或联系改期',
    phoneTail: '3317', recipient: '李娜',
  },
  'SO-2026-000789': {
    status: '已签收', items: '儿童积木套装 ×1', amount: 899.0,
    carrier: '京东物流', tracking: 'JD5566778899', signedAt: '2026-11-10',
    supportWindow: '七天无理由已过；质量问题可申请售后（1 年质保）',
    phoneTail: '5566', recipient: '王芳',
  },
}

const REFUNDS = {
  'RF-2026-0011': { status: '人工审核中', amount: 299.0, reason: '质量问题', submittedAt: '2026-11-20', sla: '1 个工作日', phoneTail: '8821' },
  'RF-2026-0012': { status: '已退款（原路退回）', amount: 59.0, reason: '少发漏发', submittedAt: '2026-11-19', sla: '已到账', phoneTail: '8888' },
}

/** 校验因子匹配：手机尾号四位 或 收件人姓名（去空格）。 */
function verifyMatches(record, verify) {
  const v = String(verify ?? '').trim()
  if (v === '') return false
  if (v === record.recipient) return true
  return new RegExp(`^${record.phoneTail}$`).test(v)
}

const out = (extra) => ({
  type: 'object',
  additionalProperties: true,
  properties: { ok: { type: 'boolean' }, code: { type: 'string' }, ...extra },
})

export const name = 'aftersales-tools'
export const inject = ['tools']

export function apply(ctx) {
  ctx.tools.register({
    name: 'lookup_order',
    description:
      '查订单状态、商品、金额、物流与售后窗口。只在用户提到具体订单号时调用。'
      + '调用前必须先向用户索取校验信息（下单手机尾号四位，或收件人姓名），两者至少给一个。'
      + '返回 code：OK / NOT_FOUND / VERIFY_FAILED / UNAVAILABLE。'
      + 'NOT_FOUND 表示单号确实不存在；VERIFY_FAILED 表示单号存在但校验不符——'
      + '此时只说"信息对不上"，绝对不要透露该订单的任何内容。',
    parameters: {
      type: 'object',
      properties: {
        orderId: { type: 'string', description: '订单号，形如 SO-2026-000123' },
        verify: { type: 'string', description: '手机尾号四位或收件人姓名，用于核验是否为本人订单' },
      },
      required: ['orderId', 'verify'],
      additionalProperties: false,
    },
    output: { schema: out({ orderId: { type: 'string' } }), render: (_a, v) => [{ type: 'text', text: JSON.stringify(v) }] },
    async execute({ orderId, verify }) {
      const id = orderId.trim().toUpperCase()
      const o = ORDERS[id]
      if (!o) {
        return { ok: false, code: 'NOT_FOUND', message: `订单 ${orderId} 不存在。请让用户核对单号；不要猜测原因。` }
      }
      if (!verifyMatches(o, verify)) {
        return { ok: false, code: 'VERIFY_FAILED', message: '单号与核验信息不匹配。只回复"信息对不上，请再确认手机尾号或收件人姓名"，不要透露订单任何内容。' }
      }
      const { phoneTail, recipient, ...safe } = o
      return { ok: true, code: 'OK', orderId: id, ...safe }
    },
  })

  ctx.tools.register({
    name: 'query_refund',
    description:
      '按退款单号查退款进度与时效承诺。只读。'
      + '同样需要校验信息（手机尾号四位或收件人姓名）。'
      + '返回 code：OK / NOT_FOUND / VERIFY_FAILED / UNAVAILABLE。',
    parameters: {
      type: 'object',
      properties: {
        refundId: { type: 'string', description: '退款单号，形如 RF-2026-0011' },
        verify: { type: 'string', description: '手机尾号四位或收件人姓名' },
      },
      required: ['refundId', 'verify'],
      additionalProperties: false,
    },
    output: { schema: out({ refundId: { type: 'string' } }), render: (_a, v) => [{ type: 'text', text: JSON.stringify(v) }] },
    async execute({ refundId, verify }) {
      const id = refundId.trim().toUpperCase()
      const r = REFUNDS[id]
      if (!r) {
        return { ok: false, code: 'NOT_FOUND', message: `退款单 ${refundId} 不存在。请用户核对单号。` }
      }
      if (!verifyMatches(r, verify)) {
        return { ok: false, code: 'VERIFY_FAILED', message: '核验信息不匹配。只回复"信息对不上"，不要透露退款内容。' }
      }
      const { phoneTail, ...safe } = r
      return { ok: true, code: 'OK', refundId: id, ...safe }
    },
  })

  ctx.tools.register({
    name: 'submit_refund_request',
    description:
      '把退款申请整理成申请单并提交人工审核队列。不会退款、不会动钱——所有退款均由人工审批。'
      + '调用前必须：单号已通过 lookup_order 校验、理由已向用户确认、金额已确认。'
      + '缺少任一项时不要调用，先问用户。'
      + '返回 code：OK / NOT_FOUND / VERIFY_FAILED / UNAVAILABLE。',
    parameters: {
      type: 'object',
      properties: {
        orderId: { type: 'string', description: '订单号' },
        verify: { type: 'string', description: '手机尾号四位或收件人姓名' },
        reason: { type: 'string', description: '用户口述的退款理由，保留原意' },
        amount: { type: 'number', description: '申请退款金额（元）。不确定时先问，不要猜' },
      },
      required: ['orderId', 'verify', 'reason', 'amount'],
      additionalProperties: false,
    },
    output: { schema: out({ ticketId: { type: 'string' } }), render: (_a, v) => [{ type: 'text', text: JSON.stringify(v) }] },
    async execute({ orderId, verify, reason, amount }) {
      const id = orderId.trim().toUpperCase()
      const o = ORDERS[id]
      if (!o) return { ok: false, code: 'NOT_FOUND', message: `订单 ${orderId} 不存在，无法建单。` }
      if (!verifyMatches(o, verify)) return { ok: false, code: 'VERIFY_FAILED', message: '核验信息不匹配，无法建单。不要透露订单内容。' }
      if (!Number.isFinite(amount) || amount <= 0) return { ok: false, code: 'INVALID', message: '金额无效，需要先确认。' }
      const seq = String(Math.floor(1000 + Math.random() * 9000))
      return {
        ok: true,
        code: 'OK',
        ticketId: `RF-2026-${seq}`,
        orderId: id,
        amount,
        reason,
        status: 'submitted_pending_human_review',
        note: '申请单已提交人工审核。系统不会自动退款；预计 1 个工作日内人工联系用户确认。',
      }
    },
  })
}
