import { computed } from 'vue'

export type Language = 'en' | 'nl'

const translations = {
  // Header
  header: {
    home: { en: 'Home', nl: 'Home' },
    services: { en: 'Services', nl: 'Diensten' },
    contact: { en: 'Contact', nl: 'Contact' },
    solution: { en: 'Solution', nl: 'Oplossing' },
  },

  // Hero
  hero: {
    tagline: { en: 'From BIM data to business intelligence', nl: 'Van BIM-data naar business intelligence' },
    titleLine1: { en: 'Data.', nl: 'Data.' },
    titleLine2: { en: 'Structure.', nl: 'Structuur.' },
    titleLine3: { en: 'Intelligence.', nl: 'Intelligentie.' },
    description: {
      en: 'BIM AI transforms your BIM models from inaccessible data into structured, actionable business intelligence. So your experts can apply their expertise, instead of collecting data.',
      nl: 'BIM AI transformeert je BIM-modellen van ontoegankelijke data naar gestructureerde, actionable business intelligence. Zodat jouw experts hun expertise kunnen toepassen, in plaats van data te verzamelen.'
    },
    cta: { en: 'Schedule a meeting', nl: 'Plan een gesprek' },
    learnMore: { en: 'Discover more', nl: 'Ontdek meer' },
    scrollDown: { en: 'Scroll', nl: 'Scroll' },
  },

  // Value Props
  valueProps: {
    sectionLabel: { en: 'Our Approach', nl: 'Onze Aanpak' },
    sectionTitle: { en: 'The potential of your BIM data', nl: 'Het potentieel van jouw BIM-data' },
    sectionSubtitle: {
      en: 'We transform your BIM models from inaccessible data into structured business intelligence that delivers immediate value.',
      nl: 'We transformeren je BIM-modellen van ontoegankelijke data naar gestructureerde business intelligence die direct waarde oplevert.'
    },
    props: [
      {
        number: '01',
        title: { en: 'We Structure', nl: 'We Structureren' },
        description: {
          en: 'We make connections. Our data architects unlock and structure valuable BIM data from all your models and systems.',
          nl: 'We maken connecties. Onze data-architecten ontsluiten en structureren waardevolle BIM-data uit al je modellen en systemen.'
        },
        icon: 'structure'
      },
      {
        number: '02',
        title: { en: 'We Automate', nl: 'We Automatiseren' },
        description: {
          en: 'Where we put data to work. We build operational pipelines so your experts can work directly with structured data.',
          nl: 'Waar we data aan het werk zetten. We bouwen operationele pipelines zodat je experts direct met gestructureerde data kunnen werken.'
        },
        icon: 'automate'
      },
      {
        number: '03',
        title: { en: 'We Deliver', nl: 'We Leveren' },
        description: {
          en: 'Results for now and for the long term. Our data infrastructure is reliable, transferable, and ready for AI.',
          nl: 'Resultaat voor nu en voor de lange termijn. Onze data-infrastructuur is betrouwbaar, overdraagbaar en klaar voor AI.'
        },
        icon: 'deliver'
      }
    ]
  },

  // About
  about: {
    sectionLabel: { en: 'About BIM AI', nl: 'Over BIM AI' },
    title: { en: 'Data experts with a', nl: 'Data-experts met een' },
    titleHighlight: { en: 'construction mindset', nl: 'bouw mindset' },
    text1: {
      en: "We'd rather not go on endlessly about data. We sit at the table to tackle a business challenge in your organization. Which processes can we automate? What can we take off your hands?",
      nl: 'Eindeloos uitweiden over data doen we liever niet. We zitten aan tafel om een zakelijke uitdaging in je organisatie aan te gaan. Welke processen kunnen we automatiseren? Wat kunnen we uit handen nemen?'
    },
    text2: {
      en: "Only when we have a clear question do we get to work. No report or proof of concept, but an operational data infrastructure that delivers results immediately.",
      nl: 'Pas als we de vraag scherp hebben, gaan we aan de slag. Geen rapport of proof of concept, maar een operationele data-infrastructuur die meteen resultaat oplevert.'
    },
    features: [
      { en: 'BIM data structured and accessible', nl: 'BIM-data gestructureerd en toegankelijk' },
      { en: 'Automated reports and analyses', nl: 'Automatische rapportages en analyses' },
      { en: 'AI-ready data infrastructure', nl: 'AI-ready data-infrastructuur' }
    ],
    cta: { en: 'View our services', nl: 'Bekijk onze diensten' },
    statValue: { en: '60%', nl: '60%' },
    statLabel: { en: 'of expert time goes to data work', nl: 'van expert-tijd gaat naar datawerk' },
  },

  // Problem
  problem: {
    sectionLabel: { en: 'The Problem', nl: 'Het Probleem' },
    title: { en: 'The lifecycle of a parameter', nl: 'De levenscyclus van een parameter' },
    subtitle: { en: 'Spoiler: it goes wrong at step 2', nl: 'Spoiler: het gaat mis bij stap 2' },
    steps: [
      { department: { en: 'BIM coordinator', nl: 'BIM-coördinator' }, value: '450m³', issue: { en: 'models', nl: 'modelleert' } },
      { department: { en: 'Calculation', nl: 'Calculatie' }, value: '475m³', issue: { en: 'adjusts (margin)', nl: 'past aan (marge)' } },
      { department: { en: 'Sustainability', nl: 'Duurzaamheid' }, value: '450m³', issue: { en: 'extracts + CO2', nl: 'haalt eruit + CO2' } },
      { department: { en: 'Procurement', nl: 'Inkoop' }, value: '475m³', issue: { en: 'works with calc.', nl: 'werkt met calc.' } },
      { department: { en: 'Project management', nl: 'Projectleiding' }, value: '460m³', issue: { en: 'planning', nl: 'planning' } },
      { department: { en: 'Execution', nl: 'Uitvoering' }, value: '490m³', issue: { en: 'orders', nl: 'bestelt' } },
    ],
    problemTitle: { en: 'Six departments. Six truths.', nl: 'Zes afdelingen. Zes waarheden.' },
    problemText: {
      en: "The problem isn't the parameter. The problem is that it gets copied six times. Every time a new spreadsheet, a new adjustment, a new \"this is the final version\".",
      nl: 'Het probleem is niet de parameter. Het probleem is dat hij zes keer gekopieerd wordt. Elke keer een nieuwe spreadsheet, een nieuwe aanpassing, een nieuw "dit is de laatste versie".'
    },
    solutionTitle: { en: 'The solution?', nl: 'De oplossing?' },
    solutionText: {
      en: 'One parameter. One place. Where every adjustment is visible, every calculation traceable, and everyone works with the same truth.',
      nl: 'Eén parameter. Eén plek. Waar elke aanpassing zichtbaar is, elke berekening traceerbaar, en iedereen werkt met dezelfde waarheid.'
    },
    quote: {
      en: '"That\'s not a BIM question. That\'s a',
      nl: '"Dat is geen BIM-vraagstuk. Dat is een'
    },
    quoteHighlight: { en: 'data infrastructure', nl: 'data-infrastructuur' },
    quoteEnd: { en: 'question."', nl: 'vraagstuk."' },
  },

  // Services
  services: {
    sectionLabel: { en: 'Services', nl: 'Diensten' },
    sectionTitle: { en: 'How we help you', nl: 'Hoe wij je helpen' },
    sectionSubtitle: {
      en: 'From sustainability analyses to complete data infrastructure. We make your BIM data work.',
      nl: 'Van duurzaamheidsanalyses tot complete data-infrastructuur. We maken je BIM-data werkend.'
    },
    moreInfo: { en: 'More information', nl: 'Meer informatie' },
    items: [
      {
        title: { en: 'Sustainability Analysis', nl: 'Duurzaamheidsanalyse' },
        description: {
          en: 'From 3 days to 10 minutes. Automatic CO2 calculations directly from your BIM models.',
          nl: 'Van 3 dagen naar 10 minuten. Automatische CO2-berekeningen direct uit je BIM-modellen.'
        },
        features: [
          { en: 'CO2 impact calculations', nl: 'CO2-impact berekeningen' },
          { en: 'Material analyses', nl: 'Materiaalanalyses' },
          { en: 'Environmental performance reports', nl: 'Milieuprestatie rapportages' }
        ],
        icon: 'leaf',
        color: 'green'
      },
      {
        title: { en: 'Data Structuring', nl: 'Data Structurering' },
        description: {
          en: 'Make your BIM data accessible to everyone. From unstructured to actionable intelligence.',
          nl: 'Maak je BIM-data toegankelijk voor iedereen. Van ongestructureerd naar actionable intelligence.'
        },
        features: [
          { en: 'Data extraction & transformation', nl: 'Data extractie & transformatie' },
          { en: 'Automated classification', nl: 'Geautomatiseerde classificatie' },
          { en: 'Single source of truth', nl: 'Single source of truth' }
        ],
        icon: 'layers',
        color: 'blue'
      },
      {
        title: { en: 'AI-Ready Infrastructure', nl: 'AI-Ready Infrastructuur' },
        description: {
          en: 'Build the foundation for AI. Structured data ready for machine learning.',
          nl: 'Bouw het fundament voor AI. Gestructureerde data die klaar is voor machine learning.'
        },
        features: [
          { en: 'Microsoft Fabric integration', nl: 'Microsoft Fabric integratie' },
          { en: 'Temporal data modeling', nl: 'Temporele data modeling' },
          { en: 'Predictive analytics ready', nl: 'Predictive analytics ready' }
        ],
        icon: 'cpu',
        color: 'purple'
      },
      {
        title: { en: 'Automation', nl: 'Automatisering' },
        description: {
          en: 'Stop manual data work. Automate quantity extractions and reports.',
          nl: 'Stop met handmatig datawerk. Automatiseer hoeveelheidsextracties en rapportages.'
        },
        features: [
          { en: 'Automated exports', nl: 'Geautomatiseerde exports' },
          { en: 'Real-time dashboards', nl: 'Real-time dashboards' },
          { en: 'Workflow optimization', nl: 'Workflow optimalisatie' }
        ],
        icon: 'zap',
        color: 'orange'
      }
    ]
  },

  // CTA
  cta: {
    researchLabel: { en: 'Research', nl: 'Onderzoek' },
    researchTitle: { en: 'Share your challenges', nl: 'Deel je uitdagingen' },
    researchDescription: {
      en: "We're researching the gap between BIM data and what organizations want to do with it. 30 minutes of brainstorming about where time is lost and what you'd like to automate.",
      nl: 'We doen onderzoek naar de kloof tussen BIM-data en wat organisaties ermee willen doen. 30 minuten sparren over waar tijd verloren gaat en wat je zou willen automatiseren.'
    },
    researchList: [
      { en: 'Digitalization/innovation managers', nl: 'Digitalisering/innovatie managers' },
      { en: 'Data strategists', nl: 'Data strategen' },
      { en: 'BIM/VDC leaders', nl: 'BIM/VDC leaders' },
      { en: 'Experts who spend too much time on data', nl: 'Experts die te veel tijd kwijt zijn aan data' }
    ],
    researchCta: { en: 'Schedule a conversation', nl: 'Plan een gesprek' },
    contactLabel: { en: 'Contact', nl: 'Contact' },
    contactTitle: { en: 'Get in touch', nl: 'Neem contact op' },
    contactDescription: {
      en: "Want to know more about how BIM AI can help you structure your BIM data? Let's meet.",
      nl: 'Meer weten over hoe BIM AI je kan helpen met het structureren van je BIM-data? Laten we kennismaken.'
    },
    contactCta: { en: 'Send a message', nl: 'Stuur een bericht' },
  },

  // Footer
  footer: {
    tagline: { en: 'Data. Structure. Intelligence.', nl: 'Data. Structuur. Intelligentie.' },
    description: {
      en: 'We transform BIM data into structured, actionable business intelligence.',
      nl: 'We transformeren BIM-data naar gestructureerde, actionable business intelligence.'
    },
    navigation: { en: 'Navigation', nl: 'Navigatie' },
    navItems: {
      home: { en: 'Home', nl: 'Home' },
      approach: { en: 'Approach', nl: 'Aanpak' },
      about: { en: 'About us', nl: 'Over ons' },
      services: { en: 'Services', nl: 'Diensten' },
      contact: { en: 'Contact', nl: 'Contact' },
    },
    services: { en: 'Services', nl: 'Diensten' },
    serviceItems: {
      sustainability: { en: 'Sustainability Analysis', nl: 'Duurzaamheidsanalyse' },
      dataStructuring: { en: 'Data Structuring', nl: 'Data Structurering' },
      aiInfrastructure: { en: 'AI-Ready Infrastructure', nl: 'AI-Ready Infrastructuur' },
      automation: { en: 'Automation', nl: 'Automatisering' },
    },
    contact: { en: 'Contact', nl: 'Contact' },
    copyright: { en: 'All rights reserved.', nl: 'Alle rechten voorbehouden.' },
    privacy: { en: 'Privacy', nl: 'Privacy' },
    terms: { en: 'Terms', nl: 'Voorwaarden' },
  }
}

export function useTranslations(language: { value: Language }) {
  const t = computed(() => {
    const lang = language.value

    return {
      header: {
        home: translations.header.home[lang],
        services: translations.header.services[lang],
        contact: translations.header.contact[lang],
        solution: translations.header.solution[lang],
      },
      hero: {
        tagline: translations.hero.tagline[lang],
        titleLine1: translations.hero.titleLine1[lang],
        titleLine2: translations.hero.titleLine2[lang],
        titleLine3: translations.hero.titleLine3[lang],
        description: translations.hero.description[lang],
        cta: translations.hero.cta[lang],
        learnMore: translations.hero.learnMore[lang],
        scrollDown: translations.hero.scrollDown[lang],
      },
      valueProps: {
        sectionLabel: translations.valueProps.sectionLabel[lang],
        sectionTitle: translations.valueProps.sectionTitle[lang],
        sectionSubtitle: translations.valueProps.sectionSubtitle[lang],
        props: translations.valueProps.props.map(p => ({
          number: p.number,
          title: p.title[lang],
          description: p.description[lang],
          icon: p.icon
        }))
      },
      about: {
        sectionLabel: translations.about.sectionLabel[lang],
        title: translations.about.title[lang],
        titleHighlight: translations.about.titleHighlight[lang],
        text1: translations.about.text1[lang],
        text2: translations.about.text2[lang],
        features: translations.about.features.map(f => f[lang]),
        cta: translations.about.cta[lang],
        statValue: translations.about.statValue[lang],
        statLabel: translations.about.statLabel[lang],
      },
      problem: {
        sectionLabel: translations.problem.sectionLabel[lang],
        title: translations.problem.title[lang],
        subtitle: translations.problem.subtitle[lang],
        steps: translations.problem.steps.map(s => ({
          department: s.department[lang],
          value: s.value,
          issue: s.issue[lang]
        })),
        problemTitle: translations.problem.problemTitle[lang],
        problemText: translations.problem.problemText[lang],
        solutionTitle: translations.problem.solutionTitle[lang],
        solutionText: translations.problem.solutionText[lang],
        quote: translations.problem.quote[lang],
        quoteHighlight: translations.problem.quoteHighlight[lang],
        quoteEnd: translations.problem.quoteEnd[lang],
      },
      services: {
        sectionLabel: translations.services.sectionLabel[lang],
        sectionTitle: translations.services.sectionTitle[lang],
        sectionSubtitle: translations.services.sectionSubtitle[lang],
        moreInfo: translations.services.moreInfo[lang],
        items: translations.services.items.map(s => ({
          title: s.title[lang],
          description: s.description[lang],
          features: s.features.map(f => f[lang]),
          icon: s.icon,
          color: s.color
        }))
      },
      cta: {
        researchLabel: translations.cta.researchLabel[lang],
        researchTitle: translations.cta.researchTitle[lang],
        researchDescription: translations.cta.researchDescription[lang],
        researchList: translations.cta.researchList.map(r => r[lang]),
        researchCta: translations.cta.researchCta[lang],
        contactLabel: translations.cta.contactLabel[lang],
        contactTitle: translations.cta.contactTitle[lang],
        contactDescription: translations.cta.contactDescription[lang],
        contactCta: translations.cta.contactCta[lang],
      },
      footer: {
        tagline: translations.footer.tagline[lang],
        description: translations.footer.description[lang],
        navigation: translations.footer.navigation[lang],
        navItems: {
          home: translations.footer.navItems.home[lang],
          approach: translations.footer.navItems.approach[lang],
          about: translations.footer.navItems.about[lang],
          services: translations.footer.navItems.services[lang],
          contact: translations.footer.navItems.contact[lang],
        },
        services: translations.footer.services[lang],
        serviceItems: {
          sustainability: translations.footer.serviceItems.sustainability[lang],
          dataStructuring: translations.footer.serviceItems.dataStructuring[lang],
          aiInfrastructure: translations.footer.serviceItems.aiInfrastructure[lang],
          automation: translations.footer.serviceItems.automation[lang],
        },
        contact: translations.footer.contact[lang],
        copyright: translations.footer.copyright[lang],
        privacy: translations.footer.privacy[lang],
        terms: translations.footer.terms[lang],
      }
    }
  })

  return { t }
}
