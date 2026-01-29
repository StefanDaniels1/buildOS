<script setup lang="ts">
defineProps<{
  translations: {
    tagline: string
    description: string
    navigation: string
    navItems: {
      home: string
      approach: string
      about: string
      services: string
      contact: string
    }
    services: string
    serviceItems: {
      sustainability: string
      dataStructuring: string
      aiInfrastructure: string
      automation: string
    }
    contact: string
    copyright: string
    privacy: string
    terms: string
  }
}>()

const currentYear = new Date().getFullYear()
</script>

<template>
  <footer class="footer">
    <div class="container">
      <div class="footer-content">
        <!-- Logo & Description -->
        <div class="footer-brand">
          <a href="#" class="footer-logo">
            <span class="logo-bim">BIM</span>
            <span class="logo-ai">AI</span>
          </a>
          <p class="footer-tagline">{{ translations.tagline }}</p>
          <p class="footer-description">
            {{ translations.description }}
          </p>
          
          <!-- Social Links -->
          <div class="social-links">
            <a href="https://linkedin.com" target="_blank" rel="noopener" aria-label="LinkedIn">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/>
                <rect x="2" y="9" width="4" height="12"/>
                <circle cx="4" cy="4" r="2"/>
              </svg>
            </a>
          </div>
        </div>

        <!-- Navigation -->
        <div class="footer-nav">
          <h4 class="footer-nav-title">{{ translations.navigation }}</h4>
          <ul class="footer-nav-list">
            <li><a href="#">{{ translations.navItems.home }}</a></li>
            <li><a href="#approach">{{ translations.navItems.approach }}</a></li>
            <li><a href="#about">{{ translations.navItems.about }}</a></li>
            <li><a href="#services">{{ translations.navItems.services }}</a></li>
            <li><a href="#contact">{{ translations.navItems.contact }}</a></li>
          </ul>
        </div>

        <!-- Services -->
        <div class="footer-nav">
          <h4 class="footer-nav-title">{{ translations.services }}</h4>
          <ul class="footer-nav-list">
            <li><a href="#services">{{ translations.serviceItems.sustainability }}</a></li>
            <li><a href="#services">{{ translations.serviceItems.dataStructuring }}</a></li>
            <li><a href="#services">{{ translations.serviceItems.aiInfrastructure }}</a></li>
            <li><a href="#services">{{ translations.serviceItems.automation }}</a></li>
          </ul>
        </div>

        <!-- Contact -->
        <div class="footer-contact">
          <h4 class="footer-nav-title">{{ translations.contact }}</h4>
          <div class="contact-details">
            <a href="mailto:stefan@bimai.nl" class="contact-link">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
              stefan@bimai.nl
            </a>
            <div class="address">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                <circle cx="12" cy="10" r="3"/>
              </svg>
              <span>
                Nederland
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer Bottom -->
      <div class="footer-bottom">
        <p class="copyright">
          &copy; {{ currentYear }} BIM AI. {{ translations.copyright }}
        </p>
        <div class="footer-legal">
          <a href="#">{{ translations.privacy }}</a>
          <a href="#">{{ translations.terms }}</a>
        </div>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  background: var(--bg-secondary);
  padding: var(--spacing-4xl) 0 var(--spacing-xl);
  border-top: 1px solid var(--border-color);
}

/* Footer Content */
.footer-content {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1.5fr;
  gap: var(--spacing-3xl);
  padding-bottom: var(--spacing-3xl);
  border-bottom: 1px solid var(--border-color);
}

/* Brand Section */
.footer-brand {
  max-width: 300px;
}

.footer-logo {
  display: inline-flex;
  align-items: baseline;
  gap: 0.25rem;
  margin-bottom: var(--spacing-sm);
}

.logo-bim {
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  color: var(--color-charcoal);
}

[data-theme="dark"] .logo-bim {
  color: var(--text-primary);
}

.logo-ai {
  font-size: 1.5rem;
  font-weight: 300;
  letter-spacing: 0.15em;
  color: var(--color-primary);
}

.footer-tagline {
  font-size: var(--font-size-sm);
  font-weight: 300;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  margin-bottom: var(--spacing-md);
}

.footer-description {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: var(--spacing-lg);
}

/* Social Links */
.social-links {
  display: flex;
  gap: var(--spacing-md);
}

.social-links a {
  width: 40px;
  height: 40px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}

.social-links a:hover {
  background: var(--color-primary);
  color: white;
  transform: translateY(-2px);
}

.social-links svg {
  width: 20px;
  height: 20px;
}

/* Navigation */
.footer-nav-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: var(--spacing-lg);
}

.footer-nav-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.footer-nav-list a {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  transition: color var(--transition-fast);
}

.footer-nav-list a:hover {
  color: var(--color-primary);
}

/* Contact */
.contact-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.contact-link,
.address {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  transition: color var(--transition-fast);
}

.contact-link:hover {
  color: var(--color-primary);
}

.contact-link svg,
.address svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  margin-top: 2px;
}

/* Footer Bottom */
.footer-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--spacing-xl);
}

.copyright {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.footer-legal {
  display: flex;
  gap: var(--spacing-xl);
}

.footer-legal a {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  transition: color var(--transition-fast);
}

.footer-legal a:hover {
  color: var(--color-primary);
}

/* Responsive */
@media (max-width: 1024px) {
  .footer-content {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-2xl);
  }

  .footer-brand {
    max-width: 100%;
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .footer-content {
    grid-template-columns: 1fr;
    text-align: center;
  }

  .footer-brand {
    grid-column: span 1;
    margin: 0 auto;
  }

  .social-links {
    justify-content: center;
  }

  .footer-nav-list {
    align-items: center;
  }

  .contact-details {
    align-items: center;
  }

  .footer-bottom {
    flex-direction: column;
    gap: var(--spacing-md);
    text-align: center;
  }
}
</style>
