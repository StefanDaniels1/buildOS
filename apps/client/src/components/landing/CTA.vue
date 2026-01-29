<script setup lang="ts">
defineProps<{
  translations: {
    researchLabel: string
    researchTitle: string
    researchDescription: string
    researchList: string[]
    researchCta: string
    contactLabel: string
    contactTitle: string
    contactDescription: string
    contactCta: string
  }
}>()
</script>

<template>
  <section class="cta section" id="contact">
    <div class="container">
      <div class="cta-grid">
        <!-- Research CTA -->
        <div class="cta-card research">
          <div class="cta-content">
            <span class="cta-label">{{ translations.researchLabel }}</span>
            <h3 class="cta-title">{{ translations.researchTitle }}</h3>
            <p class="cta-description">
              {{ translations.researchDescription }}
            </p>
            <ul class="cta-list">
              <li v-for="item in translations.researchList" :key="item">{{ item }}</li>
            </ul>
            <a href="mailto:stefan@bimai.nl" class="btn btn-secondary">
              {{ translations.researchCta }}
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </a>
          </div>
          <div class="cta-decoration">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </div>
        </div>

        <!-- Contact CTA -->
        <div class="cta-card contact">
          <div class="cta-background">
            <div class="bg-shape bg-shape-1"></div>
            <div class="bg-shape bg-shape-2"></div>
            <div class="bg-shape bg-shape-3"></div>
          </div>
          <div class="cta-content">
            <span class="cta-label">{{ translations.contactLabel }}</span>
            <h3 class="cta-title">{{ translations.contactTitle }}</h3>
            <p class="cta-description">
              {{ translations.contactDescription }}
            </p>
            <div class="contact-info">
              <div class="contact-item">
                <div class="contact-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                    <polyline points="22,6 12,13 2,6"/>
                  </svg>
                </div>
                <a href="mailto:stefan@bimai.nl">stefan@bimai.nl</a>
              </div>
              <div class="contact-item">
                <div class="contact-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/>
                    <rect x="2" y="9" width="4" height="12"/>
                    <circle cx="4" cy="4" r="2"/>
                  </svg>
                </div>
                <a href="https://www.linkedin.com/company/bim-ai/" target="_blank" rel="noopener">LinkedIn</a>
              </div>
            </div>
            <a href="mailto:stefan@bimai.nl" class="btn btn-primary">
              {{ translations.contactCta }}
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </a>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.cta {
  background: var(--bg-secondary);
  position: relative;
}

.cta::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border-color), transparent);
}

/* CTA Grid */
.cta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-xl);
}

/* CTA Card */
.cta-card {
  background: var(--card-bg);
  border-radius: var(--radius-2xl);
  padding: var(--spacing-3xl);
  position: relative;
  overflow: hidden;
  border: 1px solid var(--border-color);
}

/* Research Card */
.cta-card.research {
  display: flex;
  justify-content: space-between;
}

.cta-card.research .cta-decoration {
  position: absolute;
  right: var(--spacing-2xl);
  top: 50%;
  transform: translateY(-50%);
  width: 120px;
  height: 120px;
  opacity: 0.1;
}

.cta-card.research .cta-decoration svg {
  width: 100%;
  height: 100%;
  color: var(--color-primary);
}

/* Contact Card */
.cta-card.contact {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  color: white;
  border: none;
}

.cta-card.contact .cta-label {
  color: rgba(255, 255, 255, 0.7);
}

.cta-card.contact .cta-description {
  color: rgba(255, 255, 255, 0.9);
}

.cta-card.contact .btn-primary {
  background: white;
  color: var(--color-primary);
}

.cta-card.contact .btn-primary:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-2px);
}

/* Contact Background Shapes */
.cta-background {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.bg-shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

.bg-shape-1 {
  width: 300px;
  height: 300px;
  top: -150px;
  right: -100px;
}

.bg-shape-2 {
  width: 200px;
  height: 200px;
  bottom: -100px;
  left: -50px;
}

.bg-shape-3 {
  width: 100px;
  height: 100px;
  top: 50%;
  right: 20%;
}

/* CTA Content */
.cta-content {
  position: relative;
  z-index: 1;
  max-width: 400px;
}

.cta-label {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-primary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: var(--spacing-md);
  display: block;
}

.cta-title {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  margin-bottom: var(--spacing-md);
}

.cta-description {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: var(--spacing-lg);
}

/* CTA List */
.cta-list {
  margin-bottom: var(--spacing-xl);
}

.cta-list li {
  position: relative;
  padding-left: var(--spacing-lg);
  margin-bottom: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.cta-list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  width: 6px;
  height: 6px;
  background: var(--color-primary);
  border-radius: 50%;
}

/* Contact Info */
.contact-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.contact-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.contact-icon {
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.contact-icon svg {
  width: 20px;
  height: 20px;
  color: white;
}

.contact-item a {
  color: white;
  font-weight: 500;
  transition: opacity var(--transition-fast);
}

.contact-item a:hover {
  opacity: 0.8;
}

/* Button */
.btn-icon {
  width: 18px;
  height: 18px;
  transition: transform var(--transition-fast);
}

.btn:hover .btn-icon {
  transform: translateX(4px);
}

/* Responsive */
@media (max-width: 1024px) {
  .cta-grid {
    grid-template-columns: 1fr;
  }

  .cta-card {
    padding: var(--spacing-2xl);
  }

  .cta-content {
    max-width: 100%;
  }
}

@media (max-width: 768px) {
  .cta-card.research .cta-decoration {
    display: none;
  }
}
</style>
