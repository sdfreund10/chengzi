import { useState } from 'preact/hooks'
import type { Category, Difficulty } from './api'

const OPTIONS: { id: Difficulty; label: string; detail: string }[] = [
  { id: 'beginner', label: 'Beginner', detail: 'HSK 1–3' },
  { id: 'intermediate', label: 'Intermediate', detail: 'HSK 4–5' },
  { id: 'advanced', label: 'Advanced', detail: 'HSK 6+' },
]

type DifficultyProps = {
  category: Category
  onBack: () => void
  onContinue: (difficulties: Difficulty[]) => void
}

export function DifficultyStep({ category, onBack, onContinue }: DifficultyProps) {
  const [selected, setSelected] = useState<Set<Difficulty>>(() => new Set())

  function toggle(id: Difficulty) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  function submit() {
    if (selected.size === 0) return
    onContinue(OPTIONS.map((opt) => opt.id).filter((id) => selected.has(id)))
  }

  return (
    <main class="app">
      <header class="app-header">
        <div>
          <p class="eyebrow">juzi</p>
          <h1>Difficulty</h1>
          <p class="lede">{category.name}</p>
        </div>
        <button type="button" class="btn ghost" onClick={onBack}>
          Back
        </button>
      </header>

      <section class="difficulty-grid" aria-label="Difficulty levels">
        {OPTIONS.map((opt) => {
          const isSelected = selected.has(opt.id)
          console.log(category)
          const count = category[`${opt.id}_count`]
          return (
            <button
              key={opt.id}
              type="button"
              class={`difficulty-option${isSelected ? ' selected' : ''}`}
              aria-pressed={isSelected}
              onClick={() => toggle(opt.id)}
            >
              <span class="difficulty-label">{opt.label}</span>
              <span class="difficulty-detail">{opt.detail}</span>
              {count ? <span class="difficulty-count">{count} words</span> : null}
            </button>
          )
        })}
      </section>

      <div class="picker-actions">
        <button
          type="button"
          class="btn"
          disabled={selected.size === 0}
          onClick={submit}
        >
          Build deck
        </button>
      </div>
    </main>
  )
}
