"use client";

import type { FormEvent } from "react";
import { useMemo, useState, useTransition } from "react";

import { createReservationAction, updateReservationAction } from "@/lib/api";
import type { ReservationAction } from "@/lib/types";
import { formatActionStatusLabel, formatActionTypeLabel } from "@/lib/presentation";

type ReservationActionsPanelProps = {
  reservationId: number;
  actionSupportEnabled: boolean;
  initialActions: ReservationAction[];
};

const ACTION_TYPE_OPTIONS = [
  { value: "call_guest", label: "Misafiri ara" },
  { value: "send_message", label: "Mesaj gönder" },
  { value: "request_deposit", label: "Depozito iste" },
  { value: "manual_review", label: "Manuel inceleme" },
];

export function ReservationActionsPanel({
  reservationId,
  actionSupportEnabled,
  initialActions,
}: ReservationActionsPanelProps) {
  const [actions, setActions] = useState(initialActions);
  const [actedBy, setActedBy] = useState("operations");
  const [actionType, setActionType] = useState("manual_review");
  const [actionNote, setActionNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const pendingSummary = useMemo(
    () => ({
      open: actions.filter((action) => action.action_status === "open").length,
      completed: actions.filter((action) => action.action_status === "completed").length,
      followUp: actions.filter((action) => action.action_status === "follow_up").length,
    }),
    [actions],
  );

  function handleCreateAction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    startTransition(async () => {
      try {
        const created = await createReservationAction(reservationId, {
          action_type: actionType,
          action_status: "open",
          action_note: actionNote,
          acted_by: actedBy,
        });
        setActions((current) => [created, ...current]);
        setActionNote("");
        setSuccess("Aksiyon kaydedildi.");
      } catch (createError) {
        setError(createError instanceof Error ? createError.message : "Aksiyon kaydedilemedi.");
      }
    });
  }

  function handleStatusUpdate(actionId: number, actionStatus: string) {
    setError(null);
    setSuccess(null);

    startTransition(async () => {
      try {
        const updated = await updateReservationAction(actionId, { action_status: actionStatus });
        setActions((current) => current.map((action) => (action.id === updated.id ? updated : action)));
        setSuccess("Aksiyon durumu güncellendi.");
      } catch (updateError) {
        setError(updateError instanceof Error ? updateError.message : "Aksiyon güncellenemedi.");
      }
    });
  }

  if (!actionSupportEnabled) {
    return (
      <div className="empty-state">
        Aksiyon akışı yalnızca DB-backed operasyon modunda açıktır. Artifact fallback modunda bu alan read-only kalır.
      </div>
    );
  }

  return (
    <div className="stack">
      <div className="summary-band">
        <div className="summary-cell">
          Açık aksiyon
          <strong>{pendingSummary.open}</strong>
        </div>
        <div className="summary-cell">
          Tamamlanan
          <strong>{pendingSummary.completed}</strong>
        </div>
        <div className="summary-cell">
          Takip gereken
          <strong>{pendingSummary.followUp}</strong>
        </div>
      </div>

      <form className="stack" onSubmit={handleCreateAction}>
        <div className="filters">
          <div className="field">
            <label htmlFor="acted_by">İşlemi yapan</label>
            <input id="acted_by" value={actedBy} onChange={(event) => setActedBy(event.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="action_type">Aksiyon tipi</label>
            <select id="action_type" value={actionType} onChange={(event) => setActionType(event.target.value)}>
              {ACTION_TYPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="field">
          <label htmlFor="action_note">Not</label>
          <textarea
            id="action_note"
            className="textarea"
            rows={4}
            value={actionNote}
            onChange={(event) => setActionNote(event.target.value)}
            placeholder="Örneğin: girişten 48 saat önce tekrar aranacak."
          />
        </div>
        <div className="section-note">
          <button className="button" type="submit" disabled={isPending}>
            {isPending ? "Kaydediliyor" : "Aksiyon ekle"}
          </button>
          {error ? <span className="error-text">{error}</span> : null}
          {success ? <span className="success-text">{success}</span> : null}
        </div>
      </form>

      {actions.length === 0 ? (
        <div className="empty-state">Bu rezervasyon için henüz aksiyon kaydı yok.</div>
      ) : (
        <div className="status-list">
          {actions.map((action) => (
            <article key={action.id} className="status-item">
              <div className="panel-header">
                <div>
                  <h3>{formatActionTypeLabel(action.action_type)}</h3>
                  <p className="muted">
                    {action.acted_by} · {new Date(action.acted_at).toLocaleString("tr-TR")}
                  </p>
                </div>
                <span className="pill">{formatActionStatusLabel(action.action_status)}</span>
              </div>
              <p className="muted">{action.action_note || "Not girilmedi."}</p>
              <div className="section-note">
                {action.action_status !== "completed" ? (
                  <button
                    type="button"
                    className="button button-secondary"
                    disabled={isPending}
                    onClick={() => handleStatusUpdate(action.id, "completed")}
                  >
                    Tamamlandı
                  </button>
                ) : null}
                {action.action_status !== "follow_up" ? (
                  <button
                    type="button"
                    className="button button-secondary"
                    disabled={isPending}
                    onClick={() => handleStatusUpdate(action.id, "follow_up")}
                  >
                    Takibe al
                  </button>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
