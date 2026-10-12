/**
 * SCENERYX — APPLE LIGHT THEME & CONTINUOUS SCROLLYTELLING ENGINE
 * Powers global scroll tracking, Hero pinned scrollytelling, section-by-section
 * interactive story steps, tab switches, and accessible accordions.
 */

document.addEventListener('DOMContentLoaded', () => {
  initGlobalScrollProgress();
  initHeader();
  initHeroScrollytelling();
  initContinuousSectionScrolly();
  initMobileNav();
  initSettingsSwitcher();
  initHubSwitcher();
  initTelemetrySwitcher();
  initFaqAccordions();
});

/* --------------------------------------------------------------------------
   1. GLOBAL SCROLL PROGRESS BAR (Apple Style)
   -------------------------------------------------------------------------- */
function initGlobalScrollProgress() {
  const globalFill = document.querySelector('.global-scroll-fill');
  if (!globalFill) return;

  window.addEventListener('scroll', () => {
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    if (docHeight > 0) {
      const progress = window.scrollY / docHeight;
      globalFill.style.transform = `scaleX(${progress})`;
    }
  }, { passive: true });
}

/* --------------------------------------------------------------------------
   2. HEADER SCROLL STATE
   -------------------------------------------------------------------------- */
function initHeader() {
  const header = document.querySelector('.site-header');
  if (!header) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 30) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  }, { passive: true });
}

/* --------------------------------------------------------------------------
   3. HERO SCROLLYTELLING ANIMATION (PINNED MASTHEAD)
   -------------------------------------------------------------------------- */
function initHeroScrollytelling() {
  const scrollySection = document.querySelector('.scrolly');
  const scrollyPin = document.querySelector('.scrolly-pin');
  const progressBar = document.querySelector('.scrolly-progress-bar');
  const stepIndicator = document.querySelector('.scrolly-step');
  
  const panel1 = document.querySelector('.panel-1');
  const panel2 = document.querySelector('.panel-2');
  const panel3 = document.querySelector('.panel-3');

  if (!scrollySection || !scrollyPin || !panel1 || !panel2 || !panel3) return;
  if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

  gsap.registerPlugin(ScrollTrigger);

  const bg1 = panel1.querySelector('.panel-bg');
  const scrim1 = panel1.querySelector('.panel-scrim');
  const content1 = panel1.querySelector('.panel-content');

  const bg2 = panel2.querySelector('.panel-bg');
  const scrim2 = panel2.querySelector('.panel-scrim');
  const content2 = panel2.querySelector('.panel-content');

  const bg3 = panel3.querySelector('.panel-bg');
  const scrim3 = panel3.querySelector('.panel-scrim');
  const content3 = panel3.querySelector('.panel-content');

  // Initial pointer events
  gsap.set(panel1, { pointerEvents: 'auto' });
  gsap.set(panel2, { pointerEvents: 'none' });
  gsap.set(panel3, { pointerEvents: 'none' });

  // Initial transform and opacity states
  gsap.set(bg1, { scale: 1, opacity: 1, transformOrigin: 'center center' });
  gsap.set(scrim1, { opacity: 1 });
  gsap.set(content1, { y: 0, opacity: 1 });

  gsap.set(bg2, { scale: 1.06, opacity: 0, transformOrigin: 'center center' });
  gsap.set(scrim2, { opacity: 0 });
  gsap.set(content2, { y: 50, opacity: 0 });

  gsap.set(bg3, { scale: 1.06, opacity: 0, transformOrigin: 'center center' });
  gsap.set(scrim3, { opacity: 0 });
  gsap.set(content3, { y: 50, opacity: 0 });

  const tl = gsap.timeline({
    scrollTrigger: {
      trigger: scrollySection,
      start: 'top top',
      end: '+=2400',
      pin: scrollyPin,
      pinSpacing: true,
      scrub: 1,
      invalidateOnRefresh: true,
      onUpdate: (self) => {
        const p = self.progress;

        if (progressBar) {
          progressBar.style.transform = `scaleX(${p})`;
        }

        if (stepIndicator) {
          if (p < 0.35) {
            stepIndicator.textContent = '01 / 03';
            panel1.style.pointerEvents = 'auto';
            panel2.style.pointerEvents = 'none';
            panel3.style.pointerEvents = 'none';
          } else if (p < 0.72) {
            stepIndicator.textContent = '02 / 03';
            panel1.style.pointerEvents = 'none';
            panel2.style.pointerEvents = 'auto';
            panel3.style.pointerEvents = 'none';
          } else {
            stepIndicator.textContent = '03 / 03';
            panel1.style.pointerEvents = 'none';
            panel2.style.pointerEvents = 'none';
            panel3.style.pointerEvents = 'auto';
          }
        }
      }
    }
  });

  // Master scrub sequence:
  // Phase 1: Panel 1 to Panel 2 (Background zooms slightly & cross-fades, Text content elevates & cross-fades)
  tl.to(bg1, { scale: 1.08, opacity: 0, duration: 1.2, ease: 'power2.inOut' }, 0.8)
    .to(content1, { y: -50, opacity: 0, duration: 1.0, ease: 'power2.inOut' }, 0.8)
    .to(bg2, { scale: 1.0, opacity: 1, duration: 1.2, ease: 'power2.inOut' }, 1.0)
    .to(scrim2, { opacity: 1, duration: 1.0, ease: 'power2.inOut' }, 1.0)
    .to(content2, { y: 0, opacity: 1, duration: 1.2, ease: 'power2.out' }, 1.0)

  // Hold Panel 2 in view
    .to({}, { duration: 1.0 })

  // Phase 2: Panel 2 to Panel 3 (Background zooms slightly & cross-fades, Text content elevates & cross-fades)
    .to(bg2, { scale: 1.08, opacity: 0, duration: 1.2, ease: 'power2.inOut' }, 3.2)
    .to(scrim2, { opacity: 0, duration: 1.0, ease: 'power2.inOut' }, 3.2)
    .to(content2, { y: -50, opacity: 0, duration: 1.0, ease: 'power2.inOut' }, 3.2)
    .to(bg3, { scale: 1.0, opacity: 1, duration: 1.2, ease: 'power2.inOut' }, 3.4)
    .to(scrim3, { opacity: 1, duration: 1.0, ease: 'power2.inOut' }, 3.4)
    .to(content3, { y: 0, opacity: 1, duration: 1.2, ease: 'power2.out' }, 3.4)

  // Hold Panel 3 before releasing naturally
    .to({}, { duration: 0.8 });
}

/* --------------------------------------------------------------------------
   4. CONTINUOUS SCROLLYTELLING SECTIONS (Apple-Style Pinned Stages)
   -------------------------------------------------------------------------- */
function initContinuousSectionScrolly() {
  if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

  gsap.registerPlugin(ScrollTrigger);

  // A. Unified Settings Stage (Transforms between 2D & VR dynamically)
  const settingsStages = document.querySelectorAll('#settings-unified .story-step');
  const tab2D = document.querySelector('.showcase-tab[data-mode="2d"]');
  const tabVR = document.querySelector('.showcase-tab[data-mode="vr"]');

  settingsStages.forEach((step, index) => {
    ScrollTrigger.create({
      trigger: step,
      start: 'top 65%',
      end: 'bottom 65%',
      onEnter: () => activateSettingsStep(index + 1),
      onEnterBack: () => activateSettingsStep(index + 1),
    });
  });

  function activateSettingsStep(stepNum) {
    settingsStages.forEach((s, idx) => {
      s.classList.toggle('active', idx === stepNum - 1);
    });

    if (stepNum === 2 && tabVR) {
      // Automatically switch UI to VR Headset mode on scroll
      tabVR.click();
    } else if (stepNum === 1 && tab2D) {
      // Automatically switch UI to 2D Desktop mode on scroll
      tab2D.click();
    }
  }

  // B. Scenery Hub Stages
  const hubStages = document.querySelectorAll('#scenery-hub .story-step');
  hubStages.forEach((step, index) => {
    ScrollTrigger.create({
      trigger: step,
      start: 'top 65%',
      end: 'bottom 65%',
      onEnter: () => activateHubStep(index),
      onEnterBack: () => activateHubStep(index),
    });
  });

  function activateHubStep(idx) {
    hubStages.forEach((s, i) => {
      s.classList.toggle('active', i === idx);
    });
  }

  // C. Flight Optimizer Stages
  const optStages = document.querySelectorAll('#optimizer .story-step');
  optStages.forEach((step, index) => {
    ScrollTrigger.create({
      trigger: step,
      start: 'top 65%',
      end: 'bottom 65%',
      onEnter: () => activateOptStep(index),
      onEnterBack: () => activateOptStep(index),
    });
  });

  function activateOptStep(idx) {
    optStages.forEach((s, i) => {
      s.classList.toggle('active', i === idx);
    });
  }

  // D. In-Game Panel Stages
  const panelStages = document.querySelectorAll('#ingame-panel .story-step');
  panelStages.forEach((step, index) => {
    ScrollTrigger.create({
      trigger: step,
      start: 'top 65%',
      end: 'bottom 65%',
      onEnter: () => activatePanelStep(index),
      onEnterBack: () => activatePanelStep(index),
    });
  });

  function activatePanelStep(idx) {
    panelStages.forEach((s, i) => {
      s.classList.toggle('active', i === idx);
    });
  }
}

/* --------------------------------------------------------------------------
   5. MOBILE NAVIGATION DRAWER
   -------------------------------------------------------------------------- */
function initMobileNav() {
  const menuBtn = document.querySelector('.menu-button');
  const mobileNav = document.querySelector('.mobile-nav');

  if (!menuBtn || !mobileNav) return;

  menuBtn.addEventListener('click', () => {
    const isOpen = mobileNav.classList.toggle('open');
    menuBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });

  mobileNav.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      mobileNav.classList.remove('open');
      menuBtn.setAttribute('aria-expanded', 'false');
    });
  });
}

/* --------------------------------------------------------------------------
   6. INTERACTIVE UNIFIED SETTINGS SWITCHER (2D VS VR & CONFIG PATHS)
   -------------------------------------------------------------------------- */
function initSettingsSwitcher() {
  const tabs = document.querySelectorAll('#settings-unified .showcase-tab');
  const stageImg = document.getElementById('settings-stage-img');
  const metricTarget = document.getElementById('metric-target');
  const metricTlod = document.getElementById('metric-tlod');
  const metricRender = document.getElementById('metric-render');
  const metricLatency = document.getElementById('metric-latency');

  if (!tabs.length) return;

  const views = {
    'graphics': {
      src: 'assets/visuel-win-graphics.webp',
      alt: 'SceneryX MSFS Graphic Settings Interface',
      target: '30 / 90 Hz Cadence',
      tlod: '70 Floor → 155 Cruise',
      render: '100% Native (Sweet Spot)',
      latency: '55% (Balanced)'
    },
    'settings': {
      src: 'assets/visuel-win-settings.webp',
      alt: 'SceneryX Settings & Configuration Interface',
      target: 'Real-Time Sync',
      tlod: 'SimBrief Integrated',
      render: '5 Scenery Paths',
      latency: 'Non-Destructive'
    }
  };

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const viewKey = tab.getAttribute('data-view') || 'graphics';
      const data = views[viewKey];

      if (data && stageImg) {
        stageImg.style.opacity = '0.35';
        setTimeout(() => {
          stageImg.src = data.src;
          stageImg.alt = data.alt;
          stageImg.style.opacity = '1';
        }, 150);

        if (metricTarget) metricTarget.textContent = data.target;
        if (metricTlod) metricTlod.textContent = data.tlod;
        if (metricRender) metricRender.textContent = data.render;
        if (metricLatency) metricLatency.textContent = data.latency;
      }
    });
  });
}

/* --------------------------------------------------------------------------
   6B. INTERACTIVE SCENERY HUB SWITCHER (INSPECTOR VS RADIAL)
   -------------------------------------------------------------------------- */
function initHubSwitcher() {
  const tabs = document.querySelectorAll('.hub-tab');
  const inspectorView = document.getElementById('hub-view-inspector');
  const radialView = document.getElementById('hub-view-radial');

  if (!tabs.length || !inspectorView || !radialView) return;

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const view = tab.getAttribute('data-hub-view');
      if (view === 'radial') {
        inspectorView.style.display = 'none';
        radialView.style.display = 'grid';
      } else {
        radialView.style.display = 'none';
        inspectorView.style.display = 'block';
      }
    });
  });
}

/* --------------------------------------------------------------------------
   6C. INTERACTIVE TELEMETRY SWITCHER (REPORT 1 VS OSCILLOSCOPE 2)
   -------------------------------------------------------------------------- */
function initTelemetrySwitcher() {
  const tabs = document.querySelectorAll('.report-tab');
  const img = document.getElementById('telemetry-stage-img');

  if (!tabs.length || !img) return;

  const reports = {
    '1': 'assets/visuel-win-report1.webp',
    '2': 'assets/visuel-win-report2.webp'
  };

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const view = tab.getAttribute('data-report-view') || '1';
      const src = reports[view];
      if (src) {
        img.style.opacity = '0.35';
        setTimeout(() => {
          img.src = src;
          img.style.opacity = '1';
        }, 150);
      }
    });
  });
}

/* --------------------------------------------------------------------------
   7. ACCESSIBLE FAQ ACCORDIONS
   -------------------------------------------------------------------------- */
function initFaqAccordions() {
  const faqItems = document.querySelectorAll('.faq-item');

  faqItems.forEach(item => {
    const questionBtn = item.querySelector('.faq-question');
    const answer = item.querySelector('.faq-answer');

    if (!questionBtn || !answer) return;

    questionBtn.addEventListener('click', () => {
      const isActive = item.classList.contains('active');

      faqItems.forEach(otherItem => {
        if (otherItem !== item) {
          otherItem.classList.remove('active');
          const otherAnswer = otherItem.querySelector('.faq-answer');
          const otherBtn = otherItem.querySelector('.faq-question');
          if (otherAnswer) otherAnswer.style.maxHeight = null;
          if (otherBtn) otherBtn.setAttribute('aria-expanded', 'false');
        }
      });

      if (isActive) {
        item.classList.remove('active');
        answer.style.maxHeight = null;
        questionBtn.setAttribute('aria-expanded', 'false');
      } else {
        item.classList.add('active');
        answer.style.maxHeight = answer.scrollHeight + 'px';
        questionBtn.setAttribute('aria-expanded', 'true');
      }
    });
  });
}
