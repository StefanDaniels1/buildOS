<script setup lang="ts">
interface Step {
  department: string
  value: string
  issue: string
}

defineProps<{
  translations: {
    sectionLabel: string
    title: string
    subtitle: string
    steps: Step[]
    problemTitle: string
    problemText: string
    solutionTitle: string
    solutionText: string
    quote: string
    quoteHighlight: string
    quoteEnd: string
  }
}>()
</script>

<template>
  <section class="problem section">
    <div class="container">
      <!-- Section Header -->
      <div class="problem-header">
        <span class="section-label">{{ translations.sectionLabel }}</span>
        <h2 class="section-title">
          {{ translations.title }}
          <span class="subtitle">{{ translations.subtitle }}</span>
        </h2>
      </div>

      <!-- Problem Visualization -->
      <div class="problem-content">
        <!-- Timeline -->
        <div class="timeline">
          <div
            v-for="(step, index) in translations.steps"
            :key="index"
            class="timeline-step"
            :class="{ 'highlight': index === translations.steps.length - 1 }"
          >
            <div class="step-number">{{ index + 1 }}</div>
            <div class="step-content">
              <span class="step-department">{{ step.department }}</span>
              <span class="step-value">{{ step.value }}</span>
              <span class="step-issue">{{ step.issue }}</span>
            </div>
            <div v-if="index < translations.steps.length - 1" class="step-connector">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </div>
          </div>
        </div>

        <!-- Problem Statement -->
        <div class="problem-statement">
          <div class="statement-card">
            <div class="statement-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            </div>
            <div class="statement-content">
              <h3>{{ translations.problemTitle }}</h3>
              <p>{{ translations.problemText }}</p>
            </div>
          </div>

          <div class="statement-card solution">
            <div class="statement-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
            </div>
            <div class="statement-content">
              <h3>{{ translations.solutionTitle }}</h3>
              <p>{{ translations.solutionText }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Quote -->
      <div class="problem-quote">
        <blockquote>
          {{ translations.quote }} <span class="highlight">{{ translations.quoteHighlight }}</span> {{ translations.quoteEnd }}
        </blockquote>
      </div>
    </div>
  </section>
</template>

<style scoped>
.problem {
  background: var(--bg-secondary);
  position: relative;
  overflow: hidden;
}

.problem::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border-color), transparent);
}

/* Header */
.problem-header {
  text-align: center;
  margin-bottom: var(--spacing-4xl);
}

.problem-header .section-title {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.problem-header .subtitle {
  font-size: var(--font-size-lg);
  font-weight: 400;
  color: var(--text-muted);
}

/* Timeline */
.timeline {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-4xl);
  padding: var(--spacing-xl);
  background: var(--card-bg);
  border-radius: var(--radius-2xl);
  border: 1px solid var(--border-color);
  overflow-x: auto;
}

.timeline-step {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  transition: all var(--transition-base);
  min-width: fit-content;
}

.timeline-step:hover {
  transform: translateY(-2px);
  box-shadow: var(--card-shadow);
}

.timeline-step.highlight {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  color: white;
}

.timeline-step.highlight .step-department,
.timeline-step.highlight .step-issue {
  color: rgba(255, 255, 255, 0.8);
}

.timeline-step.highlight .step-value {
  color: white;
}

.step-number {
  width: 28px;
  height: 28px;
  background: var(--color-primary-light);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-primary);
  flex-shrink: 0;
}

.timeline-step.highlight .step-number {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.step-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.step-department {
  font-size: var(--font-size-xs);
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.step-value {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--text-primary);
}

.step-issue {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.step-connector {
  margin: 0 var(--spacing-xs);
}

.step-connector svg {
  width: 20px;
  height: 20px;
  color: var(--text-muted);
}

/* Problem Statements */
.problem-statement {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-4xl);
}

.statement-card {
  display: flex;
  gap: var(--spacing-lg);
  padding: var(--spacing-2xl);
  background: var(--card-bg);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  transition: all var(--transition-base);
}

.statement-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--card-shadow-hover);
}

.statement-card.solution {
  border-color: var(--color-primary);
  background: linear-gradient(135deg, rgba(6, 150, 215, 0.05), rgba(6, 150, 215, 0.02));
}

.statement-icon {
  width: 48px;
  height: 48px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.statement-card.solution .statement-icon {
  background: var(--color-primary);
}

.statement-icon svg {
  width: 24px;
  height: 24px;
  color: var(--color-primary);
}

.statement-card.solution .statement-icon svg {
  color: white;
}

.statement-content h3 {
  font-size: var(--font-size-lg);
  font-weight: 600;
  margin-bottom: var(--spacing-sm);
}

.statement-content p {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  line-height: 1.7;
}

/* Quote */
.problem-quote {
  text-align: center;
}

.problem-quote blockquote {
  font-size: var(--font-size-2xl);
  font-weight: 300;
  color: var(--text-primary);
  font-style: italic;
  max-width: 800px;
  margin: 0 auto;
  line-height: 1.6;
}

.problem-quote .highlight {
  color: var(--color-primary);
  font-weight: 500;
}

/* Responsive */
@media (max-width: 1024px) {
  .timeline {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-md);
  }

  .timeline-step {
    justify-content: flex-start;
  }

  .step-connector {
    display: none;
  }

  .problem-statement {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .statement-card {
    flex-direction: column;
    text-align: center;
    align-items: center;
  }

  .problem-quote blockquote {
    font-size: var(--font-size-xl);
  }
}
</style>
