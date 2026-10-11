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
        <header>
          <p class="eyebrow">juzi</p>
          <h1>No cards</h1>
        </header>
        <button type="button" class="btn ghost" onClick={onExit}>
          Back to decks
        </button>
      </main>
    )
  }

  const modeLabel = MODE_LABELS[card.mode] ?? card.mode

  return (
    <main class="app study">
      <header class="study-top">
        <div>
          <p class="eyebrow">{session.category.name}</p>
          <div class="study-meta">
            <span class="chip">{modeLabel}</span>
            <span class="muted">
              1 / {session.total}
            </span>
          </div>
        </div>
        <button type="button" class="btn ghost" onClick={onExit}>
          Exit
        </button>
      </header>

      <section class="study-card" aria-label="Study card">
        <p class="prompt zh pinyin">{card.prompt}</p>
        <p class="hint muted">Tap anywhere to reveal</p>
      </section>
    </main>
  )
}
