/* ─── Tag data ──────────────────────────────────────────────── */
  const TAG_DATA = [
    { id: 'politics',      icon: '🏛️' },
    { id: 'technology',    icon: '💻' },
    { id: 'lifestyle',     icon: '🌿' },
    { id: 'food',          icon: '🍕' },
    { id: 'work',          icon: '💼' },
    { id: 'animals',       icon: '🐾' },
    { id: 'sports',        icon: '⚽' },
    { id: 'entertainment', icon: '🎬' },
  ];

  const MAX_TAGS = 1;
  let selectedTags = new Set();

  /* ─── Render tag buttons ────────────────────────────────────── */
  const wrap = document.getElementById('tags-wrap');
  TAG_DATA.forEach(({ id, icon }) => {
    const btn = document.createElement('button');
    btn.type = 'button'; // prevent accidental form submit
    btn.className = 'tag';
    btn.dataset.tag = id;
    btn.innerHTML = `<span>${icon}</span> ${id}`;
    btn.addEventListener('click', () => toggleTag(id, btn));
    wrap.appendChild(btn);
  });

  function toggleTag(id, btn) {
    if (selectedTags.has(id)) {
      selectedTags.delete(id);
      btn.classList.remove('selected');
    } else {
      if (selectedTags.size >= MAX_TAGS) return;
      selectedTags.add(id);
      btn.classList.add('selected');
    }
    updateTagState();
  }

  function updateTagState() {
    const count = selectedTags.size;
    document.getElementById('tag-count').textContent = `${count}/${MAX_TAGS} tags selected`;
    document.querySelectorAll('.tag').forEach(btn => {
      const isSelected = selectedTags.has(btn.dataset.tag);
      btn.classList.toggle('disabled', count >= MAX_TAGS && !isSelected);
    });
    validateForm();
  }

  /* ─── Duration slider ───────────────────────────────────────── */
  const slider  = document.getElementById('duration');
  const durVal  = document.getElementById('duration-val');

  function updateSliderBackground() {
    const pct = ((slider.value - slider.min) / (slider.max - slider.min)) * 100;
    slider.style.background =
      `linear-gradient(to right, var(--accent) ${pct}%, var(--border) ${pct}%)`;
  }

  slider.addEventListener('input', () => {
    const h = parseInt(slider.value);
    durVal.textContent = h === 1 ? '1 hour' : `${h} hours`;
    updateSliderBackground();
  });
  updateSliderBackground();

  /* ─── Validation ────────────────────────────────────────────── */
  const promptEl  = document.getElementById('prompt');
  const submitBtn = document.getElementById('submit-btn');

  promptEl.addEventListener('input', validateForm);

  function validateForm() {
    submitBtn.disabled = promptEl.value.trim().length === 0;
  }

  /* ─── Submit — populate hidden fields, then submit form ─────── */
  function handleSubmit() {
    const title = promptEl.value.trim();
    if (!title) return;

    // description mirrors the title (single-field form)
    document.getElementById('description-hidden').value = title;

    // category = first selected tag, or 'general' if none chosen
    document.getElementById('category-hidden').value =
      selectedTags.size > 0 ? [...selectedTags][0] : 'general';

    // convert hours → days (min 1, max 14)
    const hours = parseInt(slider.value);
    const days  = Math.max(1, Math.min(14, Math.ceil(hours / 24)));
    document.getElementById('duration-days-hidden').value = days;

    document.getElementById('debate-form').submit();
  }

  /* ─── Cancel ────────────────────────────────────────────────── */
  function handleCancel() {
    if (promptEl.value.trim() || selectedTags.size) {
      if (confirm('Discard this debate?')) window.location.href = '/dashboard';
    } else {
      window.location.href = '/dashboard';
    }
  }

  /* ─── Toast (kept for any future use) ──────────────────────── */
  let toastTimer;
  function showToast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('show'), 3000);
  }