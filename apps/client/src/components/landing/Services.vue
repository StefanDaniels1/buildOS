<script setup lang="ts">
interface Service {
  title: string
  description: string
  features: string[]
  icon: string
  color: string
}

defineProps<{
  translations: {
    sectionLabel: string
    sectionTitle: string
    sectionSubtitle: string
    moreInfo: string
    items: Service[]
  }
}>()
</script>

<template>
  <section class="services section" id="services">
    <div class="container">
      <!-- Section Header -->
      <div class="section-header">
        <span class="section-label">{{ translations.sectionLabel }}</span>
        <h2 class="section-title">{{ translations.sectionTitle }}</h2>
        <p class="section-subtitle">
          {{ translations.sectionSubtitle }}
        </p>
      </div>

      <!-- Services Grid -->
      <div class="services-grid">
        <article
          v-for="service in translations.items"
          :key="service.title"
          class="service-card"
          :class="service.color"
        >
          <!-- Card Header -->
          <div class="service-header">
            <div class="service-icon">
              <!-- Leaf Icon -->
              <svg v-if="service.icon === 'leaf'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
                <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
              </svg>
              <!-- Layers Icon -->
              <svg v-if="service.icon === 'layers'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <polygon points="12 2 2 7 12 12 22 7 12 2"/>
                <polyline points="2 17 12 22 22 17"/>
                <polyline points="2 12 12 17 22 12"/>
              </svg>
              <!-- CPU Icon -->
              <svg v-if="service.icon === 'cpu'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="4" y="4" width="16" height="16" rx="2" ry="2"/>
                <rect x="9" y="9" width="6" height="6"/>
                <line x1="9" y1="1" x2="9" y2="4"/>
                <line x1="15" y1="1" x2="15" y2="4"/>
                <line x1="9" y1="20" x2="9" y2="23"/>
                <line x1="15" y1="20" x2="15" y2="23"/>
                <line x1="20" y1="9" x2="23" y2="9"/>
                <line x1="20" y1="14" x2="23" y2="14"/>
                <line x1="1" y1="9" x2="4" y2="9"/>
                <line x1="1" y1="14" x2="4" y2="14"/>
              </svg>
              <!-- Zap Icon -->
              <svg v-if="service.icon === 'zap'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
            </div>
            <h3 class="service-title">{{ service.title }}</h3>
          </div>

          <!-- Card Content -->
          <p class="service-description">{{ service.description }}</p>

          <!-- Features -->
          <ul class="service-features">
            <li v-for="feature in service.features" :key="feature">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              {{ feature }}
            </li>
          </ul>

          <!-- Card Link -->
          <a href="#contact" class="service-link">
            {{ translations.moreInfo }}
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </a>

          <!-- Card Decoration -->
          <div class="service-decoration"></div>
        </article>
      </div>
    </div>
  </section>
</template>

<style scoped>
.services {
  background: var(--bg-primary);
  position: relative;
}

/* Services Grid */
.services-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-xl);
}

/* Service Card */
.service-card {
  background: var(--card-bg);
  border-radius: var(--radius-2xl);
  padding: var(--spacing-2xl);
  position: relative;
  overflow: hidden;
  transition: all var(--transition-base);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.service-card:hover {
  transform: translateY(-8px);
  box-shadow: var(--card-shadow-hover);
}

.service-card:hover .service-decoration {
  transform: scale(1.5);
  opacity: 0.1;
}

/* Color Variants */
.service-card.green .service-icon { background: rgba(34, 197, 94, 0.1); }
.service-card.green .service-icon svg { color: #22c55e; }
.service-card.green .service-decoration { background: #22c55e; }
.service-card.green .service-link { color: #22c55e; }

.service-card.blue .service-icon { background: rgba(6, 150, 215, 0.1); }
.service-card.blue .service-icon svg { color: var(--color-primary); }
.service-card.blue .service-decoration { background: var(--color-primary); }
.service-card.blue .service-link { color: var(--color-primary); }

.service-card.purple .service-icon { background: rgba(139, 92, 246, 0.1); }
.service-card.purple .service-icon svg { color: #8b5cf6; }
.service-card.purple .service-decoration { background: #8b5cf6; }
.service-card.purple .service-link { color: #8b5cf6; }

.service-card.orange .service-icon { background: rgba(249, 115, 22, 0.1); }
.service-card.orange .service-icon svg { color: #f97316; }
.service-card.orange .service-decoration { background: #f97316; }
.service-card.orange .service-link { color: #f97316; }

/* Card Header */
.service-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.service-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.service-icon svg {
  width: 28px;
  height: 28px;
}

.service-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--text-primary);
}

/* Card Content */
.service-description {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: var(--spacing-lg);
}

/* Features */
.service-features {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xl);
  flex-grow: 1;
}

.service-features li {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--text-primary);
}

.service-features svg {
  width: 16px;
  height: 16px;
  color: var(--color-primary);
  flex-shrink: 0;
}

/* Card Link */
.service-link {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
  font-weight: 600;
  transition: gap var(--transition-fast);
}

.service-link svg {
  width: 16px;
  height: 16px;
  transition: transform var(--transition-fast);
}

.service-link:hover {
  gap: var(--spacing-md);
}

.service-link:hover svg {
  transform: translateX(4px);
}

/* Card Decoration */
.service-decoration {
  position: absolute;
  bottom: -100px;
  right: -100px;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  opacity: 0.05;
  transition: all var(--transition-slow);
  pointer-events: none;
}

/* Responsive */
@media (max-width: 1024px) {
  .services-grid {
    grid-template-columns: 1fr;
    max-width: 600px;
    margin: 0 auto;
  }
}

@media (max-width: 768px) {
  .service-card {
    padding: var(--spacing-xl);
  }
}
</style>
