<script setup lang="ts">
import heroVideo from '../../landing-devices.mp4'

defineProps<{
  translations: {
    tagline: string
    titleLine1: string
    titleLine2: string
    titleLine3: string
    description: string
    cta: string
    learnMore: string
    scrollDown: string
  }
}>()
</script>

<template>
  <section class="hero">
    <div class="hero-background">
      <!-- Decorative Elements -->
      <div class="hero-gradient"></div>
      <div class="hero-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
      </div>
    </div>

    <div class="container">
      <div class="hero-content">
        <div class="hero-text">
          <!-- Tagline -->
          <p class="hero-tagline animate-fade-in-up">
            {{ translations.tagline }}
          </p>

          <!-- Main Headline -->
          <h1 class="hero-title animate-fade-in-up delay-1">
            <span class="title-line">{{ translations.titleLine1 }}</span>
            <span class="title-line">{{ translations.titleLine2 }}</span>
            <span class="title-line accent">{{ translations.titleLine3 }}</span>
          </h1>

          <!-- Description -->
          <p class="hero-description animate-fade-in-up delay-2">
            {{ translations.description }}
          </p>

          <!-- CTA Buttons -->
          <div class="hero-actions animate-fade-in-up delay-3">
            <a href="#contact" class="btn btn-primary btn-large">
              {{ translations.cta }}
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </a>
            <a href="#services" class="btn btn-secondary btn-large">
              {{ translations.learnMore }}
            </a>
          </div>
        </div>

        <!-- Hero Visual -->
        <div class="hero-visual animate-fade-in delay-2">
          <div class="visual-container">
            <video
              class="hero-video"
              autoplay
              loop
              muted
              playsinline
              :src="heroVideo"
            />
          </div>
        </div>
      </div>

      <!-- Scroll Indicator -->
      <div class="scroll-indicator animate-fade-in delay-4">
        <span>{{ translations.scrollDown }}</span>
        <div class="scroll-line">
          <div class="scroll-dot"></div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  padding-top: 100px;
  overflow: hidden;
}

/* Background */
.hero-background {
  position: absolute;
  inset: 0;
  z-index: -1;
}

.hero-gradient {
  position: absolute;
  inset: 0;
  background: var(--bg-gradient);
  opacity: 0.5;
}

[data-theme="dark"] .hero-gradient {
  opacity: 1;
}

.hero-shapes {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.shape {
  position: absolute;
  border-radius: var(--radius-2xl);
  opacity: 0.4;
  transform: rotate(-10deg);
}

.shape-1 {
  width: 400px;
  height: 150px;
  background: var(--color-primary-light);
  top: 15%;
  right: 5%;
  animation: float 8s ease-in-out infinite;
}

.shape-2 {
  width: 300px;
  height: 120px;
  background: var(--color-primary-medium);
  top: 35%;
  right: 10%;
  animation: float 8s ease-in-out infinite 0.5s;
}

.shape-3 {
  width: 350px;
  height: 130px;
  background: var(--color-primary);
  top: 55%;
  right: 7%;
  animation: float 8s ease-in-out infinite 1s;
  box-shadow: 0 15px 40px rgba(6, 150, 215, 0.3);
}

@keyframes float {
  0%, 100% {
    transform: rotate(-10deg) translateY(0);
  }
  50% {
    transform: rotate(-10deg) translateY(-20px);
  }
}

/* Content Layout */
.hero-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-4xl);
  align-items: center;
}

/* Text Content */
.hero-text {
  max-width: 600px;
}

.hero-tagline {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-primary);
  text-transform: uppercase;
  letter-spacing: 0.15em;
  margin-bottom: var(--spacing-lg);
}

.hero-title {
  font-size: var(--font-size-7xl);
  font-weight: 300;
  line-height: 1.1;
  margin-bottom: var(--spacing-xl);
}

.title-line {
  display: block;
  letter-spacing: 0.05em;
}

.title-line.accent {
  color: var(--color-primary);
  font-weight: 400;
}

.hero-description {
  font-size: var(--font-size-lg);
  color: var(--text-secondary);
  line-height: 1.8;
  margin-bottom: var(--spacing-2xl);
}

/* Actions */
.hero-actions {
  display: flex;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.btn-large {
  padding: var(--spacing-lg) var(--spacing-2xl);
  font-size: var(--font-size-base);
}

.btn-icon {
  width: 20px;
  height: 20px;
  transition: transform var(--transition-fast);
}

.btn:hover .btn-icon {
  transform: translateX(4px);
}

/* Hero Visual */
.hero-visual {
  display: flex;
  justify-content: center;
  align-items: center;
}

.visual-container {
  width: 100%;
  max-width: 600px;
}

.hero-video {
  width: 100%;
  height: auto;
  border-radius: var(--radius-2xl);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

/* Scroll Indicator */
.scroll-indicator {
  position: absolute;
  bottom: var(--spacing-2xl);
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.scroll-line {
  width: 1px;
  height: 60px;
  background: var(--border-color);
  position: relative;
  overflow: hidden;
}

.scroll-dot {
  width: 3px;
  height: 10px;
  background: var(--color-primary);
  border-radius: var(--radius-full);
  position: absolute;
  left: -1px;
  animation: scrollDown 2s ease-in-out infinite;
}

@keyframes scrollDown {
  0% {
    top: 0;
    opacity: 0;
  }
  30% {
    opacity: 1;
  }
  70% {
    opacity: 1;
  }
  100% {
    top: 100%;
    opacity: 0;
  }
}

/* Responsive */
@media (max-width: 1024px) {
  .hero-content {
    grid-template-columns: 1fr;
    gap: var(--spacing-3xl);
    text-align: center;
  }

  .hero-text {
    max-width: 100%;
  }

  .hero-actions {
    justify-content: center;
  }

  .hero-visual {
    order: -1;
  }

  .visual-container {
    max-width: 500px;
  }

  .shape {
    display: none;
  }
}

@media (max-width: 768px) {
  .hero {
    padding-top: 80px;
  }

  .hero-title {
    font-size: var(--font-size-5xl);
  }

  .hero-description {
    font-size: var(--font-size-base);
  }

  .hero-actions {
    flex-direction: column;
    width: 100%;
  }

  .btn-large {
    width: 100%;
    justify-content: center;
  }

  .scroll-indicator {
    display: none;
  }
}
</style>
