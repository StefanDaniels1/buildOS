<script setup lang="ts">
import { ref, onMounted } from 'vue'
import LandingHeader from '../components/landing/Header.vue'
import Hero from '../components/landing/Hero.vue'
import ValueProps from '../components/landing/ValueProps.vue'
import About from '../components/landing/About.vue'
import Services from '../components/landing/Services.vue'
import Problem from '../components/landing/Problem.vue'
import CTA from '../components/landing/CTA.vue'
import Footer from '../components/landing/Footer.vue'
import { useTranslations, type Language } from '../composables/useTranslations'

const isDark = ref(false)

// Language state
const language = ref<Language>((localStorage.getItem('language') as Language) || 'en')
const { t } = useTranslations(language)

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  document.documentElement.classList.remove('light', 'dark')
  document.documentElement.classList.add(isDark.value ? 'dark' : 'light')
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

const toggleLanguage = () => {
  language.value = language.value === 'en' ? 'nl' : 'en'
  localStorage.setItem('language', language.value)
}

onMounted(() => {
  // Check for saved theme preference (light mode is default)
  const savedTheme = localStorage.getItem('theme')

  if (savedTheme === 'dark') {
    isDark.value = true
    document.documentElement.setAttribute('data-theme', 'dark')
  } else {
    isDark.value = false
    document.documentElement.setAttribute('data-theme', 'light')
  }
})
</script>

<template>
  <div class="landing-app">
    <LandingHeader :is-dark="isDark" :language="language" :translations="t.header" @toggle-theme="toggleTheme" @toggle-language="toggleLanguage" />
    <main>
      <Hero :translations="t.hero" />
      <ValueProps :translations="t.valueProps" />
      <About :translations="t.about" />
      <Problem :translations="t.problem" />
      <Services :translations="t.services" />
      <CTA :translations="t.cta" />
    </main>
    <Footer :translations="t.footer" />
  </div>
</template>

<style scoped>
.landing-app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

main {
  flex: 1;
}
</style>
