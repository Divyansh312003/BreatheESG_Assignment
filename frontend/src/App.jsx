import { useEffect, useState } from 'react'

import './App.css'

const EMPTY_DASHBOARD = {
  summary: {
    totalRecords: 0,
    pendingReview: 0,
    approved: 0,
    rejected: 0,
    flagged: 0,
    totalEstimatedKgCo2e: 0,
    byScope: { scope1: 0, scope2: 0, scope3: 0 },
    bySourceType: { sap: 0, utility: 0, travel: 0 },
  },
  records: [],
  imports: [],
  auditEvents: [],
}

const SOURCE_CARD_COPY = {
  sap: {
    title: 'SAP fuel + procurement',
    description:
      'Upload a flat export from SAP MM. The parser normalizes fuel rows into Scope 1 liters and procurement rows into spend-based Scope 3 activity.',
  },
  utility: {
    title: 'Utility electricity',
    description:
      'Upload a Green Button-style utility feed. Billing periods, tariff metadata, and interval totals are preserved for review.',
  },
  travel: {
    title: 'Corporate travel',
    description:
      'Sync a Concur-like demo feed with air, hotel, and ground receipts. Missing flight distance is derived from airport pairs when possible.',
  },
}

function formatNumber(value, digits = 0) {
  if (value === null || value === undefined) {
    return '0'
  }

  return new Intl.NumberFormat('en-US', {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value)
}

function formatDate(value) {
  if (!value) {
    return 'N/A'
  }

  return new Date(value).toLocaleDateString('en-GB', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function SummaryCard({ label, value, detail }) {
  return (
    <article className="summary-card">
      <p className="eyebrow">{label}</p>
      <h3>{value}</h3>
      <p>{detail}</p>
    </article>
  )
}

function ImportCard({ item }) {
  return (
    <article className="import-card">
      <div className="import-head">
        <div>
          <p className="eyebrow">{item.sourceType}</p>
          <h4>{item.sourceDocument || item.sourceType}</h4>
        </div>
        <span className={`status-pill status-${item.status.toLowerCase()}`}>
          {item.status.replaceAll('_', ' ')}
        </span>
      </div>
      <p className="import-meta">
        {item.acceptedCount} imported, {item.flaggedCount} flagged, {item.rejectedCount} rejected
      </p>
      {item.issues.length > 0 ? (
        <ul className="issue-list">
          {item.issues.map((issue) => (
            <li key={issue.id}>
              <strong>{issue.severity}</strong> {issue.message}
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted">No import issues recorded.</p>
      )}
    </article>
  )
}

function App() {
  const [referenceData, setReferenceData] = useState({
    tenants: [],
    facilities: [],
    dataSources: [],
  })
  const [dashboard, setDashboard] = useState(EMPTY_DASHBOARD)
  const [selectedTenantId, setSelectedTenantId] = useState('')
  const [selectedSourceType, setSelectedSourceType] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('')
  const [selectedRecordId, setSelectedRecordId] = useState(null)
  const [reviewNote, setReviewNote] = useState('')
  const [analystName, setAnalystName] = useState('Demo Analyst')
  const [files, setFiles] = useState({ sap: null, utility: null })
  const [loading, setLoading] = useState(true)
  const [busyAction, setBusyAction] = useState('')
  const [banner, setBanner] = useState('')

  async function loadReferenceData() {
    const response = await fetch('/api/v1/reference-data')
    const payload = await response.json()
    setReferenceData(payload)
    if (!selectedTenantId && payload.tenants.length > 0) {
      setSelectedTenantId(String(payload.tenants[0].id))
    }
  }

  async function loadDashboard(activeTenantId = selectedTenantId) {
    const search = new URLSearchParams()
    if (activeTenantId) {
      search.set('tenantId', activeTenantId)
    }
    if (selectedSourceType) {
      search.set('sourceType', selectedSourceType)
    }
    if (selectedStatus) {
      search.set('status', selectedStatus)
    }

    const response = await fetch(`/api/v1/dashboard?${search.toString()}`)
    const payload = await response.json()
    setDashboard(payload)
    if (!selectedRecordId && payload.records.length > 0) {
      setSelectedRecordId(payload.records[0].id)
      setReviewNote(payload.records[0].reviewNote || '')
    }
  }

  useEffect(() => {
    async function bootstrap() {
      setLoading(true)
      await loadReferenceData()
      setLoading(false)
    }

    bootstrap()
  }, [])

  useEffect(() => {
    if (!selectedTenantId) {
      return
    }

    loadDashboard(selectedTenantId)
  }, [selectedTenantId, selectedSourceType, selectedStatus])

  useEffect(() => {
    const selected = dashboard.records.find((record) => record.id === selectedRecordId)
    if (selected) {
      setReviewNote(selected.reviewNote || '')
    } else if (dashboard.records.length > 0) {
      setSelectedRecordId(dashboard.records[0].id)
      setReviewNote(dashboard.records[0].reviewNote || '')
    }
  }, [dashboard.records, selectedRecordId])

  const selectedRecord = dashboard.records.find((record) => record.id === selectedRecordId) || null

  async function uploadSource(kind) {
    const selectedFile = files[kind]
    if (!selectedTenantId || !selectedFile) {
      setBanner('Choose a tenant and a file before uploading.')
      return
    }

    setBusyAction(kind)
    setBanner('')
    const formData = new FormData()
    formData.append('tenantId', selectedTenantId)
    formData.append('actor', analystName)
    formData.append('file', selectedFile)

    const response = await fetch(`/api/v1/imports/${kind}`, {
      method: 'POST',
      body: formData,
    })
    const payload = await response.json()
    setBusyAction('')

    if (!response.ok) {
      setBanner(payload.error || 'Import failed.')
      return
    }

    setFiles((current) => ({ ...current, [kind]: null }))
    setBanner(`Imported ${kind.toUpperCase()} data successfully.`)
    await loadDashboard(selectedTenantId)
  }

  async function syncTravelDemo() {
    if (!selectedTenantId) {
      setBanner('Choose a tenant before syncing travel data.')
      return
    }

    setBusyAction('travel')
    setBanner('')
    const response = await fetch('/api/v1/imports/travel-sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tenantId: Number(selectedTenantId), actor: analystName }),
    })
    const payload = await response.json()
    setBusyAction('')

    if (!response.ok) {
      setBanner(payload.error || 'Travel sync failed.')
      return
    }

    setBanner('Synced travel demo feed successfully.')
    await loadDashboard(selectedTenantId)
  }

  async function submitReview(reviewStatus) {
    if (!selectedRecord) {
      return
    }

    setBusyAction(reviewStatus)
    setBanner('')
    const response = await fetch(`/api/v1/records/${selectedRecord.id}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reviewStatus,
        actor: analystName,
        note: reviewNote,
      }),
    })
    const payload = await response.json()
    setBusyAction('')

    if (!response.ok) {
      setBanner(payload.error || 'Review update failed.')
      return
    }

    setBanner(`Record ${payload.record.externalId} marked ${reviewStatus}.`)
    await loadDashboard(selectedTenantId)
  }

  if (loading) {
    return (
      <main className="page-shell">
        <section className="panel loading-panel">
          <p className="eyebrow">Loading</p>
          <h1>Preparing the emissions review workspace…</h1>
        </section>
      </main>
    )
  }

  return (
    <main className="page-shell">
      <section className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">Breathe ESG Prototype</p>
          <h1>Ingest messy enterprise data. Normalize it. Let analysts sign off with context.</h1>
          <p>
            This prototype models the real onboarding problem in the assignment: SAP exports, utility
            feeds, and travel receipts land in different shapes, then converge into one review queue
            with audit history and source-of-truth traceability.
          </p>
        </div>
        <div className="hero-controls">
          <label>
            Tenant
            <select value={selectedTenantId} onChange={(event) => setSelectedTenantId(event.target.value)}>
              {referenceData.tenants.map((tenant) => (
                <option key={tenant.id} value={tenant.id}>
                  {tenant.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Analyst
            <input value={analystName} onChange={(event) => setAnalystName(event.target.value)} />
          </label>
          <label>
            Source filter
            <select value={selectedSourceType} onChange={(event) => setSelectedSourceType(event.target.value)}>
              <option value="">All sources</option>
              <option value="SAP">SAP</option>
              <option value="UTILITY">Utility</option>
              <option value="TRAVEL">Travel</option>
            </select>
          </label>
          <label>
            Review filter
            <select value={selectedStatus} onChange={(event) => setSelectedStatus(event.target.value)}>
              <option value="">All statuses</option>
              <option value="PENDING">Pending</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </label>
        </div>
      </section>

      {banner ? <div className="banner">{banner}</div> : null}

      <section className="summary-grid">
        <SummaryCard
          label="Records in ledger"
          value={formatNumber(dashboard.summary.totalRecords)}
          detail={`${formatNumber(dashboard.summary.flagged)} flagged for review`}
        />
        <SummaryCard
          label="Pending analyst sign-off"
          value={formatNumber(dashboard.summary.pendingReview)}
          detail={`${formatNumber(dashboard.summary.approved)} approved so far`}
        />
        <SummaryCard
          label="Estimated emissions"
          value={`${formatNumber(dashboard.summary.totalEstimatedKgCo2e, 1)} kg`}
          detail="Prototype coefficients only, not auditor-grade factors"
        />
        <SummaryCard
          label="Scope mix"
          value={`${dashboard.summary.byScope.scope1}/${dashboard.summary.byScope.scope2}/${dashboard.summary.byScope.scope3}`}
          detail="Scope 1 / Scope 2 / Scope 3 records"
        />
      </section>

      <section className="panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">Ingestion</p>
            <h2>Source connectors</h2>
          </div>
          <p className="muted">Download the bundled samples or upload your own realistic source extracts.</p>
        </div>

        <div className="source-grid">
          <article className="source-card">
            <p className="eyebrow">SAP</p>
            <h3>{SOURCE_CARD_COPY.sap.title}</h3>
            <p>{SOURCE_CARD_COPY.sap.description}</p>
            <div className="source-actions">
              <a href="/api/v1/sample-files/sap">Download sample CSV</a>
              <input
                type="file"
                accept=".csv"
                onChange={(event) =>
                  setFiles((current) => ({ ...current, sap: event.target.files?.[0] || null }))
                }
              />
              <button type="button" onClick={() => uploadSource('sap')} disabled={busyAction === 'sap'}>
                {busyAction === 'sap' ? 'Uploading…' : 'Upload SAP export'}
              </button>
            </div>
          </article>

          <article className="source-card">
            <p className="eyebrow">Utility</p>
            <h3>{SOURCE_CARD_COPY.utility.title}</h3>
            <p>{SOURCE_CARD_COPY.utility.description}</p>
            <div className="source-actions">
              <a href="/api/v1/sample-files/utility">Download sample XML</a>
              <input
                type="file"
                accept=".xml"
                onChange={(event) =>
                  setFiles((current) => ({ ...current, utility: event.target.files?.[0] || null }))
                }
              />
              <button
                type="button"
                onClick={() => uploadSource('utility')}
                disabled={busyAction === 'utility'}
              >
                {busyAction === 'utility' ? 'Uploading…' : 'Upload utility feed'}
              </button>
            </div>
          </article>

          <article className="source-card">
            <p className="eyebrow">Travel</p>
            <h3>{SOURCE_CARD_COPY.travel.title}</h3>
            <p>{SOURCE_CARD_COPY.travel.description}</p>
            <div className="source-actions">
              <a href="/api/v1/sample-files/travel">Download demo JSON</a>
              <button type="button" onClick={syncTravelDemo} disabled={busyAction === 'travel'}>
                {busyAction === 'travel' ? 'Syncing…' : 'Sync Concur demo feed'}
              </button>
            </div>
          </article>
        </div>
      </section>

      <section className="workspace-grid">
        <article className="panel">
          <div className="section-head">
            <div>
              <p className="eyebrow">Review queue</p>
              <h2>Normalized activity records</h2>
            </div>
            <p className="muted">Select a record to inspect the raw payload, normalized values, and analyst controls.</p>
          </div>

          <div className="record-table">
            <div className="table-head">
              <span>Record</span>
              <span>Source</span>
              <span>Scope</span>
              <span>Status</span>
              <span>Flagged</span>
            </div>
            {dashboard.records.map((record) => (
              <button
                type="button"
                key={record.id}
                className={`table-row ${record.id === selectedRecordId ? 'is-selected' : ''}`}
                onClick={() => {
                  setSelectedRecordId(record.id)
                  setReviewNote(record.reviewNote || '')
                }}
              >
                <span>
                  <strong>{record.description}</strong>
                  <small>{record.facilityName}</small>
                </span>
                <span>{record.sourceType}</span>
                <span>{record.scope.replace('SCOPE_', 'Scope ')}</span>
                <span>{record.reviewStatus}</span>
                <span>{record.suspicionScore > 0 ? `${record.suspicionScore} issues` : 'Clean'}</span>
              </button>
            ))}
          </div>
        </article>

        <article className="panel detail-panel">
          <div className="section-head">
            <div>
              <p className="eyebrow">Analyst detail</p>
              <h2>{selectedRecord ? selectedRecord.externalId : 'Select a record'}</h2>
            </div>
          </div>

          {selectedRecord ? (
            <>
              <div className="detail-metadata">
                <div>
                  <span className="meta-label">Facility</span>
                  <strong>{selectedRecord.facilityName}</strong>
                </div>
                <div>
                  <span className="meta-label">Date</span>
                  <strong>{formatDate(selectedRecord.activityDate)}</strong>
                </div>
                <div>
                  <span className="meta-label">Estimated kgCO2e</span>
                  <strong>{formatNumber(selectedRecord.estimatedKgCo2e || 0, 1)}</strong>
                </div>
              </div>

              <div className="flag-list">
                {selectedRecord.suspicionReasons.length > 0 ? (
                  selectedRecord.suspicionReasons.map((reason) => (
                    <span key={reason} className="flag-pill">
                      {reason}
                    </span>
                  ))
                ) : (
                  <span className="flag-pill flag-pill-clean">No suspicion flags on this record.</span>
                )}
              </div>

              <label className="note-box">
                Analyst note
                <textarea
                  value={reviewNote}
                  onChange={(event) => setReviewNote(event.target.value)}
                  placeholder="Explain what you validated or why you rejected the row."
                />
              </label>

              <div className="action-row">
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => submitReview('REJECTED')}
                  disabled={busyAction === 'REJECTED'}
                >
                  {busyAction === 'REJECTED' ? 'Rejecting…' : 'Reject'}
                </button>
                <button
                  type="button"
                  className="solid-button"
                  onClick={() => submitReview('APPROVED')}
                  disabled={busyAction === 'APPROVED'}
                >
                  {busyAction === 'APPROVED' ? 'Approving…' : 'Approve + lock'}
                </button>
              </div>

              <div className="payload-grid">
                <div>
                  <p className="eyebrow">Normalized payload</p>
                  <pre>{JSON.stringify(selectedRecord.normalizedPayload, null, 2)}</pre>
                </div>
                <div>
                  <p className="eyebrow">Raw source payload</p>
                  <pre>{JSON.stringify(selectedRecord.sourcePayload, null, 2)}</pre>
                </div>
              </div>
            </>
          ) : (
            <p className="muted">Choose a record from the queue to review it.</p>
          )}
        </article>
      </section>

      <section className="history-grid">
        <article className="panel">
          <div className="section-head">
            <div>
              <p className="eyebrow">Import history</p>
              <h2>Recent ingestion runs</h2>
            </div>
          </div>
          <div className="stack-list">
            {dashboard.imports.map((item) => (
              <ImportCard key={item.id} item={item} />
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="section-head">
            <div>
              <p className="eyebrow">Audit feed</p>
              <h2>Latest analyst and import events</h2>
            </div>
          </div>
          <div className="audit-list">
            {dashboard.auditEvents.map((event) => (
              <article key={event.id} className="audit-entry">
                <div>
                  <p className="eyebrow">{event.eventType.replaceAll('_', ' ')}</p>
                  <h4>{event.message}</h4>
                </div>
                <span>{formatDate(event.createdAt)}</span>
              </article>
            ))}
          </div>
        </article>
      </section>
    </main>
  )
}

export default App
