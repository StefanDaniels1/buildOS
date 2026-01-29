<script setup lang="ts">
interface ValueProp {
  number: string
  title: string
  description: string
  icon: string
}

defineProps<{
  translations: {
    sectionLabel: string
    sectionTitle: string
    sectionSubtitle: string
    props: ValueProp[]
  }
}>()
</script>

<template>
  <section class="value-props section" id="approach">
    <div class="container">
      <!-- Section Header -->
      <div class="section-header">
        <span class="section-label">{{ translations.sectionLabel }}</span>
        <h2 class="section-title">{{ translations.sectionTitle }}</h2>
        <p class="section-subtitle">
          {{ translations.sectionSubtitle }}
        </p>
      </div>

      <!-- Value Props Grid -->
      <div class="props-grid">
        <div
          v-for="(prop, index) in translations.props"
          :key="prop.number"
          class="prop-card"
          :class="`delay-${index + 1}`"
        >
          <!-- Card Header -->
          <div class="prop-header">
            <span class="prop-number">{{ prop.number }}</span>
            <div class="prop-icon" :class="prop.icon">
              <!-- Structure Icon -->
              <svg v-if="prop.icon === 'structure'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                <line x1="12" y1="22.08" x2="12" y2="12"/>
              </svg>
              <!-- Automate Icon -->
              <svg v-if="prop.icon === 'automate'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                <circle cx="12" cy="12" r="4"/>
              </svg>
              <!-- Deliver Icon -->
              <svg v-if="prop.icon === 'deliver'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
            </div>
          </div>

          <!-- Card Content -->
          <div class="prop-content">
            <h3 class="prop-title">{{ prop.title }}</h3>
            <p class="prop-description">{{ prop.description }}</p>
          </div>

          <!-- Card Decoration -->
          <div class="prop-decoration"></div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.value-props {
  background: var(--bg-secondary);
  position: relative;
  overflow: hidden;
}

.value-props::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border-color), transparent);
}

/* Props Grid */
.props-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-xl);
}

/* Prop Card */
.prop-card {
  background: var(--card-bg);
  border-radius: var(--radius-2xl);
  padding: var(--spacing-2xl);
  position: relative;
  overflow: hidden;
  transition: all var(--transition-base);
  border: 1px solid var(--border-color);
}

.prop-card:hover {
  transform: translateY(-8px);
  box-shadow: var(--card-shadow-hover);
}

.prop-card:hover .prop-decoration {
  opacity: 1;
  transform: scale(1);
}

/* Card Header */
.prop-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-xl);
}

.prop-number {
  font-size: var(--font-size-4xl);
  font-weight: 700;
  color: var(--color-primary);
  opacity: 0.2;
  line-height: 1;
}

.prop-icon {
  width: 48px;
  height: 48px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-base);
}

.prop-card:hover .prop-icon {
  background: var(--color-primary);
}

.prop-icon svg {
  width: 24px;
  height: 24px;
  color: var(--color-primary);
  transition: color var(--transition-base);
}

.prop-card:hover .prop-icon svg {
  color: white;
}

/* Card Content */
.prop-content {
  position: relative;
  z-index: 1;
}

.prop-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  margin-bottom: var(--spacing-md);
  color: var(--text-primary);
}

.prop-description {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  line-height: 1.7;
}

/* Card Decoration */
.prop-decoration {
  position: absolute;
  bottom: -50px;
  right: -50px;
  width: 200px;
  height: 200px;
  background: var(--color-primary);
  border-radius: 50%;
  opacity: 0;
  transform: scale(0.8);
  transition: all var(--transition-slow);
}

/* Responsive */
@media (max-width: 1024px) {
  .props-grid {
    grid-template-columns: 1fr;
    max-width: 600px;
    margin: 0 auto;
  }
}

@media (max-width: 768px) {
  .prop-card {
    padding: var(--spacing-xl);
  }

  .prop-number {
    font-size: var(--font-size-3xl);
  }
}
</style>
