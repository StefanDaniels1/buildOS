<script setup lang="ts">
import aboutVideo from '../../landing-matrix.mp4'

defineProps<{
  translations: {
    sectionLabel: string
    title: string
    titleHighlight: string
    text1: string
    text2: string
    features: string[]
    cta: string
    statValue: string
    statLabel: string
  }
}>()
</script>

<template>
  <section class="about section" id="about">
    <div class="container">
      <div class="about-grid">
        <!-- Image Side -->
        <div class="about-image">
          <div class="image-wrapper">
            <video
              class="about-video"
              autoplay
              loop
              muted
              playsinline
              :src="aboutVideo"
            />

            <!-- Decorative Elements -->
            <div class="image-decoration decoration-1"></div>
            <div class="image-decoration decoration-2"></div>
          </div>

          <!-- Stats Card -->
          <div class="stats-card">
            <div class="stat">
              <span class="stat-value">{{ translations.statValue }}</span>
              <span class="stat-label">{{ translations.statLabel }}</span>
            </div>
          </div>
        </div>

        <!-- Text Side -->
        <div class="about-content">
          <span class="section-label">{{ translations.sectionLabel }}</span>
          <h2 class="about-title">
            {{ translations.title }}
            <span class="highlight">{{ translations.titleHighlight }}</span>
          </h2>
          <p class="about-text">
            {{ translations.text1 }}
          </p>
          <p class="about-text">
            {{ translations.text2 }}
          </p>

          <!-- Features List -->
          <ul class="features-list">
            <li v-for="feature in translations.features" :key="feature" class="feature-item">
              <div class="feature-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
              <span>{{ feature }}</span>
            </li>
          </ul>

          <a href="#services" class="btn btn-primary">
            {{ translations.cta }}
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </a>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.about {
  background: var(--bg-primary);
  overflow: hidden;
}

/* Grid Layout */
.about-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-4xl);
  align-items: center;
}

/* Image Side */
.about-image {
  position: relative;
}

.image-wrapper {
  position: relative;
  border-radius: var(--radius-2xl);
  overflow: visible;
}

.about-video {
  width: 100%;
  height: auto;
  border-radius: var(--radius-2xl);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

/* Image Decorations */
.image-decoration {
  position: absolute;
  border-radius: var(--radius-2xl);
  z-index: -1;
}

.decoration-1 {
  width: 80%;
  height: 80%;
  background: var(--color-primary-light);
  top: -20px;
  left: -20px;
  opacity: 0.5;
}

.decoration-2 {
  width: 60%;
  height: 60%;
  background: var(--color-primary-medium);
  bottom: -30px;
  right: -30px;
  opacity: 0.3;
}

/* Stats Card */
.stats-card {
  position: absolute;
  bottom: var(--spacing-2xl);
  right: calc(-1 * var(--spacing-xl));
  background: var(--card-bg);
  border-radius: var(--radius-xl);
  padding: var(--spacing-xl);
  box-shadow: var(--card-shadow-hover);
  border: 1px solid var(--border-color);
  z-index: 10;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.stat-value {
  font-size: var(--font-size-4xl);
  font-weight: 700;
  color: var(--color-primary);
  line-height: 1;
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  max-width: 150px;
}

/* Content Side */
.about-content {
  max-width: 560px;
}

.about-title {
  font-size: var(--font-size-4xl);
  font-weight: 600;
  line-height: 1.2;
  margin-bottom: var(--spacing-xl);
  margin-top: var(--spacing-md);
}

.highlight {
  color: var(--color-primary);
}

.about-text {
  font-size: var(--font-size-lg);
  color: var(--text-secondary);
  line-height: 1.8;
  margin-bottom: var(--spacing-lg);
}

/* Features List */
.features-list {
  margin: var(--spacing-2xl) 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.feature-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.feature-icon {
  width: 28px;
  height: 28px;
  background: var(--color-primary-light);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

[data-theme="dark"] .feature-icon {
  background: rgba(6, 150, 215, 0.2);
}

.feature-icon svg {
  width: 16px;
  height: 16px;
  color: var(--color-primary);
}

.feature-item span {
  font-size: var(--font-size-base);
  color: var(--text-primary);
  font-weight: 500;
}

/* Button */
.btn-icon {
  width: 20px;
  height: 20px;
  transition: transform var(--transition-fast);
}

.btn:hover .btn-icon {
  transform: translateX(4px);
}

/* Responsive */
@media (max-width: 1024px) {
  .about-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-3xl);
  }

  .about-image {
    max-width: 500px;
    margin: 0 auto;
  }

  .stats-card {
    right: var(--spacing-md);
    bottom: var(--spacing-md);
  }

  .about-content {
    max-width: 100%;
    text-align: center;
  }

  .features-list {
    align-items: center;
  }
}

@media (max-width: 768px) {
  .about-title {
    font-size: var(--font-size-3xl);
  }

  .about-text {
    font-size: var(--font-size-base);
  }

  .stats-card {
    position: relative;
    right: auto;
    bottom: auto;
    margin-top: var(--spacing-xl);
    text-align: center;
  }

  .stat-label {
    max-width: 100%;
  }
}
</style>
