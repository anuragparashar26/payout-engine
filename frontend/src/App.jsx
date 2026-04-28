import { useEffect, useMemo, useRef, useState } from 'react'

const API_BASE = ''

const MERCHANTS = [
  { label: 'Ravi Textiles', token: 'ravi-token-dev' },
  { label: 'Priya Design Co', token: 'priya-token-dev' },
  { label: 'Mehul Exports', token: 'mehul-token-dev' },
]

const statusBadge = {
  pending: 'bg-blue-900/50 text-blue-300 border border-blue-700',
  processing: 'bg-amber-900/50 text-amber-300 border border-amber-700',
  completed: 'bg-emerald-900/50 text-emerald-300 border border-emerald-700',
  failed: 'bg-rose-900/50 text-rose-300 border border-rose-700',
}

const typeColor = {
  credit: 'text-emerald-400',
  debit: 'text-rose-400',
}

const formatRupees = (paise) =>
  (paise / 100).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })

const formatDate = (value) => new Date(value).toLocaleString('en-IN')

function App() {
  const [selectedToken, setSelectedToken] = useState(MERCHANTS[0].token)
  const [balance, setBalance] = useState({ available_paise: 0, held_paise: 0, total_paise: 0 })
  const [payouts, setPayouts] = useState([])
  const [ledger, setLedger] = useState([])
  const [bankAccounts, setBankAccounts] = useState([])
  const [amountRupees, setAmountRupees] = useState('')
  const [selectedBankAccount, setSelectedBankAccount] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  const idempotencyKeyRef = useRef(globalThis.crypto.randomUUID())
  const selectedMerchant = useMemo(
    () => MERCHANTS.find((merchant) => merchant.token === selectedToken),
    [selectedToken],
  )

  const request = async (path, options = {}) => {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Authorization': `Token ${selectedToken}`,
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    })
    const body = await response.json().catch(() => ({}))
    return { response, body }
  }

  const loadAll = async () => {
    const [balanceRes, payoutsRes, ledgerRes, bankRes] = await Promise.all([
      request('/api/v1/balance/'),
      request('/api/v1/payouts/'),
      request('/api/v1/ledger/'),
      request('/api/v1/bank-accounts/'),
    ])

    if (balanceRes.response.ok) {
      setBalance(balanceRes.body)
    }
    if (payoutsRes.response.ok) {
      setPayouts(payoutsRes.body)
    }
    if (ledgerRes.response.ok) {
      setLedger(ledgerRes.body)
    }
    if (bankRes.response.ok) {
      setBankAccounts(bankRes.body)
      const hasSelected = bankRes.body.some((bank) => bank.id === selectedBankAccount)
      if (!hasSelected) {
        setSelectedBankAccount(bankRes.body[0]?.id || '')
      }
    }
  }

  useEffect(() => {
    loadAll()
    const intervalId = window.setInterval(loadAll, 5000)
    return () => window.clearInterval(intervalId)
  }, [selectedToken])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setErrorMessage('')

    const amountPaise = Math.round(Number(amountRupees) * 100)
    if (!selectedBankAccount || amountPaise <= 0) {
      setErrorMessage('Enter a valid amount and choose a bank account.')
      return
    }

    setIsSubmitting(true)
    const { response, body } = await request('/api/v1/payouts/', {
      method: 'POST',
      headers: {
        'Idempotency-Key': idempotencyKeyRef.current,
      },
      body: JSON.stringify({
        amount_paise: amountPaise,
        bank_account_id: selectedBankAccount,
      }),
    })

    if (response.status === 201) {
      setAmountRupees('')
      idempotencyKeyRef.current = globalThis.crypto.randomUUID()
      await loadAll()
    } else if (response.status === 402) {
      setErrorMessage('Insufficient funds for this payout request.')
    } else {
      setErrorMessage(body.error || 'Unable to create payout right now.')
    }
    setIsSubmitting(false)
  }

  return (
    <main className="mx-auto min-h-screen max-w-7xl p-4 md:p-8">
      <header className="mb-6 rounded-3xl border border-white/10 bg-gradient-header backdrop-blur-sm p-6 shadow-lg shadow-black/40">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-400">Playto Payout Engine</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-white md:text-4xl">Merchant payout control panel</h1>
          </div>
          <label className="flex flex-col gap-1 text-sm font-medium text-slate-300">
            Merchant
            <select
              className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-white backdrop-blur-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 focus:outline-none transition"
              value={selectedToken}
              onChange={(event) => {
                setSelectedToken(event.target.value)
                setErrorMessage('')
              }}
            >
              {MERCHANTS.map((merchant) => (
                <option key={merchant.token} value={merchant.token}>
                  {merchant.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </header>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <article className="rounded-2xl border border-blue-500/30 bg-gradient-card backdrop-blur-sm p-5 shadow-lg shadow-black/30">
          <p className="text-sm font-medium text-blue-400">Available</p>
          <p className="mt-2 text-3xl font-bold text-white">INR {formatRupees(balance.available_paise)}</p>
        </article>
        <article className="rounded-2xl border border-white/10 bg-gradient-card backdrop-blur-sm p-5 shadow-lg shadow-black/30">
          <p className="text-sm font-medium text-slate-400">Held</p>
          <p className="mt-2 text-3xl font-bold text-white">INR {formatRupees(balance.held_paise)}</p>
        </article>
        <article className="rounded-2xl border border-white/10 bg-gradient-card backdrop-blur-sm p-5 shadow-lg shadow-black/30">
          <p className="text-sm font-medium text-slate-400">Total</p>
          <p className="mt-2 text-3xl font-bold text-white">INR {formatRupees(balance.total_paise)}</p>
        </article>
      </section>

      <section className="mt-6 rounded-3xl border border-white/10 bg-gradient-card backdrop-blur-sm p-5 shadow-lg shadow-black/30">
        <h2 className="text-xl font-semibold text-white">Request payout</h2>
        <p className="text-sm text-slate-400">Merchant token: {selectedMerchant?.token}</p>
        <form className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-4" onSubmit={handleSubmit}>
          <label className="flex flex-col gap-1 text-sm font-medium text-slate-300 md:col-span-2">
            Amount (INR)
            <input
              type="number"
              min="1"
              step="0.01"
              value={amountRupees}
              onChange={(event) => setAmountRupees(event.target.value)}
              className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-white placeholder:text-slate-500 backdrop-blur-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 focus:outline-none transition"
              required
            />
          </label>
          <label className="flex flex-col gap-1 text-sm font-medium text-slate-300">
            Bank account
            <select
              value={selectedBankAccount}
              onChange={(event) => setSelectedBankAccount(event.target.value)}
              className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-white backdrop-blur-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 focus:outline-none transition"
              required
            >
              {bankAccounts.map((bank) => (
                <option key={bank.id} value={bank.id}>
                  {bank.name} ({bank.account_number})
                </option>
              ))}
            </select>
          </label>
          <button
            type="submit"
            className="rounded-xl bg-gradient-button px-4 py-2 text-sm font-semibold text-white transition hover:bg-gradient-button-hover focus:ring-2 focus:ring-blue-500/50 focus:outline-none disabled:cursor-not-allowed disabled:bg-blue-900/50 disabled:text-blue-400"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Submitting...' : 'Request payout'}
          </button>
        </form>
        {errorMessage && <p className="mt-3 text-sm font-medium text-rose-400">{errorMessage}</p>}
      </section>

      <section className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-2">
        <article className="overflow-x-auto rounded-3xl border border-white/10 bg-gradient-card backdrop-blur-sm p-5 shadow-lg shadow-black/30">
          <h2 className="mb-4 text-xl font-semibold text-white">Payout history</h2>
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400">
                <th className="pb-2">Created</th>
                <th className="pb-2">Amount</th>
                <th className="pb-2">Bank account</th>
                <th className="pb-2">Status</th>
                <th className="pb-2">Attempts</th>
              </tr>
            </thead>
            <tbody>
              {payouts.map((payout) => (
                <tr key={payout.id} className="border-t border-white/10 text-slate-300">
                  <td className="py-2 pr-4">{formatDate(payout.created_at)}</td>
                  <td className="py-2 pr-4">INR {formatRupees(payout.amount_paise)}</td>
                  <td className="py-2 pr-4">{payout.bank_account_name}</td>
                  <td className="py-2 pr-4">
                    <span className={`rounded-full px-2 py-1 text-xs font-semibold ${statusBadge[payout.status] || 'bg-blue-900/50 text-blue-300 border border-blue-700'}`}>
                      {payout.status}
                    </span>
                  </td>
                  <td className="py-2">{payout.attempts}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>

        <article className="overflow-x-auto rounded-3xl border border-white/10 bg-gradient-card backdrop-blur-sm p-5 shadow-lg shadow-black/30">
          <h2 className="mb-4 text-xl font-semibold text-white">Ledger</h2>
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400">
                <th className="pb-2">Created</th>
                <th className="pb-2">Type</th>
                <th className="pb-2">Amount</th>
                <th className="pb-2">Note</th>
              </tr>
            </thead>
            <tbody>
              {ledger.map((entry) => (
                <tr key={entry.id} className="border-t border-white/10 text-slate-300">
                  <td className="py-2 pr-4">{formatDate(entry.created_at)}</td>
                  <td className={`py-2 pr-4 font-semibold ${typeColor[entry.type] || 'text-slate-400'}`}>{entry.type}</td>
                  <td className="py-2 pr-4">INR {formatRupees(entry.amount_paise)}</td>
                  <td className="py-2">{entry.note || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>
      </section>
    </main>
  )
}

export default App