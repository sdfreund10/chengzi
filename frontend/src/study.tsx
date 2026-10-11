import { useState } from 'preact/hooks'
import type { StudyCard, StudySession } from './api'
import { CaughtUp } from './caughtUp'
import {
  cardPrompt,
  cardReveal,
  gradeEasy,
  gradeHard,
  type DisplayLine,
} from './studyCard'

const MODE_LABELS: Record<string, string> = {
  pinyin_to_en: 'Pinyin to English',
  en_to_zh: 'English to Chinese',
  zh_to_en: 'Chinese to English',
}

type StudyProps = {
  session: StudySession
  onExit: () => void
}

function lineClass(line: DisplayLine, role: 'prompt' | 'answer'): string {
  const parts = [role === 'prompt' ? 'prompt-line' : 'answer-line', line.kind]
  if (line.kind === 'chinese') parts.push('zh')
  return parts.join(' ')
}

function DisplayLines({
  lines,
  role,
}: {
  lines: DisplayLine[]
  role: 'prompt' | 'answer'
}) {
  const paired = role === 'prompt' && lines.length === 2
  const linesBody = lines.map((line) => (
    <p key={`${line.kind}-${line.text}`} class={lineClass(line, role)}>
      {line.text}
    </p>
  ))
  return (
    <div class={role === 'prompt' ? 'prompt-block' : 'answer'}>
      {paired ? <div class="prompt-pair">{linesBody}</div> : linesBody}
    </div>
  )
}

export function Study({ session, onExit }: StudyProps) {
  const [queue, setQueue] = useState<StudyCard[]>(() => [...session.cards])
  const [revealed, setRevealed] = useState(false)

  const card = queue[0]
  if (!card) {
    return <CaughtUp onBack={onExit} />
  }

  const modeLabel = MODE_LABELS[card.mode] ?? card.mode
  const promptLines = cardPrompt(card)
  const revealLines = cardReveal(card)

  function onGrade(hard: boolean) {
    setQueue((prev) => (hard ? gradeHard(prev) : gradeEasy(prev)))
    setRevealed(false)
  }

  return (
    <main class="app study">
      <div class={`study-shell${revealed ? ' revealed' : ''}`}>
        <div class="study-top">
          <div class="study-top-main">
            <span class="chip">{modeLabel}</span>
            <span class="muted">
              {queue.length} / {session.total}
            </span>
          </div>
          <button type="button" class="text-btn" onClick={onExit}>
            Exit
          </button>
        </div>

        {revealed ? (
          <>
            <div class="study-body">
              <DisplayLines lines={promptLines} role="prompt" />
              <DisplayLines lines={revealLines} role="answer" />
            </div>
            <div class="grade-zones" aria-label="Grade card">
              <button
                type="button"
                class="grade-zone hard"
                onClick={() => onGrade(true)}
              >
                Hard
                <small>back soon</small>
              </button>
              <button
                type="button"
                class="grade-zone easy"
                onClick={() => onGrade(false)}
              >
                Easy
                <small>later</small>
              </button>
            </div>
          </>
        ) : (
          <div
            class="study-body reveal-target"
            onClick={() => setRevealed(true)}
            role="button"
            tabIndex={0}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault()
                setRevealed(true)
              }
            }}
          >
            <DisplayLines lines={promptLines} role="prompt" />
            <p class="hint">Tap anywhere to reveal</p>
          </div>
        )}
      </div>
    </main>
  )
}
