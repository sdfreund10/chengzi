import type { StudySession } from './api'

const MODE_LABELS: Record<string, string> = {
  pinyin_to_en: 'Pinyin to English',
  en_to_zh: 'English to Chinese',
  zh_to_en: 'Chinese to English',
}

type StudyProps = {
  session: StudySession
  onExit: () => void
}

export function Study({ session, onExit }: StudyProps) {
  const card = session.cards[0]
  if (!card) {
    return (
      <main class="app">
        <h1 class="title">No cards</h1>
        <div class="picker-actions">
          <button type="button" class="cta" onClick={onExit}>
            Back to decks
          </button>
        </div>
      </main>
    )
  }

  const modeLabel = MODE_LABELS[card.mode] ?? card.mode

  return (
    <main class="app study">
      <div class="study-shell">
        <div class="study-top">
          <div class="study-top-main">
            <span class="chip">{modeLabel}</span>
            <span class="muted">
              1 / {session.total}
            </span>
          </div>
          <button type="button" class="text-btn" onClick={onExit}>
            Exit
          </button>
        </div>

        <p class="prompt zh pinyin">{card.prompt}</p>
        <p class="hint">Tap anywhere to reveal</p>
      </div>
    </main>
  )
}
