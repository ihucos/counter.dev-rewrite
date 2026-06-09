<script lang="ts">
  /**
   * Sources and Countries Panel
   * Provides smart source grouping with favicons, country names with flags,
   * and "View all" modals.
   *
   * Props:
   *   refData: Record<string, number> - referrer data from query
   *   countryData: Record<string, number> - country data from query
   */
  let {
    refData = {} as Record<string, number>,
    countryData = {} as Record<string, number>
  }: {
    refData: Record<string, number>;
    countryData: Record<string, number>;
  } = $props();

  const MAX_ENTRIES = 10;

  const COUNTRIES: Record<string, string> = {
    XX: 'Unknown', T1: 'Tor network',
    AF: 'Afghanistan', AL: 'Albania', DZ: 'Algeria', AS: 'American Samoa',
    AD: 'Andorra', AO: 'Angola', AI: 'Anguilla', AQ: 'Antarctica', AG: 'Antigua And Barbuda',
    AR: 'Argentina', AM: 'Armenia', AW: 'Aruba', AU: 'Australia', AT: 'Austria', AZ: 'Azerbaijan',
    BS: 'Bahamas', BH: 'Bahrain', BD: 'Bangladesh', BB: 'Barbados', BY: 'Belarus',
    BE: 'Belgium', BZ: 'Belize', BJ: 'Benin', BM: 'Bermuda', BT: 'Bhutan', BO: 'Bolivia',
    BA: 'Bosnia And Herzegovina', BW: 'Botswana', BR: 'Brazil', BN: 'Brunei Darussalam',
    BG: 'Bulgaria', BF: 'Burkina Faso', BI: 'Burundi', KH: 'Cambodia', CM: 'Cameroon',
    CA: 'Canada', CV: 'Cape Verde', KY: 'Cayman Islands', CF: 'Central African Republic',
    TD: 'Chad', CL: 'Chile', CN: 'China', CO: 'Colombia', KM: 'Comoros', CG: 'Congo',
    CD: 'Congo, Democratic Republic', CK: 'Cook Islands', CR: 'Costa Rica', CI: "Cote D'Ivoire",
    HR: 'Croatia', CU: 'Cuba', CY: 'Cyprus', CZ: 'Czech Republic', DK: 'Denmark', DJ: 'Djibouti',
    DM: 'Dominica', DO: 'Dominican Republic', EC: 'Ecuador', EG: 'Egypt', SV: 'El Salvador',
    GQ: 'Equatorial Guinea', ER: 'Eritrea', EE: 'Estonia', ET: 'Ethiopia', FO: 'Faroe Islands',
    FJ: 'Fiji', FI: 'Finland', FR: 'France', GF: 'French Guiana', PF: 'French Polynesia',
    GA: 'Gabon', GM: 'Gambia', GE: 'Georgia', DE: 'Germany', GH: 'Ghana', GI: 'Gibraltar',
    GR: 'Greece', GL: 'Greenland', GD: 'Grenada', GP: 'Guadeloupe', GU: 'Guam', GT: 'Guatemala',
    GG: 'Guernsey', GN: 'Guinea', GW: 'Guinea-Bissau', GY: 'Guyana', HT: 'Haiti', HN: 'Honduras',
    HK: 'Hong Kong', HU: 'Hungary', IS: 'Iceland', IN: 'India', ID: 'Indonesia', IR: 'Iran',
    IQ: 'Iraq', IE: 'Ireland', IM: 'Isle Of Man', IL: 'Israel', IT: 'Italy', JM: 'Jamaica',
    JP: 'Japan', JE: 'Jersey', JO: 'Jordan', KZ: 'Kazakhstan', KE: 'Kenya', KI: 'Kiribati',
    KR: 'Korea', KW: 'Kuwait', KG: 'Kyrgyzstan', LA: "Lao People's Democratic Republic",
    LV: 'Latvia', LB: 'Lebanon', LS: 'Lesotho', LR: 'Liberia', LY: 'Libyan Arab Jamahiriya',
    LI: 'Liechtenstein', LT: 'Lithuania', LU: 'Luxembourg', MO: 'Macao', MG: 'Madagascar',
    MW: 'Malawi', MY: 'Malaysia', MV: 'Maldives', ML: 'Mali', MT: 'Malta', MH: 'Marshall Islands',
    MQ: 'Martinique', MR: 'Mauritania', MU: 'Mauritius', YT: 'Mayotte', MX: 'Mexico',
    FM: 'Micronesia', MD: 'Moldova', MC: 'Monaco', MN: 'Mongolia', ME: 'Montenegro', MS: 'Montserrat',
    MA: 'Morocco', MZ: 'Mozambique', MM: 'Myanmar', NA: 'Namibia', NR: 'Nauru', NP: 'Nepal',
    NL: 'Netherlands', NC: 'New Caledonia', NZ: 'New Zealand', NI: 'Nicaragua', NE: 'Niger',
    NG: 'Nigeria', NU: 'Niue', NF: 'Norfolk Island', MP: 'Northern Mariana Islands',
    NO: 'Norway', OM: 'Oman', PK: 'Pakistan', PW: 'Palau', PS: 'Palestine', PA: 'Panama',
    PG: 'Papua New Guinea', PY: 'Paraguay', PE: 'Peru', PH: 'Philippines', PN: 'Pitcairn',
    PL: 'Poland', PT: 'Portugal', PR: 'Puerto Rico', QA: 'Qatar', RE: 'Reunion', RO: 'Romania',
    RU: 'Russian Federation', RW: 'Rwanda', SH: 'Saint Helena', KN: 'Saint Kitts And Nevis',
    LC: 'Saint Lucia', PM: 'Saint Pierre And Miquelon', VC: 'Saint Vincent And Grenadines',
    WS: 'Samoa', SM: 'San Marino', ST: 'Sao Tome And Principe', SA: 'Saudi Arabia', SN: 'Senegal',
    RS: 'Serbia', SC: 'Seychelles', SL: 'Sierra Leone', SG: 'Singapore', SK: 'Slovakia',
    SI: 'Slovenia', SB: 'Solomon Islands', SO: 'Somalia', ZA: 'South Africa', ES: 'Spain',
    LK: 'Sri Lanka', SD: 'Sudan', SR: 'Suriname', SZ: 'Swaziland', SE: 'Sweden',
    CH: 'Switzerland', SY: 'Syrian Arab Republic', TW: 'Taiwan', TJ: 'Tajikistan',
    TZ: 'Tanzania', TH: 'Thailand', TL: 'Timor-Leste', TG: 'Togo', TK: 'Tokelau',
    TO: 'Tonga', TT: 'Trinidad And Tobago', TN: 'Tunisia', TR: 'Turkey', TM: 'Turkmenistan',
    TC: 'Turks And Caicos Islands', TV: 'Tuvalu', UG: 'Uganda', UA: 'Ukraine',
    AE: 'United Arab Emirates', GB: 'United Kingdom', US: 'United States', UY: 'Uruguay',
    UZ: 'Uzbekistan', VU: 'Vanuatu', VA: 'Vatican City', VE: 'Venezuela', VN: 'Viet Nam',
    VG: 'Virgin Islands, British', VI: 'Virgin Islands, U.S.', WF: 'Wallis And Futuna',
    EH: 'Western Sahara', YE: 'Yemen', ZM: 'Zambia', ZW: 'Zimbabwe',
  };

  interface GroupMeta { match: string[]; link: string; icon: string; }

  const GROUP_SOURCES: Record<string, GroupMeta> = {
    'Google search': {
      match: ['google.com', 'google.ad', 'google.ae', 'google.com.af', 'google.com.ag', 'google.com.ai', 'google.al', 'google.am', 'google.co.ao', 'google.com.ar', 'google.as', 'google.at', 'google.com.au', 'google.az', 'google.ba', 'google.com.bd', 'google.be', 'google.bf', 'google.bg', 'google.com.bh', 'google.bi', 'google.bj', 'google.com.bn', 'google.com.bo', 'google.com.br', 'google.bs', 'google.bt', 'google.co.bw', 'google.by', 'google.com.bz', 'google.ca', 'google.cd', 'google.cf', 'google.cg', 'google.ch', 'google.ci', 'google.co.ck', 'google.cl', 'google.cm', 'google.cn', 'google.com.co', 'google.co.cr', 'google.com.cu', 'google.cv', 'google.com.cy', 'google.cz', 'google.de', 'google.dj', 'google.dk', 'google.dm', 'google.com.do', 'google.dz', 'google.com.ec', 'google.ee', 'google.com.eg', 'google.es', 'google.com.et', 'google.fi', 'google.com.fj', 'google.fm', 'google.fr', 'google.ga', 'google.ge', 'google.gg', 'google.com.gh', 'google.com.gi', 'google.gl', 'google.gm', 'google.gr', 'google.com.gt', 'google.gy', 'google.com.hk', 'google.hn', 'google.hr', 'google.ht', 'google.hu', 'google.co.id', 'google.ie', 'google.co.il', 'google.im', 'google.co.in', 'google.iq', 'google.is', 'google.it', 'google.je', 'google.com.jm', 'google.jo', 'google.co.jp', 'google.co.ke', 'google.com.kh', 'google.ki', 'google.kg', 'google.co.kr', 'google.com.kw', 'google.kz', 'google.la', 'google.com.lb', 'google.li', 'google.lk', 'google.co.ls', 'google.lt', 'google.lu', 'google.lv', 'google.com.ly', 'google.co.ma', 'google.md', 'google.me', 'google.mg', 'google.mk', 'google.ml', 'google.com.mm', 'google.mn', 'google.ms', 'google.com.mt', 'google.mu', 'google.mv', 'google.mw', 'google.com.mx', 'google.com.my', 'google.co.mz', 'google.com.na', 'google.com.ng', 'google.com.ni', 'google.ne', 'google.nl', 'google.no', 'google.com.np', 'google.nr', 'google.nu', 'google.co.nz', 'google.com.om', 'google.com.pa', 'google.com.pe', 'google.com.pg', 'google.com.ph', 'google.com.pk', 'google.pl', 'google.pn', 'google.com.pr', 'google.ps', 'google.pt', 'google.com.py', 'google.com.qa', 'google.ro', 'google.ru', 'google.rw', 'google.com.sa', 'google.com.sb', 'google.sc', 'google.se', 'google.com.sg', 'google.sh', 'google.si', 'google.sk', 'google.com.sl', 'google.sn', 'google.so', 'google.sm', 'google.sr', 'google.st', 'google.com.sv', 'google.td', 'google.tg', 'google.co.th', 'google.com.tj', 'google.tl', 'google.tm', 'google.tn', 'google.to', 'google.com.tr', 'google.tt', 'google.com.tw', 'google.co.tz', 'google.com.ua', 'google.co.ug', 'google.co.uk', 'google.com.uy', 'google.co.uz', 'google.com.vc', 'google.co.ve', 'google.vg', 'google.co.vi', 'google.com.vn', 'google.vu', 'google.ws', 'google.rs', 'google.co.za', 'google.co.zm', 'google.co.zw', 'google.cat', 'com.google.android.googlequicksearchbox'],
      link: 'google.com', icon: 'google.com',
    },
    'Twitter/X': { match: ['t.co', 'com.twitter.android', 'twitter.com', 'x.com'], link: 'x.com', icon: 'x.com' },
    Facebook: { match: ['facebook.com', 'm.facebook.com', 'l.facebook.com', 'fb.com', 'com.facebook.katana'], link: 'facebook.com', icon: 'facebook.com' },
    Instagram: { match: ['instagram.com', 'com.instagram.android'], link: 'instagram.com', icon: 'instagram.com' },
    LinkedIn: { match: ['linkedin.com', 'linkedin.cn'], link: 'linkedin.com', icon: 'linkedin.com' },
    'Yahoo search': { match: ['yahoo.com', 'search.yahoo.com'], link: 'yahoo.com', icon: 'yahoo.com' },
    Wikipedia: { match: ['wikipedia.org'], link: 'wikipedia.org', icon: 'wikipedia.org' },
    Bing: { match: ['bing.com'], link: 'bing.com', icon: 'bing.com' },
    DuckDuckGo: { match: ['duckduckgo.com'], link: 'duckduckgo.com', icon: 'duckduckgo.com' },
    Reddit: { match: ['reddit.com', 'com.laurencedawson.reddit_sync', 'com.andrewshu.android.reddit'], link: 'reddit.com', icon: 'reddit.com' },
    Pinterest: { match: ['pinterest.com', 'pinterest.at', 'pinterest.ca', 'pinterest.ch', 'pinterest.cl', 'pinterest.co.kr', 'pinterest.co.uk', 'pinterest.com.au', 'pinterest.com.mx', 'pinterest.de', 'pinterest.dk', 'pinterest.es', 'pinterest.fr', 'pinterest.ie', 'pinterest.it', 'pinterest.jp', 'pinterest.net', 'pinterest.nz', 'pinterest.ph', 'pinterest.pt', 'pinterest.ru', 'pinterest.se', 'com.pinterest'], link: 'pinterest.com', icon: 'pinterest.com' },
    YouTube: { match: ['youtube.com', 'm.youtube.com', 'com.google.android.youtube'], link: 'youtube.com', icon: 'youtube.com' },
    WhatsApp: { match: ['whatsapp.com', 'com.whatsapp'], link: 'whatsapp.com', icon: 'whatsapp.com' },
    TikTok: { match: ['tiktok.com', 'vm.tiktok.com'], link: 'tiktok.com', icon: 'tiktok.com' },
    Telegram: { match: ['telegram.org', 't.me'], link: 'telegram.org', icon: 'telegram.org' },
  };

  let activeTab = $state('sources');
  let showSourcesModal = $state(false);
  let showCountriesModal = $state(false);

  interface SourceItem {
    group: string;
    link: string;
    icon: string;
  }

  let processed = $derived.by(() => {
    const grouped: Record<string, number> = {};
    const groupItems: Record<string, SourceItem> = {};
    for (const [ref, count] of Object.entries(refData)) {
      let cleanRef = ref;
      if (cleanRef.startsWith('www.')) cleanRef = cleanRef.slice(4);
      let info: SourceItem = { group: cleanRef, link: cleanRef, icon: cleanRef };
      for (const [groupName, meta] of Object.entries(GROUP_SOURCES)) {
        for (const m of meta.match) {
          if (cleanRef === m) {
            info = { group: groupName, link: meta.link, icon: meta.icon };
            break;
          }
        }
        if (info.group !== cleanRef) break;
      }
      groupItems[info.group] = info;
      grouped[info.group] = (grouped[info.group] || 0) + count;
    }
    return { grouped, groupItems };
  });

  let allSourcesEntries = $derived(Object.entries(processed.grouped).sort((a, b) => b[1] - a[1]));
  let sourcesEntries = $derived(allSourcesEntries.slice(0, MAX_ENTRIES));
  let sourcesTotal = $derived(Object.values(processed.grouped).reduce((a, b) => a + b, 0));

  let allCountryEntries = $derived(Object.entries(countryData).sort((a, b) => b[1] - a[1]));
  let countryEntries = $derived(allCountryEntries.slice(0, MAX_ENTRIES));
  let countriesTotal = $derived(Object.values(countryData).reduce((a, b) => a + b, 0));

  function hasSources(): boolean { return Object.keys(refData).length > 0; }
  function hasCountries(): boolean { return Object.keys(countryData).length > 0; }
  function hasData(): boolean { return hasSources() || hasCountries(); }

  function n(x: number | null | undefined): string {
    if (x == null) return '0';
    return x.toString().replace(/\B(?=(?:\d{3})+(?!\d))/g, ',');
  }

  function pctLabel(value: number, total: number): string {
    if (!total) return '0%';
    const pct = Math.round((value / total) * 100);
    return (pct === 0 && value > 0) ? '<1%' : pct + '%';
  }

  function pctWidth(value: number, total: number): number {
    if (!total) return 0;
    const pct = Math.round((value / total) * 100);
    return (pct === 0 && value > 0) ? 4 : Math.max(pct, 0);
  }

  function getCountryName(code: string): string {
    if (!code) return 'Unknown';
    return COUNTRIES[code.toUpperCase()] || code.toUpperCase();
  }

  function getCountryFlag(code: string): string {
    if (!code || code === 'xx' || code.toUpperCase() === 'XX') return '';
    const c = code.toUpperCase();
    const offset = 0x1F1E6 - 65;
    return String.fromCodePoint(c.charCodeAt(0) + offset, c.charCodeAt(1) + offset);
  }

  function getFaviconUrl(domain: string): string {
    return domain ? 'https://icons.duckduckgo.com/ip3/' + domain + '.ico' : '';
  }

  function handleFaviconError(e: Event): void {
    (e.target as HTMLElement).style.display = 'none';
  }
</script>

{#if hasData()}
  <div class="sources-countries-panel">
    <div class="tab-bar">
      {#if hasSources()}
        <button class="tab-btn" class:active={activeTab === 'sources'} onclick={() => activeTab = 'sources'}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><path d="M16.24 7.76l-2.12 6.36-6.36 2.12 2.12-6.36z"/>
          </svg>
          <span>Sources</span>
        </button>
      {/if}
      {#if hasCountries()}
        <button class="tab-btn" class:active={activeTab === 'countries'} onclick={() => activeTab = 'countries'}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
          </svg>
          <span>Countries</span>
        </button>
      {/if}
    </div>

    {#if activeTab === 'sources' && hasSources()}
      <div class="tab-content">
        <div class="items-list">
          {#each sourcesEntries as [name, count]}
            <div class="item-row">
              <div class="item-bar" style="width: {pctWidth(count, sourcesTotal)}%"></div>
              <div class="item-row-inner">
                <span class="item-label">
                  {#if processed.groupItems[name]?.icon}
                    <img class="favicon" src={getFaviconUrl(processed.groupItems[name].icon)} alt="" onerror={handleFaviconError} width="16" height="16" />
                  {/if}
                  {name}
                </span>
                <span class="item-count">{n(count)}</span>
                <span class="item-pct">{pctLabel(count, sourcesTotal)}</span>
              </div>
            </div>
          {/each}
        </div>
        {#if allSourcesEntries.length > MAX_ENTRIES}
          <button class="view-all-btn" onclick={() => showSourcesModal = true}>
            <span class="view-all-dots">
              <span class="dot"></span><span class="dot"></span><span class="dot"></span>
            </span>
            <span>View all ({allSourcesEntries.length})</span>
          </button>
        {/if}
      </div>
    {/if}

    {#if activeTab === 'countries' && hasCountries()}
      <div class="tab-content">
        <div class="items-list">
          {#each countryEntries as [code, count]}
            <div class="item-row">
              <div class="item-bar" style="width: {pctWidth(count, countriesTotal)}%"></div>
              <div class="item-row-inner">
                <span class="item-label">
                  {#if getCountryFlag(code)}
                    <span class="flag">{getCountryFlag(code)}</span>
                  {/if}
                  {getCountryName(code)}
                </span>
                <span class="item-count">{n(count)}</span>
                <span class="item-pct">{pctLabel(count, countriesTotal)}</span>
              </div>
            </div>
          {/each}
        </div>
        {#if allCountryEntries.length > MAX_ENTRIES}
          <button class="view-all-btn" onclick={() => showCountriesModal = true}>
            <span class="view-all-dots">
              <span class="dot"></span><span class="dot"></span><span class="dot"></span>
            </span>
            <span>View all ({allCountryEntries.length})</span>
          </button>
        {/if}
      </div>
    {/if}
  </div>

  {#if showSourcesModal}
    <div class="modal-overlay" onclick={() => showSourcesModal = false} role="presentation"></div>
    <div class="modal" role="dialog" aria-label="All sources">
      <div class="modal-header">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><path d="M16.24 7.76l-2.12 6.36-6.36 2.12 2.12-6.36z"/>
        </svg>
        <h3>Sources</h3>
        <button class="modal-close" onclick={() => showSourcesModal = false} aria-label="Close">&times;</button>
      </div>
      <div class="modal-body">
        <div class="items-list">
          {#each allSourcesEntries as [name, count]}
            <div class="item-row">
              <div class="item-bar" style="width: {pctWidth(count, sourcesTotal)}%"></div>
              <div class="item-row-inner">
                <span class="item-label">
                  {#if processed.groupItems[name]?.icon}
                    <img class="favicon" src={getFaviconUrl(processed.groupItems[name].icon)} alt="" onerror={handleFaviconError} width="16" height="16" />
                  {/if}
                  {name}
                </span>
                <span class="item-count">{n(count)}</span>
                <span class="item-pct">{pctLabel(count, sourcesTotal)}</span>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}

  {#if showCountriesModal}
    <div class="modal-overlay" onclick={() => showCountriesModal = false} role="presentation"></div>
    <div class="modal" role="dialog" aria-label="All countries">
      <div class="modal-header">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
        </svg>
        <h3>Countries</h3>
        <button class="modal-close" onclick={() => showCountriesModal = false} aria-label="Close">&times;</button>
      </div>
      <div class="modal-body">
        <div class="items-list">
          {#each allCountryEntries as [code, count]}
            <div class="item-row">
              <div class="item-bar" style="width: {pctWidth(count, countriesTotal)}%"></div>
              <div class="item-row-inner">
                <span class="item-label">
                  {#if getCountryFlag(code)}
                    <span class="flag">{getCountryFlag(code)}</span>
                  {/if}
                  {getCountryName(code)}
                </span>
                <span class="item-count">{n(count)}</span>
                <span class="item-pct">{pctLabel(count, countriesTotal)}</span>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}
{/if}

<style>
  .sources-countries-panel { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
  .tab-bar { display: flex; gap: 4px; border-bottom: 1px solid #e5e7eb; margin-bottom: 16px; }
  .tab-btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border: none; background: none; font-size: 13px; color: #888; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; font-family: inherit; }
  .tab-btn:hover { color: #555; background: #f9fafb; border-radius: 6px 6px 0 0; }
  .tab-btn.active { color: #2563eb; border-bottom-color: #2563eb; font-weight: 600; }
  .tab-btn svg { width: 16px; height: 16px; flex-shrink: 0; }
  .tab-content { min-height: 100px; }
  .items-list { display: flex; flex-direction: column; gap: 2px; }
  .item-row { position: relative; display: flex; align-items: center; height: 40px; padding: 0 12px; border-radius: 20px; overflow: hidden; }
  .item-bar { position: absolute; left: 0; top: 0; height: 100%; background: #e7f6ff; border-radius: 20px; transition: width 0.3s ease; min-width: 4px; }
  .item-row-inner { position: relative; z-index: 1; display: flex; align-items: center; width: 100%; gap: 8px; }
  .item-label { flex: 1; font-size: 13px; color: #444; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: flex; align-items: center; gap: 8px; }
  .favicon { width: 16px; height: 16px; border-radius: 2px; flex-shrink: 0; }
  .flag { font-size: 16px; line-height: 1; }
  .item-count { font-size: 13px; font-weight: 600; color: #111; white-space: nowrap; }
  .item-pct { font-size: 11px; color: #888; width: 36px; text-align: right; flex-shrink: 0; }
  .view-all-btn { display: flex; align-items: center; gap: 10px; width: 100%; margin-top: 8px; padding: 12px 16px; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 10px; cursor: pointer; font-size: 14px; color: #555; font-family: inherit; }
  .view-all-btn:hover { background: #f3f4f6; border-color: #d1d5db; color: #333; }
  .view-all-dots { display: flex; gap: 3px; }
  .dot { width: 6px; height: 6px; border-radius: 50%; background: #2563eb; }
  .dot:nth-child(2) { opacity: 0.5; }
  .dot:nth-child(3) { opacity: 0.3; }
  .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 999; }
  .modal { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; border-radius: 12px; width: 90%; max-width: 480px; max-height: 80vh; overflow-y: auto; z-index: 1000; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
  .modal-header { display: flex; align-items: center; gap: 8px; padding: 20px 24px 0; }
  .modal-header h3 { margin: 0; font-size: 18px; flex: 1; }
  .modal-close { background: none; border: none; font-size: 28px; cursor: pointer; color: #888; padding: 0; line-height: 1; }
  .modal-close:hover { color: #333; }
  .modal-body { padding: 16px 24px 24px; }
</style>
