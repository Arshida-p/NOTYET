/**
 * NOTYET - Community Validation Client Script (Feature 3)
 * Handles AJAX upvoting, duplicate vote prevention sync, search UI,
 * reason modals, and dynamic demand progress updates.
 */

document.addEventListener('DOMContentLoaded', () => {
  const LOCAL_STORAGE_KEY = 'notyet_validated_needs';

  // 1. Retrieve validated IDs from server session & client localStorage
  function getValidatedIds() {
    let localIds = [];
    try {
      const stored = localStorage.getItem(LOCAL_STORAGE_KEY);
      if (stored) {
        localIds = JSON.parse(stored);
      }
    } catch (e) {
      localIds = [];
    }

    // Merge with server session validated IDs injected into DOM
    const sessionIdsContainer = document.getElementById('userValidatedIds');
    let sessionIds = [];
    if (sessionIdsContainer && sessionIdsContainer.dataset.ids) {
      try {
        sessionIds = JSON.parse(sessionIdsContainer.dataset.ids);
      } catch (e) {
        sessionIds = [];
      }
    }

    const merged = Array.from(new Set([...localIds, ...sessionIds].map(Number)));
    try {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(merged));
    } catch (e) {}

    return merged;
  }

  function saveValidatedId(id) {
    const numId = Number(id);
    const current = getValidatedIds();
    if (!current.includes(numId)) {
      current.push(numId);
      try {
        localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(current));
      } catch (e) {}
    }
  }

  // 2. Mark cards as already validated
  function applyValidatedStateToCards() {
    const validatedIds = getValidatedIds();
    validatedIds.forEach(id => {
      const card = document.querySelector(`.validation-card[data-need-id="${id}"]`);
      if (card) {
        const validateBtn = card.querySelector('.btn-validate-main');
        if (validateBtn) {
          validateBtn.classList.add('btn-already-validated');
          validateBtn.setAttribute('disabled', 'disabled');
          validateBtn.innerHTML = '<span>✓</span> Validated by You';
        }
        const commentBtn = card.querySelector('.btn-validate-comment');
        if (commentBtn) {
          commentBtn.style.opacity = '0.5';
          commentBtn.title = 'You have already added your validation to this request.';
        }
      }
    });
  }

  applyValidatedStateToCards();

  // 3. Search Bar UI: clear button logic
  const searchInput = document.getElementById('validationSearchInput');
  const searchClearBtn = document.getElementById('searchClearBtn');

  if (searchInput && searchClearBtn) {
    function toggleClearBtn() {
      searchClearBtn.style.display = searchInput.value.trim().length > 0 ? 'block' : 'none';
    }

    searchInput.addEventListener('input', toggleClearBtn);
    toggleClearBtn();

    searchClearBtn.addEventListener('click', () => {
      searchInput.value = '';
      toggleClearBtn();
      if (searchInput.form) {
        searchInput.form.submit();
      }
    });
  }

  // 4. Modal Handlers
  const validationModal = document.getElementById('validationReasonModal');
  const storiesModal = document.getElementById('storiesModal');

  function openModal(modal) {
    if (modal) {
      modal.classList.add('is-active');
      document.body.style.overflow = 'hidden';
    }
  }

  function closeModal(modal) {
    if (modal) {
      modal.classList.remove('is-active');
      document.body.style.overflow = '';
    }
  }

  // Close modals on backdrop click or close button
  document.querySelectorAll('.modal-close-btn, .modal-cancel-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const modal = e.target.closest('.validation-modal-backdrop');
      closeModal(modal);
    });
  });

  document.querySelectorAll('.validation-modal-backdrop').forEach(backdrop => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        closeModal(backdrop);
      }
    });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal(validationModal);
      closeModal(storiesModal);
    }
  });

  // 5. Open Validation Reason Modal when clicking "Add Reason" or quick validate
  document.querySelectorAll('.btn-open-reason-modal').forEach(btn => {
    btn.addEventListener('click', () => {
      const card = btn.closest('.validation-card');
      const needId = card.dataset.needId;
      const needTitle = card.dataset.needTitle;

      const validatedIds = getValidatedIds();
      if (validatedIds.includes(Number(needId))) {
        showToast('You have already validated this community request.', 'info');
        return;
      }

      document.getElementById('modalNeedId').value = needId;
      document.getElementById('modalNeedTitleText').textContent = needTitle;
      document.getElementById('modalSupporterName').value = '';
      document.getElementById('modalSupportReason').value = '';

      openModal(validationModal);
      setTimeout(() => {
        const reasonInput = document.getElementById('modalSupportReason');
        if (reasonInput) reasonInput.focus();
      }, 100);
    });
  });

  // 6. Handle Validation Form Submissions via AJAX
  async function submitValidation(needId, supporterName, supportReason, formElement) {
    const validatedIds = getValidatedIds();
    if (validatedIds.includes(Number(needId))) {
      showToast('You have already validated this community request.', 'info');
      return;
    }

    const formData = new FormData();
    formData.append('supporter_name', supporterName || 'Supportive Neighbour');
    if (supportReason) {
      formData.append('support_reason', supportReason);
    }

    // Visual button loading state
    let targetBtn = null;
    if (formElement) {
      targetBtn = formElement.querySelector('button[type="submit"]');
      if (targetBtn) {
        targetBtn.disabled = true;
        targetBtn.dataset.origText = targetBtn.innerHTML;
        targetBtn.innerHTML = '<span>⏳</span> Validating...';
      }
    }

    try {
      const response = await fetch(`/validate/${needId}`, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        saveValidatedId(needId);
        updateCardUiAfterValidation(needId, data);
        closeModal(validationModal);
        showToast(data.message, 'success');
      } else if (data.status === 'already_validated') {
        saveValidatedId(needId);
        applyValidatedStateToCards();
        closeModal(validationModal);
        showToast(data.message, 'info');
      } else {
        showToast(data.message || 'Validation failed. Please try again.', 'error');
      }
    } catch (err) {
      console.warn('AJAX validation error, falling back to standard submit:', err);
      if (formElement) {
        formElement.submit();
      }
    } finally {
      if (targetBtn && targetBtn.dataset.origText) {
        targetBtn.disabled = false;
        targetBtn.innerHTML = targetBtn.dataset.origText;
      }
    }
  }

  // Listen for Quick Validate (+1) direct button submits
  document.querySelectorAll('.form-quick-validate').forEach(form => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const needId = form.dataset.needId;
      submitValidation(needId, 'Neighbourhood Resident', '', form);
    });
  });

  // Listen for Reason Modal submission
  const modalForm = document.getElementById('modalValidationForm');
  if (modalForm) {
    modalForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const needId = document.getElementById('modalNeedId').value;
      const supporterName = document.getElementById('modalSupporterName').value.trim();
      const supportReason = document.getElementById('modalSupportReason').value.trim();
      submitValidation(needId, supporterName, supportReason, modalForm);
    });
  }

  // 7. Update Card UI in place without full page refresh
  function updateCardUiAfterValidation(needId, data) {
    const card = document.querySelector(`.validation-card[data-need-id="${needId}"]`);
    if (!card) return;

    // Update Counter
    const counterEl = card.querySelector('.validation-counter-val');
    if (counterEl) {
      counterEl.textContent = data.validation_count;
      counterEl.classList.add('counter-bump');
      setTimeout(() => counterEl.classList.remove('counter-bump'), 600);
    }

    // Update Badge & Milestone
    if (data.demand_info) {
      const badgeEl = card.querySelector('.card-demand-badge');
      if (badgeEl) {
        badgeEl.className = `card-demand-badge ${data.demand_info.class_name}`;
        badgeEl.innerHTML = `${data.demand_info.icon} ${data.demand_info.label}`;
      }

      const progressFill = card.querySelector('.demand-progress-fill');
      if (progressFill) {
        progressFill.style.width = `${data.demand_info.percent}%`;
      }

      const progressTarget = card.querySelector('.progress-header-target');
      if (progressTarget) {
        progressTarget.textContent = data.demand_info.description;
      }
    }

    // If reason was entered, inject into neighbor stories preview
    if (data.support_reason) {
      let previewBox = card.querySelector('.neighbor-reasons-preview');
      if (!previewBox) {
        previewBox = document.createElement('div');
        previewBox.className = 'neighbor-reasons-preview';
        const descEl = card.querySelector('.need-desc');
        if (descEl && descEl.parentNode) {
          descEl.parentNode.insertBefore(previewBox, descEl.nextSibling);
        }
      }

      previewBox.innerHTML = `
        <div class="reasons-header-row">
          <span>💬 Neighbor Voices</span>
          <span style="color: #a7f3d0; font-size: 0.72rem;">Just Added</span>
        </div>
        <p class="reason-quote-snippet">"${escapeHtml(data.support_reason)}"</p>
        <div class="reason-supporter-meta">— ${escapeHtml(data.supporter_name || 'Neighbour')}, just now</div>
      `;
    }

    // Mark Button as Validated
    const validateBtn = card.querySelector('.btn-validate-main');
    if (validateBtn) {
      validateBtn.classList.add('btn-already-validated');
      validateBtn.setAttribute('disabled', 'disabled');
      validateBtn.innerHTML = '<span>✓</span> Validated by You';
    }

    const commentBtn = card.querySelector('.btn-validate-comment');
    if (commentBtn) {
      commentBtn.style.opacity = '0.5';
    }
  }

  // 8. View All Stories Modal
  document.querySelectorAll('.view-stories-trigger').forEach(trigger => {
    trigger.addEventListener('click', async (e) => {
      e.preventDefault();
      const needId = trigger.dataset.needId;
      const needTitle = trigger.dataset.needTitle;

      document.getElementById('storiesModalNeedTitle').textContent = needTitle;
      const listContainer = document.getElementById('storiesModalList');
      listContainer.innerHTML = '<p style="color: var(--text-dim); text-align: center; padding: 2rem;">Loading neighbor stories...</p>';
      openModal(storiesModal);

      try {
        const res = await fetch(`/api/need/${needId}/validations`);
        const stories = await res.json();

        if (stories && stories.length > 0) {
          listContainer.innerHTML = stories.map(s => `
            <div class="story-item">
              <div class="story-item-header">
                <span class="story-author">👤 ${escapeHtml(s.supporter_name || 'Neighbour')}</span>
                <span class="story-date">${s.created_at ? s.created_at.substring(0, 10) : ''}</span>
              </div>
              <p class="story-text">"${escapeHtml(s.support_reason || 'Endorsed this community need.')}"</p>
            </div>
          `).join('');
        } else {
          listContainer.innerHTML = '<p style="color: var(--text-dim); text-align: center; padding: 1.5rem;">No written reasons submitted yet for this need.</p>';
        }
      } catch (err) {
        listContainer.innerHTML = '<p style="color: var(--accent-rose); text-align: center; padding: 1.5rem;">Unable to load neighbor stories right now.</p>';
      }
    });
  });

  // 9. Toast Notification Helper
  function showToast(message, type = 'info') {
    let container = document.querySelector('.alerts-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'alerts-container';
      const main = document.querySelector('.main-wrapper') || document.body;
      main.insertBefore(container, main.firstChild);
    }

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.setAttribute('role', 'alert');
    alert.innerHTML = `
      <span>${escapeHtml(message)}</span>
      <button type="button" class="alert-close" aria-label="Dismiss alert">&times;</button>
    `;

    container.appendChild(alert);

    alert.querySelector('.alert-close').addEventListener('click', () => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-6px)';
      setTimeout(() => alert.remove(), 250);
    });

    setTimeout(() => {
      if (alert && alert.parentElement) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-6px)';
        setTimeout(() => alert.remove(), 250);
      }
    }, 5000);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
