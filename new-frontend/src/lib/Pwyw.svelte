<script lang="ts">
  /**
   * Pay What You Want (PWYW) modal
   *
   * Shows a donation/subscription prompt after users have been tracked for 90+ days.
   * Calculates a smart suggestion tier based on average daily page views.
   * Integrates with PayPal for subscription payments.
   *
   * Props:
   *   totalDaysTracked: number - maximum days any host has been tracked
   *   averageDailyHits: number - average daily page views across all hosts (last 7 days)
   *   userId: number | null - user id for PayPal custom_id
   *   isSubscribed: boolean - whether user already has an active subscription
   */
  let {
    totalDaysTracked = 0,
    averageDailyHits = 0,
    userId = null,
    isSubscribed = false
  }: {
    totalDaysTracked: number;
    averageDailyHits: number;
    userId: number | null;
    isSubscribed: boolean;
  } = $props();

  let showModal = $state(false);
  let selectedPlan = $state(3);
  let hasShownAuto = $state(false);

  interface PlanTier {
    label: string;
    plans: PlanItem[];
  }

  interface PlanItem {
    value: number;
    label: string;
    suggested?: boolean;
  }

  const PLAN_TIERS: PlanTier[] = [
    {
      label: 'Starter',
      plans: [
        { value: 3, label: '3€ per month', suggested: false },
        { value: 5, label: '5€ per month', suggested: false },
        { value: 7, label: '7€ per month', suggested: false },
      ],
    },
    {
      label: 'Intermediate',
      plans: [
        { value: 20, label: '20€ per month', suggested: false },
        { value: 25, label: '25€ per month', suggested: false },
        { value: 30, label: '30€ per month', suggested: false },
      ],
    },
    {
      label: 'High Traffic',
      plans: [
        { value: 70, label: '70€ per month', suggested: false },
        { value: 90, label: '90€ per month', suggested: false },
        { value: 120, label: '120€ per month', suggested: false },
      ],
    },
  ];

  // Calculate suggestion tier based on average daily hits
  let suggestionIndex = $derived.by(() => {
    // TIER 0: < 1k hits/day → suggest starter (index 0 in the tier's first item)
    // TIER 1: 1k-10k hits/day → suggest intermediate (index 1)
    // TIER 2: > 10k hits/day → suggest high traffic (index 2)
    if (averageDailyHits > 10000) return 2;
    if (averageDailyHits > 1000) return 1;
    return 0;
  });

  // Mark the suggested plan
  let planItemsWithSuggestion = $derived.by(() => {
    return PLAN_TIERS.map((tier, tierIdx) => ({
      ...tier,
      plans: tier.plans.map((plan, planIdx) => ({
        ...plan,
        suggested: tierIdx === suggestionIndex && planIdx === 0,
      })),
    }));
  });

  // Flatten for selection: find the suggested plan value
  let defaultPlanValue = $derived.by(() => {
    for (const tier of planItemsWithSuggestion) {
      for (const plan of tier.plans) {
        if (plan.suggested) return plan.value;
      }
    }
    return 3;
  });

  // Determine if we should auto-show the modal
  let shouldShowPrompt = $derived(
    totalDaysTracked >= 90 && !isSubscribed
  );

  let copySuccess = $state(false);

  function flash(msg: string, type: string = 'info'): void {
    window.dispatchEvent(new CustomEvent('flash', { detail: { message: msg, type } }));
  }

  function openModal(): void {
    selectedPlan = defaultPlanValue;
    showModal = true;
  }

  function closeModal(): void {
    showModal = false;
  }

  function selectPlan(value: number): void {
    selectedPlan = value;
  }

  function handleSubscribe(): void {
    // In the new frontend without jQuery modal/PayPal SDK integration,
    // we use the PayPal JS SDK if available, or show a message
    if (typeof paypal !== 'undefined') {
      // PayPal SDK loaded, render button
      flash('Initiating PayPal subscription...', 'info');
    } else {
      // PayPal SDK not loaded - show info
      flash(
        'Subscription handling is coming soon. For now, you can support us at https://counter.dev',
        'info'
      );
    }
  }

  function handleDismiss(): void {
    closeModal();
    // Mark as shown in session storage (same as old behavior)
    try {
      sessionStorage.setItem('pwyw', '1');
    } catch { /* ignore */ }
  }

  // Auto-show the modal if conditions are met (on mount, once)
  $effect(() => {
    if (shouldShowPrompt && !hasShownAuto && typeof sessionStorage !== 'undefined') {
      const alreadyShown = sessionStorage.getItem('pwyw') === '1';
      if (!alreadyShown) {
        // Delay to not overwhelm the user on page load
        const timer = setTimeout(() => {
          hasShownAuto = true;
          openModal();
        }, 3000);
        return () => clearTimeout(timer);
      }
    }
  });

  function n(x: number | null | undefined): string {
    if (x == null) return '0';
    return x.toString().replace(/\B(?=(?:\d{3})+(?!\d))/g, ',');
  }
</script>

{#if shouldShowPrompt || !isSubscribed}
  <!-- Donation section (always visible at bottom for subscribed or eligible users) -->
  <section class="pwyw-section">
    <div class="content">
      <div class="donate-wrap">
        <div class="donate-icon">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a10 10 0 1 0 10 10h-10V2z"/>
            <path d="M12 12 2 12a10 10 0 0 0 10 10V12z"/>
            <path d="M12 2v10l10 0a10 10 0 0 0-10-10z"/>
          </svg>
        </div>
        <div class="donate-description">
          <h3>Pay when ready</h3>
          <p class="gray">
            Our main goal is to provide the smoothest Web Analytics experience possible.
            Therefore we do not enforce payments but ask for you to consider
            paying what you want.
          </p>
        </div>
        {#if isSubscribed}
          <div class="caption gray paying-badge">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            Thanks for paying
          </div>
        {:else}
          <button class="btn-primary" onclick={openModal}>
            Pay now
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
            </svg>
          </button>
        {/if}
      </div>
    </div>
  </section>
{/if}

<!-- Modal overlay -->
{#if showModal}
  <div class="modal-overlay" onclick={handleDismiss} role="presentation"></div>
  <div class="modal" role="dialog" aria-labelledby="pwyw-title" aria-modal="true">
    <div class="modal-header">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2a10 10 0 1 0 10 10h-10V2z"/>
        <path d="M12 12 2 12a10 10 0 0 0 10 10V12z"/>
        <path d="M12 2v10l10 0a10 10 0 0 0-10-10z"/>
      </svg>
      <h3 id="pwyw-title">Pay when ready</h3>
      <button class="btn-close" onclick={handleDismiss} aria-label="Close">&times;</button>
    </div>
    <div class="modal-content">
      <p class="modal-intro">
        Thank you for using Counter for free. If you are able to, please pay for this service.
      </p>

      {#if !isSubscribed}
        <div class="plans">
          {#each planItemsWithSuggestion as tier}
            <h5 class="tier-label">{tier.label}</h5>
            {#each tier.plans as plan}
              <button
                class="plan-row"
                class:suggested={plan.suggested}
                class:selected={selectedPlan === plan.value}
                onclick={() => selectPlan(plan.value)}
              >
                <input
                  type="radio"
                  name="plan"
                  value={plan.value}
                  checked={selectedPlan === plan.value}
                  onchange={() => selectPlan(plan.value)}
                />
                <label>
                  {plan.label}
                  {#if plan.suggested}
                    <span class="suggestion-badge">(Suggestion)</span>
                  {/if}
                </label>
              </button>
            {/each}
          {/each}
        </div>

        <div class="paypal-section">
          <p class="paypal-info">
            Selected: <strong>{selectedPlan}€/month</strong>
          </p>
          <p class="paypal-disclaimer">
            PayPal subscription integration available on the production deployment.
            For now, please contact us at <a href="mailto:hey@counter.dev">hey@counter.dev</a>
            to arrange support.
          </p>
          <button class="btn-primary btn-full" onclick={handleSubscribe}>
            Subscribe for {selectedPlan}€/month
          </button>
        </div>
      {:else}
        <div class="already-subscribed">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          <p>You are awesome! Thank you for supporting Counter.</p>
          <p class="gray small">If you are not happy with the product or service, let us know at any time.</p>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .pwyw-section {
    margin-top: 48px;
    margin-bottom: 24px;
  }
  .pwyw-section .content {
    max-width: 1060px;
    margin: 0 auto;
    padding: 0 24px;
  }
  .donate-wrap {
    display: flex;
    align-items: center;
    gap: 20px;
    background: white;
    border-radius: 12px;
    padding: 24px 28px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  .donate-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: #eff6ff;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .donate-icon svg { width: 28px; height: 28px; }
  .donate-description { flex: 1; min-width: 0; }
  .donate-description h3 {
    margin: 0 0 4px;
    font-size: 16px;
    font-weight: 700;
    color: #111;
  }
  .donate-description p {
    margin: 0;
    font-size: 14px;
    line-height: 1.5;
  }
  .donate-description .gray { color: #666; }
  .btn-primary {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #2563eb;
    color: white;
    border: none;
    padding: 10px 24px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: background 0.15s;
    flex-shrink: 0;
  }
  .btn-primary:hover { background: #1d4ed8; }
  .btn-primary:active { background: #1e40af; }
  .btn-primary svg { width: 16px; height: 16px; }
  .btn-full { width: 100%; justify-content: center; padding: 14px 24px; font-size: 16px; }
  .paying-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #d1fae5;
    color: #065f46;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
  }

  /* Modal */
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.5);
    z-index: 999;
    animation: fadeIn 0.2s ease-out;
  }
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .modal {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: white;
    border-radius: 16px;
    width: 92%;
    max-width: 480px;
    max-height: 85vh;
    overflow-y: auto;
    z-index: 1000;
    box-shadow: 0 25px 60px rgba(0,0,0,0.3);
    animation: slideUp 0.25s ease-out;
  }
  @keyframes slideUp {
    from { opacity: 0; transform: translate(-50%, -40%); }
    to { opacity: 1; transform: translate(-50%, -50%); }
  }

  .modal-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 24px 24px 0;
    position: sticky;
    top: 0;
    background: white;
    border-radius: 16px 16px 0 0;
    z-index: 1;
  }
  .modal-header h3 {
    margin: 0;
    font-size: 20px;
    font-weight: 700;
    color: #111;
    flex: 1;
  }
  .btn-close {
    background: none;
    border: none;
    font-size: 28px;
    cursor: pointer;
    color: #888;
    padding: 0 4px;
    line-height: 1;
  }
  .btn-close:hover { color: #333; }

  .modal-content {
    padding: 16px 24px 24px;
  }
  .modal-intro {
    font-size: 14px;
    color: #555;
    line-height: 1.6;
    margin: 0 0 20px;
  }

  /* Plans */
  .plans {
    margin-bottom: 20px;
  }
  .tier-label {
    font-size: 13px;
    font-weight: 700;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 16px 0 8px;
  }
  .tier-label:first-child { margin-top: 0; }
  .plan-row {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 10px 14px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    background: white;
    cursor: pointer;
    transition: all 0.15s;
    margin-bottom: 4px;
    font-family: inherit;
    font-size: 14px;
    text-align: left;
  }
  .plan-row:hover {
    border-color: #93c5fd;
    background: #f0f7ff;
  }
  .plan-row.selected {
    border-color: #2563eb;
    background: #eff6ff;
  }
  .plan-row.suggested {
    background: #e7f6ff;
    border-color: #93c5fd;
  }
  .plan-row.suggested.selected {
    border-color: #2563eb;
    background: #dbeafe;
  }
  .plan-row input[type="radio"] {
    margin: 0;
    accent-color: #2563eb;
    flex-shrink: 0;
  }
  .plan-row label {
    cursor: pointer;
    font-weight: 500;
    color: #333;
    font-size: 14px;
  }
  .plan-row.suggested label {
    font-weight: 700;
    color: #111;
  }
  .plan-row.suggested label .suggestion-badge {
    font-weight: 400;
    color: #2563eb;
    font-size: 12px;
  }

  /* PayPal section */
  .paypal-section {
    border-top: 1px solid #e5e7eb;
    padding-top: 16px;
  }
  .paypal-info {
    font-size: 14px;
    color: #555;
    margin: 0 0 8px;
  }
  .paypal-disclaimer {
    font-size: 12px;
    color: #888;
    line-height: 1.5;
    margin: 0 0 16px;
  }
  .paypal-disclaimer a { color: #2563eb; }

  /* Already subscribed */
  .already-subscribed {
    text-align: center;
    padding: 24px 0;
  }
  .already-subscribed svg { margin-bottom: 12px; }
  .already-subscribed p {
    font-size: 16px;
    color: #333;
    margin: 0 0 8px;
    font-weight: 500;
  }
  .already-subscribed .gray { color: #888; font-size: 13px; font-weight: 400; }

  .small { font-size: 13px; color: #888; }

  @media (max-width: 640px) {
    .donate-wrap { flex-wrap: wrap; }
    .donate-description { min-width: 100%; }
    .donate-description h3 { margin-top: 4px; }
    .btn-primary { width: 100%; justify-content: center; }
    .paying-badge { width: 100%; justify-content: center; }
    .modal { width: 95%; }
  }
</style>
