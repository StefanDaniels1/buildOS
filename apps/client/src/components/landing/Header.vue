<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

defineProps<{
  isDark: boolean
  language: 'en' | 'nl'
  translations: {
    home: string
    services: string
    contact: string
    solution: string
  }
}>()

const emit = defineEmits<{
  toggleTheme: []
  toggleLanguage: []
}>()

const router = useRouter()
const isScrolled = ref(false)
const isMobileMenuOpen = ref(false)

function goToSolution() {
  router.push('/solution')
}

const handleScroll = () => {
  isScrolled.value = window.scrollY > 50
}

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <header class="header" :class="{ scrolled: isScrolled }">
    <div class="container">
      <nav class="nav">
        <!-- Logo -->
        <a href="#" class="logo">
          <span class="logo-bim">BIM</span>
          <span class="logo-ai">AI</span>
        </a>

        <!-- Desktop Navigation -->
        <div class="nav-links">
          <a href="#" class="nav-link active">{{ translations.home }}</a>
          <a href="#services" class="nav-link">{{ translations.services }}</a>
          <a href="#contact" class="nav-link">{{ translations.contact }}</a>
          <button @click="goToSolution" class="nav-link solution-link">{{ translations.solution }}</button>
        </div>

        <!-- Actions -->
        <div class="nav-actions">
          <!-- Language Toggle -->
          <button
            class="lang-toggle"
            @click="emit('toggleLanguage')"
            aria-label="Switch language"
          >
            <span :class="{ active: language === 'en' }">EN</span>
            <span class="separator">|</span>
            <span :class="{ active: language === 'nl' }">NL</span>
          </button>

          <!-- Theme Toggle -->
          <button
            class="theme-toggle"
            @click="emit('toggleTheme')"
            :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
          >
            <div class="toggle-track" :class="{ dark: isDark }">
              <div class="toggle-thumb">
                <!-- Sun Icon -->
                <svg 
                  v-if="!isDark" 
                  class="toggle-icon" 
                  viewBox="0 0 24 24" 
                  fill="none" 
                  stroke="currentColor" 
                  stroke-width="2"
                >
                  <circle cx="12" cy="12" r="5"/>
                  <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
                </svg>
                <!-- Moon Icon -->
                <svg 
                  v-else 
                  class="toggle-icon" 
                  viewBox="0 0 24 24" 
                  fill="none" 
                  stroke="currentColor" 
                  stroke-width="2"
                >
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                </svg>
              </div>
            </div>
          </button>

          <!-- Contact Button (Desktop) -->
          <a href="#contact" class="btn btn-primary contact-btn">
            Contact
          </a>

          <!-- Mobile Menu Toggle -->
          <button 
            class="mobile-menu-toggle"
            @click="toggleMobileMenu"
            :aria-expanded="isMobileMenuOpen"
            aria-label="Toggle menu"
          >
            <span class="hamburger" :class="{ open: isMobileMenuOpen }">
              <span></span>
              <span></span>
              <span></span>
            </span>
          </button>
        </div>
      </nav>
    </div>

    <!-- Mobile Menu -->
    <Transition name="slide">
      <div v-if="isMobileMenuOpen" class="mobile-menu">
        <div class="container">
          <a href="#" class="mobile-nav-link" @click="isMobileMenuOpen = false">{{ translations.home }}</a>
          <a href="#services" class="mobile-nav-link" @click="isMobileMenuOpen = false">{{ translations.services }}</a>
          <a href="#contact" class="mobile-nav-link" @click="isMobileMenuOpen = false">{{ translations.contact }}</a>
          <button class="mobile-nav-link solution-mobile-link" @click="goToSolution(); isMobileMenuOpen = false">{{ translations.solution }}</button>
        </div>
      </div>
    </Transition>
  </header>
</template>

<style scoped>
.header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  padding: var(--spacing-lg) 0;
  transition: all var(--transition-base);
}

.header.scrolled {
  background: var(--bg-primary);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: var(--spacing-md) 0;
}

.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* Logo */
.logo {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}

.logo-bim {
  font-size: 1.75rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  color: var(--color-charcoal);
}

[data-theme="dark"] .logo-bim {
  color: var(--text-primary);
}

.logo-ai {
  font-size: 1.75rem;
  font-weight: 300;
  letter-spacing: 0.15em;
  color: var(--color-primary);
}

/* Navigation Links */
.nav-links {
  display: flex;
  align-items: center;
  gap: var(--spacing-xl);
}

.nav-link {
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--text-secondary);
  transition: color var(--transition-fast);
  position: relative;
}

.nav-link::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 0;
  height: 2px;
  background: var(--color-primary);
  transition: width var(--transition-fast);
}

.nav-link:hover,
.nav-link.active {
  color: var(--color-primary);
}

.nav-link:hover::after,
.nav-link.active::after {
  width: 100%;
}

/* Actions */
.nav-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

/* Language Toggle */
.lang-toggle {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  font-weight: 500;
  border: 1px solid var(--border-color);
  transition: all var(--transition-fast);
}

.lang-toggle:hover {
  background: var(--bg-secondary);
}

.lang-toggle span {
  color: var(--text-muted);
  transition: color var(--transition-fast);
}

.lang-toggle span.active {
  color: var(--color-primary);
  font-weight: 600;
}

.lang-toggle .separator {
  color: var(--border-color);
}

/* Theme Toggle */
.theme-toggle {
  padding: var(--spacing-xs);
}

.toggle-track {
  width: 56px;
  height: 30px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-full);
  position: relative;
  transition: background var(--transition-fast);
  border: 1px solid var(--border-color);
}

.toggle-track.dark {
  background: var(--color-primary-dark);
}

.toggle-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 22px;
  height: 22px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform var(--transition-fast);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.toggle-track.dark .toggle-thumb {
  transform: translateX(26px);
}

.toggle-icon {
  width: 14px;
  height: 14px;
  color: var(--color-primary);
}

.toggle-track.dark .toggle-icon {
  color: var(--color-primary-dark);
}

/* Contact Button */
.contact-btn {
  padding: var(--spacing-sm) var(--spacing-lg);
  font-size: var(--font-size-sm);
}

/* Solution Link */
.solution-link {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-primary);
  background: none;
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
}

.solution-link::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 0;
  height: 2px;
  background: var(--color-primary);
  transition: width var(--transition-fast);
}

.solution-link:hover {
  color: var(--color-primary-dark);
}

.solution-link:hover::after {
  width: 100%;
}

.solution-mobile-link {
  width: 100%;
  text-align: left;
  background: none;
  cursor: pointer;
  color: var(--color-primary);
  font-weight: 600;
}

/* Mobile Menu Toggle */
.mobile-menu-toggle {
  display: none;
  padding: var(--spacing-sm);
}

.hamburger {
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: 24px;
}

.hamburger span {
  display: block;
  height: 2px;
  background: var(--text-primary);
  border-radius: 2px;
  transition: all var(--transition-fast);
}

.hamburger.open span:nth-child(1) {
  transform: rotate(45deg) translate(5px, 5px);
}

.hamburger.open span:nth-child(2) {
  opacity: 0;
}

.hamburger.open span:nth-child(3) {
  transform: rotate(-45deg) translate(5px, -5px);
}

/* Mobile Menu */
.mobile-menu {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bg-primary);
  border-top: 1px solid var(--border-color);
  padding: var(--spacing-lg) 0;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.mobile-nav-link {
  display: block;
  padding: var(--spacing-md) 0;
  font-size: var(--font-size-lg);
  font-weight: 500;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-color);
}

.mobile-nav-link:last-child {
  border-bottom: none;
}

/* Transitions */
.slide-enter-active,
.slide-leave-active {
  transition: all var(--transition-base);
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Responsive */
@media (max-width: 768px) {
  .nav-links {
    display: none;
  }

  .contact-btn {
    display: none;
  }

  .mobile-menu-toggle {
    display: block;
  }
}
</style>
