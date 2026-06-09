<script lang="ts">
  /**
   * Traffic Sources Panel
   * Displays summary metrics: Visits, Search Engines, Social Networks, Direct Traffic.
   *
   * Props:
   *   queryData: object - the raw query response from the API
   */
  let { queryData = {} as Record<string, Record<string, number>> }: { queryData: Record<string, Record<string, number>> } = $props();

  const SEARCH_ENGINES = new Set([
    'google.com', 'bing.com', 'yahoo.com', 'duckduckgo.com', 'baidu.com', 'yandex.com',
    'ask.com', 'aol.com', 'seznam.cz', 'naver.com', 'sogou.com',
    'ecosia.org', 'startpage.com', 'qwant.com', 'search.brave.com',
  ]);

  const SOCIAL_NETWORKS = new Set([
    'facebook.com', 'twitter.com', 'linkedin.com', 'reddit.com',
    'pinterest.com', 'instagram.com', 'tumblr.com', 'youtube.com',
    'whatsapp.com', 'snapchat.com', 'tiktok.com', 'discord.com',
    'telegram.org', 'vk.com', 'weibo.com', 'medium.com',
    'dev.to', 'indiehackers.com', 't.co', 'fb.com',
    'm.facebook.com', 'l.facebook.com',
  ]);

  function getDomain(referrer: string): string {
    try {
      return new URL(referrer.startsWith('http') ? referrer : 'https://' + referrer).hostname.replace(/^www\./, '');
    } catch {
      return referrer;
    }
  }

  function isSearchEngine(referrer: string): boolean {
    if (!referrer) return false;
    const domain = getDomain(referrer);
    if (SEARCH_ENGINES.has(domain)) return true;
    if (domain.endsWith('.google.com') || domain.endsWith('.google.co.uk') ||
        domain.endsWith('.google.fr') || domain.endsWith('.google.de') ||
        domain.endsWith('.google.es') || domain.endsWith('.google.it') ||
        domain.endsWith('.google.ca') || domain.endsWith('.google.com.au') ||
        domain.endsWith('.google.co.in') || domain.endsWith('.google.co.jp') ||
        domain.endsWith('.google.ru') || domain.endsWith('.google.com.br') ||
        domain.endsWith('.google.com.mx') || domain.endsWith('.yahoo.com') ||
        domain.endsWith('.bing.com') || domain.endsWith('.yandex.com') ||
        domain.endsWith('.baidu.com')) return true;
    return false;
  }

  function isSocialNetwork(referrer: string): boolean {
    if (!referrer) return false;
    const domain = getDomain(referrer);
    for (const social of SOCIAL_NETWORKS) {
      if (domain === social || domain.endsWith('.' + social)) return true;
    }
    return false;
  }

  let totalVisits = $derived.by(() => {
    if (!queryData['date']) return 0;
    return Object.values(queryData['date']).reduce((a: number, b: number) => a + b, 0);
  });

  let totalReferrerTraffic = $derived.by(() => {
    if (!queryData['ref']) return 0;
    return Object.values(queryData['ref']).reduce((a: number, b: number) => a + b, 0);
  });

  let directTraffic = $derived(totalVisits - totalReferrerTraffic);

  let searchTraffic = $derived.by(() => {
    if (!queryData['ref']) return 0;
    let total = 0;
    for (const [referrer, count] of Object.entries(queryData['ref'])) {
      if (isSearchEngine(referrer)) total += count;
    }
    return total;
  });

  let socialTraffic = $derived.by(() => {
    if (!queryData['ref']) return 0;
    let total = 0;
    for (const [referrer, count] of Object.entries(queryData['ref'])) {
      if (isSocialNetwork(referrer)) total += count;
    }
    return total;
  });

  function n(x: number | null | undefined): string {
    if (x == null) return '0';
    return x.toString().replace(/\B(?=(?:\d{3})+(?!\d))/g, ',');
  }

  function hasData(): boolean {
    return totalVisits > 0;
  }
</script>

{#if hasData()}
  <section class="traffic-sources">
    <div class="content">
      <div class="counter-card">
        <div class="counter-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17V11"/>
          </svg>
        </div>
        <div class="counter-info">
          <span class="counter-value">{n(totalVisits)}</span>
          <span class="counter-label">Visits</span>
        </div>
      </div>

      <div class="counter-card">
        <div class="counter-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
          </svg>
        </div>
        <div class="counter-info">
          <span class="counter-value">{n(searchTraffic)}</span>
          <span class="counter-label">Search engines</span>
        </div>
      </div>

      <div class="counter-card">
        <div class="counter-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>
          </svg>
        </div>
        <div class="counter-info">
          <span class="counter-value">{n(socialTraffic)}</span>
          <span class="counter-label">Social networks</span>
        </div>
      </div>

      <div class="counter-card">
        <div class="counter-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
        </div>
        <div class="counter-info">
          <span class="counter-value">{n(Math.max(0, directTraffic))}</span>
          <span class="counter-label">Direct</span>
        </div>
      </div>
    </div>
  </section>
{/if}

<style>
  .traffic-sources {
    margin-top: 24px;
  }
  .traffic-sources .content {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    max-width: 1060px;
    margin: 0 auto;
    padding: 0 24px;
  }
  .counter-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  .counter-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: #eff6ff;
    color: #2563eb;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .counter-icon svg {
    width: 24px;
    height: 24px;
  }
  .counter-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .counter-value {
    font-size: 24px;
    font-weight: 700;
    color: #111;
    line-height: 1.2;
  }
  .counter-label {
    font-size: 13px;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  @media (max-width: 900px) {
    .traffic-sources .content { grid-template-columns: repeat(2, 1fr); }
  }
  @media (max-width: 500px) {
    .traffic-sources .content { grid-template-columns: 1fr; }
  }
</style>
