    const API = '/api';

    function app() {
      return {
        _prevPage: null,
        page: 'home',
        period: '31st March 2025',
        market: 'india',
        reportPeriods: ['All periods', '31st March 2025'],
        counts: {},
        tickers: [],
        navCards: { home: 'Home', recommendations: '⬡ Recommendations', all_stocks: 'All Stocks', per_stock: 'Research', comparison: 'Stock Comparison', portfolio: 'Portfolio', trades: 'Trade Journal', mf: 'MF Holdings', lenses: 'Lens Library', watchlist: 'Watchlist' },
        tabulators: {},
        loading: false,
        allStocksRows: [],
        shariaFilterOn: false,
        qualityFilterMinScore: 0,
        qualityLoaded: false,
        qualityLoading: false,
        stockFilterPanelOpen: false,
        stockFilters: {
          exchange: [],
          sector: [],
          // Compliance
          shariaOnly: false,
          // Market & size
          marketCapMin: '', marketCapMax: '',
          // Valuation
          peMin: '', peMax: '',
          forwardPeMin: '', forwardPeMax: '',
          pegMin: '', pegMax: '',
          pbMin: '', pbMax: '',
          evEbitdaMin: '', evEbitdaMax: '',
          psMin: '', psMax: '',
          divYieldMin: '', divYieldMax: '',
          // Profitability
          roeMin: '', roeMax: '',
          roaMin: '', roaMax: '',
          roceMin: '', roceMax: '',
          netMarginMin: '', netMarginMax: '',
          opMarginMin: '', opMarginMax: '',
          grossMarginMin: '', grossMarginMax: '',
          // Growth
          revGrowthMin: '', revGrowthMax: '',
          earnGrowthMin: '', earnGrowthMax: '',
          // Financial health
          debtEquityMin: '', debtEquityMax: '',
          currentRatioMin: '', currentRatioMax: '',
          quickRatioMin: '', quickRatioMax: '',
          intCovMin: '', intCovMax: '',
          // Price & momentum
          betaMin: '', betaMax: '',
          vs200dmaMin: '', vs200dmaMax: '',
          // Sharia ratios
          cashPctMax: '', recPctMax: '', otherRevPctMax: '',
          // Legacy
          qualityMin: '',
          revenueMin: '', revenueMax: '',
          marginMin: '', marginMax: '',
          debtEquityMin: '', debtEquityMax: '',
          peMin: '', peMax: '',
          pegMin: '', pegMax: '',
          roeMin: '', roeMax: '',
        },
        perStockQuality: null,
        perStockQualityLoading: false,
        perStockSymbol: '',
        perStockRow: null,
        perStockPeriodRows: [],
        perStockTab: 'overview',
        perStockTabs: ['overview', 'market', 'thesis', 'financials', 'valuation', 'industry', 'business', 'management', 'esg', 'ma', 'value', 'faq', 'credit', 'estimates', 'revenue', 'geofx', 'capital', 'forensic', 'iprd', 'supply_chain', 'catalysts', 'cyclical'],
        perStockTabLabels: { overview: 'Overview', market: 'Market', thesis: 'Thesis', financials: 'Financials', valuation: 'Valuation', industry: 'Industry', business: 'Business', management: 'Management', esg: 'ESG', ma: 'M&A', value: 'Value', faq: 'FAQ', credit: 'Credit', estimates: 'Estimates', revenue: 'Revenue', geofx: 'Geo/FX', capital: 'Capital', forensic: 'Forensic', iprd: 'IP & R&D', supply_chain: 'Supply Chain', catalysts: 'Catalysts', cyclical: 'Cyclicality' },
        perStockSectionData: {},
        perStockSectionLoading: {},
        metricsHistory: null,
        metricsHistoryLoading: false,
        priceHistory: null,
        priceHistoryLoading: false,
        _chartInstances: {},
        yfSections: ['overview', 'market', 'financials', 'valuation'],
        researchSections: ['thesis', 'industry', 'business', 'management', 'esg', 'estimates', 'revenue', 'catalysts', 'cyclical'],
        researchAISections: ['thesis', 'industry', 'business', 'management', 'esg', 'estimates', 'revenue', 'catalysts', 'cyclical'],
        moreAISections: ['ma', 'value', 'faq', 'credit', 'geofx', 'capital', 'forensic', 'iprd', 'supply_chain'],
        researchSectionLabels: { thesis: 'Thesis', industry: 'Industry', business: 'Business', management: 'Management', esg: 'ESG', estimates: 'Estimates', revenue: 'Revenue', catalysts: 'Catalysts', cyclical: 'Cyclicality', ma: 'M&A', value: 'Value', faq: 'FAQ', credit: 'Credit', geofx: 'Geo/FX', capital: 'Capital', forensic: 'Forensic', iprd: 'IP & R&D', supply_chain: 'Supply Chain' },
        researchModalOpen: false,
        researchModalSelected: [],
        researchRunBannerVisible: false,
        researchRunSections: [],
        researchRunSymbol: '',
        compareSymbolsText: '',
        compareSymbolsList: [],
        compareRows: [],
        compareSymbols: [],
        portfolioPivot: [],
        portfolioRows: [],
        portfolioRowsBySymbol: {},
        portfolioMissing: [],
        portfolioOptions: { symbols: [], labels: {} },
        symbolPickerState: {
          home: { query: '', open: false },
          per_stock: { query: '', open: false },
          comparison: { query: '', open: false },
          compareA: { query: '', open: false },
          compareB: { query: '', open: false },
          compareAdd: { query: '', open: false },
          portfolio: { query: '', open: false },
          personal_index: { query: '', open: false }
        },
        personalIndexHoldingsText: 'TCS 10\nINFY 8\nHCLTECH 6',
        personalIndexInputRows: [],
        holdingDraftUnits: 1,
        holdingDraftAvgPrice: '',
        holdingDraftMarket: 'IN',
        portfolioMarketFilter: 'all',
        holdingMarkets: {},
        portfolioInvestedSince: '',
        performanceData: null,
        performanceLoading: false,
        performanceError: '',
        _nonShariaCache: [],
        // Metric explainer popover
        learningMode: false,
        explainer: { open: false, pinned: false, key: null, x: 0, y: 0 },
        // Research version history state
        researchVersions: {},        // {symbol_section: [{idx, updated_at}]}
        researchVersionOpen: null,   // "SYMBOL_section" key of open dropdown
        // Purification Calculator state
        purificationMode: 'dividends',
        purificationSymbol: '',
        purificationNonHalalPct: null,
        purificationNonHalalOverride: '',
        purificationDividends: '',
        purificationBuyPrice: '',
        purificationSellPrice: '',
        purificationUnits: '',
        purificationLoading: false,
        purificationSharia: null,
        // Trade Journal state
        trades: [],
        tradesLoading: false,
        tradePositions: [],
        tradePnl: { realized_trades: [], total_realized_pnl: 0 },
        tradeFilter: 'all',        // 'all' | 'BUY' | 'SELL' | 'planned' | 'executed'
        tradeFormOpen: false,
        tradeFormMode: 'new',      // 'new' | 'edit'
        tradeEditId: null,
        tradeCheckRunning: false,
        tradeCheckResult: null,
        tradeCheckError: '',
        portfolioPricesLoading: false,
        // MF Holdings state
        mfHoldings: [],
        mfSummary: {},
        mfAsOfDate: '',
        mfImportedAt: '',
        mfLoading: false,
        mfImportRunning: false,
        mfUploadRunning: false,
        mfError: '',
        // Broker import state
        importModalOpen: false,
        importLoading: false,
        importRunning: false,
        importRows: [],
        importError: null,
        importResult: null,
        importHideExisting: true,
        _importUploadFile: null,
        tradeForm: {
          symbol: '', action: 'BUY', units: '', price: '',
          currency: 'INR', date: '', status: 'executed',
          conviction: 'medium', reasoning: '',
          risks_acknowledged: '', emotion_check: 'patient',
          exit_target: '', exit_stop: '', exit_horizon: '', exit_trigger: '',
          thesis_section: '',
        },
        // Lens Library state
        scorecardData: null,
        scorecardLoading: false,
        scorecardSymbol: '',
        lensCompositeLenses: [],
        lensThematics: [],
        lensIdeas: [],
        lensCustom: [],
        lensOpenMap: {},              // tracks expanded state per lens/idea id
        lensActiveTab: 'composite',   // composite | thematic | ideas | custom
        lensFormOpen: false,
        lensFormType: null,           // type of form open
        lensForm: {},
        lensIdeaFilter: 'all',
        lensCustomFields: [],
                usdInrRate: null,
        usdInrUpdated: '',
        personalIndexHoldingsRows: [],
        policyAnalysis: null,
        policyAnalysisLoading: false,
        policyAnalysisError: '',
        deploymentScenariosData: [],
        deploymentScenariosLoading: false,
        policyGapExpanded: {},
        prescriptionSelected: [],
        togglePrescriptionSelect(sym) {
          const idx = this.prescriptionSelected.indexOf(sym);
          if (idx === -1) {
            if (this.prescriptionSelected.length < 5) this.prescriptionSelected = [...this.prescriptionSelected, sym];
          } else {
            this.prescriptionSelected = this.prescriptionSelected.filter(s => s !== sym);
          }
        },
        goCompareSelected() {
          if (this.prescriptionSelected.length < 2) return;
          this.compareSymbols = [...this.prescriptionSelected];
          this.prescriptionSelected = [];
          this.fetchCompare();
          this.go('comparison');
        },
        watchlistText: '',
        watchlistRows: [],
        tableColumns: {},
        columnModalTable: null,
        tableSearchQuery: '',
        symbolsMissing: { symbols: [], total_missing: 0 },
        computeN: 50,
        computeWorkers: 5,
        computeRunning: false,
        computeMessage: '',
        computeError: false,
        cacheStatus: null,
        cacheStatusDismissed: false,
        darkMode: false,

        toggleDarkMode() {
          this.darkMode = !this.darkMode;
          document.documentElement.classList.toggle('dark', this.darkMode);
          localStorage.setItem('darkMode', this.darkMode ? '1' : '0');
        },

        async init() {
          const saved = localStorage.getItem('darkMode');
          this.darkMode = saved ? saved === '1' : window.matchMedia('(prefers-color-scheme: dark)').matches;
          document.documentElement.classList.toggle('dark', this.darkMode);
          const hash = (location.hash || '#home').slice(1);
          if (hash === 'sharia') { location.hash = 'all_stocks'; this.page = 'all_stocks'; }
          else this.page = hash in this.navCards ? hash : 'home';
          window.addEventListener('hashchange', () => {
            const h = (location.hash || '#home').slice(1);
            if (h === 'sharia') { location.hash = 'all_stocks'; this.page = 'all_stocks'; }
            else this.page = h in this.navCards ? h : 'home';
            this.onPageChange();
          });
          await this.fetchSettings();
          await this.fetchReportPeriods();
          await this.fetchUniverse();
          await this.fetchSymbolOptions();
          await this.fetchCounts();
          await this.fetchSymbolsMissing();
          await this.fetchCacheStatus();
          // Restore stockFilters from localStorage (merge so new keys keep defaults)
          const savedFilters = this.lsGetJSON('stockFilters', null);
          if (savedFilters) this.stockFilters = { ...this.stockFilters, ...savedFilters };
          // Persist stockFilters whenever they change
          this.$watch('stockFilters', v => this.lsSetJSON('stockFilters', v), { deep: true });
          this.onPageChange();
        },
        async fetchSettings() {
          try {
            const r = await fetch(API + '/settings').then(x => x.json());
            if (r.period) this.period = r.period;
            if (r.market) this.market = r.market;
            if (r.portfolioSymbolsText != null) {
              this.portfolioSymbolsText = r.portfolioSymbolsText;
            }
            if (r.compareSymbolsText != null) {
              this.compareSymbolsText = r.compareSymbolsText;
              this.compareSymbolsList = this.parseSymbolsText(r.compareSymbolsText).slice(0, 10);
            }
            if (r.watchlistText != null) this.watchlistText = r.watchlistText;
            if (r.personalIndexHoldingsText != null) this.personalIndexHoldingsText = r.personalIndexHoldingsText;
            if (r.holdingMarkets != null) this.holdingMarkets = r.holdingMarkets;
            if (r.portfolioInvestedSince != null) this.portfolioInvestedSince = r.portfolioInvestedSince;
            if (r.tableColumns && Object.keys(r.tableColumns).length) this.tableColumns = r.tableColumns;
            else if (r.shariaVisibleColumns && Object.keys(r.shariaVisibleColumns).length) this.tableColumns = { all_stocks: r.shariaVisibleColumns };
            if (r.computeN != null) this.computeN = r.computeN;
            if (r.computeWorkers != null) this.computeWorkers = r.computeWorkers;
          } catch (_) {}
          this.syncPersonalIndexRowsFromText();
        },
        async saveSettings() {
          try {
            await fetch(API + '/settings', {
              method: 'PUT',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                tableColumns: this.tableColumns,
                period: this.period,
                market: this.market,
                compareSymbolsText: this.compareSymbolsText,
                watchlistText: this.watchlistText,
                personalIndexHoldingsText: this.personalIndexHoldingsText,
                holdingMarkets: this.holdingMarkets,
                portfolioInvestedSince: this.portfolioInvestedSince,
                computeN: this.computeN,
                computeWorkers: this.computeWorkers
              })
            });
          } catch (_) {}
        },
        go(id) { location.hash = id; this.page = id; this.onPageChange(); },
        destroyTabulator(key) {
          if (this.tabulators[key]) { this.tabulators[key].destroy(); delete this.tabulators[key]; }
        },
        destroyAllTabulators() {
          Object.keys(this.tabulators).forEach(k => this.destroyTabulator(k));
        },
        buildColumns(data, opts = {}) {
          if (!data || !data[0]) return [];
          const { visibleColumns = null, minWidth = 100, columnOrder = null } = opts;
          const numericFields = ['total_assets', 'cash_and_short_term_investments', 'total_receivables', 'other_revenue', 'total_revenue', 'debt_to_equity_ratio', 'cash_to_assets_pct', 'other_revenue_to_revenue_pct', 'receivables_to_assets_pct', 'market_cap', 'units', 'price_override', 'current_price', 'value', 'current_weight', 'benchmark_target_weight', 'weight_gap', 'allocation_share', 'invest_amount', 'suggested_units', 'vs200DMA', 'total_score', 'profitability_score', 'cash_generation_score', 'financial_strength_score', 'valuation_score', 'peg_ratio', 'roe', 'operating_margin', 'gross_margin', 'fcf_conversion', 'debt_to_equity', 'current_ratio', 'trailing_pe', 'forward_pe'];
          let fields = columnOrder || Object.keys(data[0]);
          if (visibleColumns) fields = fields.filter(f => visibleColumns[f] !== false);
          return fields.map(field => {
            const sample = data[0][field];
            const isNum = numericFields.includes(field) || (typeof sample === 'number' && !isNaN(sample));
            return {
              title: field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
              field,
              minWidth,
              sorter: isNum ? 'number' : 'string',
              headerFilter: false,
              formatter: isNum ? (cell) => { const v = cell.getValue(); if (v == null || v === '') return '—'; return typeof v === 'number' ? v.toLocaleString(undefined, { maximumFractionDigits: 2 }) : v; } : undefined
            };
          });
        },
        initTable(key, elId, data, opts = {}) {
          this.destroyTabulator(key);
          const el = document.getElementById(elId);
          if (!el || !data || !data.length) return;
          const { visibleColumns = null, minWidth = 120, columnOrder = null } = opts;
          const columns = this.buildColumns(data, { visibleColumns, minWidth, columnOrder });
          const tab = new Tabulator(el, {
            data,
            columns,
            layout: 'fitColumns',
            pagination: true,
            paginationSize: 25,
            paginationSizeSelector: [10, 25, 50, 100, 500],
            maxHeight: '500px',
            ...opts
          });
          this.tabulators[key] = tab;
          this.$nextTick(() => this.applyTableSearch());
        },
        applyTableSearch() {
          if (this.page !== 'all_stocks') return;
          const tab = this.tabulators.all_stocks;
          if (!tab) return;
          const q = (this.tableSearchQuery || '').toLowerCase().trim();
          const f = this.stockFilters;
          const shariaOnly = !!this.shariaFilterOn;
          const hasFilter = q || shariaOnly || this.stockFilterActiveCount() > 0;
          if (!hasFilter) { tab.clearFilter(); return; }
          // n = raw number, pct = pct value (stored as 0-1 in quality data, or 0-100 in sharia data)
          const n = v => (v == null || v === '' || isNaN(Number(v))) ? null : Number(v);
          const inRange = (val, min, max) => {
            if (min !== '' && (val == null || val < Number(min))) return false;
            if (max !== '' && (val == null || val > Number(max))) return false;
            return true;
          };
          const inRangePct = (val, min, max) => { // val stored as 0–1
            const v = val != null ? val * 100 : null;
            return inRange(v, min, max);
          };
          tab.setFilter(d => {
            // Compliance & exchange
            if (shariaOnly && (d.Sharia || d.sharia) !== 'Yes') return false;
            if (f.exchange.length && !f.exchange.includes(d.exchange)) return false;
            if (f.sector.length && !f.sector.includes(d.sector)) return false;
            // Market cap (input in ₹ Cr, stored in ₹)
            const mc = n(d.market_cap);
            if (f.marketCapMin !== '' && (mc == null || mc < Number(f.marketCapMin) * 1e7)) return false;
            if (f.marketCapMax !== '' && (mc == null || mc > Number(f.marketCapMax) * 1e7)) return false;
            // Sharia ratios
            if (!inRange(n(d.cash_to_assets_pct), '', f.cashPctMax)) return false;
            if (!inRange(n(d.receivables_to_assets_pct), '', f.recPctMax)) return false;
            if (!inRange(n(d.other_revenue_to_revenue_pct), '', f.otherRevPctMax)) return false;
            // D/E (from sharia or quality)
            const de = n(d.debt_to_equity_ratio ?? d.debt_to_equity);
            if (!inRange(de, f.debtEquityMin, f.debtEquityMax)) return false;
            // Valuation
            if (!inRange(n(d.trailing_pe), f.peMin, f.peMax)) return false;
            if (!inRange(n(d.forward_pe), f.forwardPeMin, f.forwardPeMax)) return false;
            if (!inRange(n(d.peg_ratio), f.pegMin, f.pegMax)) return false;
            if (!inRange(n(d.price_to_book), f.pbMin, f.pbMax)) return false;
            if (!inRange(n(d.ev_to_ebitda), f.evEbitdaMin, f.evEbitdaMax)) return false;
            if (!inRange(n(d.price_to_sales), f.psMin, f.psMax)) return false;
            if (!inRange(n(d.dividend_yield), f.divYieldMin, f.divYieldMax)) return false;
            // Profitability (stored as 0–1, filter in %)
            if (!inRangePct(n(d.roe), f.roeMin, f.roeMax)) return false;
            if (!inRangePct(n(d.roa), f.roaMin, f.roaMax)) return false;
            if (!inRangePct(n(d.roce), f.roceMin, f.roceMax)) return false;
            if (!inRangePct(n(d.net_margin), f.netMarginMin, f.netMarginMax)) return false;
            if (!inRangePct(n(d.operating_margin), f.opMarginMin, f.opMarginMax)) return false;
            if (!inRangePct(n(d.gross_margin), f.grossMarginMin, f.grossMarginMax)) return false;
            // Growth (stored as 0–1, filter in %)
            if (!inRangePct(n(d.revenue_growth), f.revGrowthMin, f.revGrowthMax)) return false;
            if (!inRangePct(n(d.earnings_growth), f.earnGrowthMin, f.earnGrowthMax)) return false;
            // Financial health
            if (!inRange(n(d.current_ratio), f.currentRatioMin, f.currentRatioMax)) return false;
            if (!inRange(n(d.quick_ratio), f.quickRatioMin, f.quickRatioMax)) return false;
            if (!inRange(n(d.interest_coverage), f.intCovMin, f.intCovMax)) return false;
            // Price & momentum
            if (!inRange(n(d.beta), f.betaMin, f.betaMax)) return false;
            if (!inRange(n(d.vs_200dma), f.vs200dmaMin, f.vs200dmaMax)) return false;
            // Text search
            if (q && !Object.values(d).some(v => String(v ?? '').toLowerCase().includes(q))) return false;
            return true;
          });
        },
        stockFilterActiveCount() {
          const f = this.stockFilters;
          const has = (...keys) => keys.some(k => f[k] !== '' && f[k] != null);
          let n = 0;
          if (this.shariaFilterOn) n++;
          if (f.exchange.length) n++;
          if (f.sector.length) n++;
          if (has('marketCapMin','marketCapMax')) n++;
          if (has('peMin','peMax')) n++;
          if (has('forwardPeMin','forwardPeMax')) n++;
          if (has('pegMin','pegMax')) n++;
          if (has('pbMin','pbMax')) n++;
          if (has('evEbitdaMin','evEbitdaMax')) n++;
          if (has('psMin','psMax')) n++;
          if (has('divYieldMin','divYieldMax')) n++;
          if (has('roeMin','roeMax')) n++;
          if (has('roaMin','roaMax')) n++;
          if (has('roceMin','roceMax')) n++;
          if (has('netMarginMin','netMarginMax')) n++;
          if (has('opMarginMin','opMarginMax')) n++;
          if (has('grossMarginMin','grossMarginMax')) n++;
          if (has('revGrowthMin','revGrowthMax')) n++;
          if (has('earnGrowthMin','earnGrowthMax')) n++;
          if (has('debtEquityMin','debtEquityMax')) n++;
          if (has('currentRatioMin','currentRatioMax')) n++;
          if (has('quickRatioMin','quickRatioMax')) n++;
          if (has('intCovMin','intCovMax')) n++;
          if (has('betaMin','betaMax')) n++;
          if (has('vs200dmaMin','vs200dmaMax')) n++;
          if (has('cashPctMax')) n++;
          if (has('recPctMax')) n++;
          if (has('otherRevPctMax')) n++;
          return n;
        },
        clearAllStockFilters() {
          this.shariaFilterOn = false;
          const blank = v => Array.isArray(v) ? [] : '';
          Object.keys(this.stockFilters).forEach(k => { this.stockFilters[k] = blank(this.stockFilters[k]); });
          this.applyTableSearch();
        },
        toggleArrayFilter(key, val) {
          const arr = this.stockFilters[key];
          const idx = arr.indexOf(val);
          if (idx >= 0) arr.splice(idx, 1); else arr.push(val);
        },
        allStocksSectors() {
          const seen = new Set();
          (this.allStocksRows || []).forEach(r => { if (r.sector) seen.add(r.sector); });
          return [...seen].sort();
        },
        async onPageChange() {
          // Destroy only the Tabulator(s) for the page being left, not all of them.
          // Data stays in memory so switching back is instant (no network call).
          const _pageTabs = {
            all_stocks: ['all_stocks'],
            portfolio:  ['portfolio_pivot'],
            watchlist:  ['watchlist'],
          };
          (_pageTabs[this._prevPage] || []).forEach(k => this.destroyTabulator(k));
          // Also destroy per-symbol portfolio tables from previous page
          if (this._prevPage === 'portfolio') {
            Object.keys(this.tabulators).filter(k => k.startsWith('portfolio_sym_')).forEach(k => this.destroyTabulator(k));
          }
          this._prevPage = this.page;

          if (this.page === 'all_stocks') {
            if (this.allStocksRows.length) {
              // Data cached — just re-render the table, no network call
              this.$nextTick(() => this.initTableWithColumns('all_stocks', 'all-stocks-table', this.allStocksRows));
            } else {
              this.fetchAllStocks();
            }
            // Quality scores: load once per session
            this.$nextTick(() => { if (!this.qualityLoaded && !this.qualityLoading) this.fetchQualityScores(); });
          }
          else if (this.page === 'per_stock') {
            // Restore last symbol from session (never auto-pick the first ticker)
            if (!this.perStockSymbol) this.perStockSymbol = this.sessionGet('perStockSymbol') || '';
            // Re-fetch only if symbol changed or not yet loaded
            if (this.perStockSymbol !== this._perStockLoadedSym) {
              this.perStockTab = 'overview';
              this.fetchPerStock();
            } else {
              // Same symbol — restore last tab, re-init periods table from cached data
              const savedTab = this.sessionGet('perStockTab');
              if (savedTab && this.perStockTabs.includes(savedTab)) this.perStockTab = savedTab;
              this.$nextTick(() => {
                if (this.perStockPeriodRows.length) this.initTableWithColumns('per_stock_periods');
                this.fetchSectionDataIfNeeded(this.perStockTab);
              });
            }
          }
          else if (this.page === 'comparison') {
            // Restore from session if not already set
            if (!this.compareSymbols.length) {
              // migrate legacy session keys
              const a = this.sessionGet('compareSymA') || '';
              const b = this.sessionGet('compareSymB') || '';
              if (a && b) this.compareSymbols = [a, b];
              else if (a) this.compareSymbols = [a];
            }
            // Only fetch if no results yet; otherwise re-render charts from cache
            if (this.compareSymbols.length >= 2 && (!this.compareRows || !this.compareRows.length)) {
              this.fetchCompare();
            } else if (this.compareRows && this.compareRows.length >= 2) {
              setTimeout(() => this.renderCmpCharts(), 200);
            }
          }
          else if (this.page === 'portfolio') {
            // Always sync holdings from trade positions on page load
            await this.syncPortfolioFromTrades();
            if (this.portfolioRows.length) {
              // Re-init tables from cached data
              this.$nextTick(() => {
                const pivotColOrder = this.portfolioPivot.length ? Object.keys(this.portfolioPivot[0]) : null;
                if (this.portfolioPivot.length) this.initTable('portfolio_pivot', 'portfolio-pivot-table', this.portfolioPivot, { columnOrder: pivotColOrder });
                const symTableCols = (this.portfolioRows[0] ? Object.keys(this.portfolioRows[0]) : []).filter(k => k !== 'symbol' && k !== 'name');
                for (const [sym, rows] of Object.entries(this.portfolioRowsBySymbol || {})) {
                  const elId = 'portfolio-sym-table-' + sym.replace(/\./g, '-');
                  this.initTable('portfolio_sym_' + sym, elId, rows, { columnOrder: symTableCols, pagination: false });
                }
              });
              this.fetchPortfolioPerformance();
            } else {
              this.fetchPortfolioData(); this.fetchPortfolioPrices();
              this.fetchPortfolioPerformance();
            }
          }
          else if (this.page === 'watchlist') {
            if (this.watchlistRows.length) {
              this.$nextTick(() => this.initTableWithColumns('watchlist'));
            } else if ((this.watchlistText || '').trim()) {
              this.fetchWatchlist();
            }
          }
          else if (this.page === 'trades') {
            this.fetchTrades();
            if (!this.tradePositions.length) this.fetchTradePositions();
          }
          else if (this.page === 'mf') {
            if (!this.mfHoldings.length) this.fetchMfHoldings();
          }
          else if (this.page === 'lenses') {
            this.fetchLensLibrary();
          }
          else if (this.page === 'recommendations') {
            if (!this.personalIndexHoldingsRows.length && (this.personalIndexInputRows || []).length)
              this.fetchPortfolioPrices();
            if (!this.mfHoldings.length) this.fetchMfHoldings();
            if (!this.usdInrRate) this.fetchUsdInrRate();
            if (!this.policyAnalysis && !this.policyAnalysisLoading) this.fetchPolicyAnalysis();
          }
        },

        // ── MF Holdings ──────────────────────────────────────────────────────
        async fetchMfHoldings() {
          this.mfLoading = true; this.mfError = '';
          try {
            const d = await fetch(API + '/mf/holdings').then(r => r.json());
            this.mfHoldings = d.holdings || [];
            this.mfSummary = d.summary || {};
            this.mfAsOfDate = d.as_of_date || '';
            this.mfImportedAt = d.imported_at || '';
          } catch(e) { this.mfError = e.message; }
          finally { this.mfLoading = false; }
        },
        async reimportMf() {
          this.mfImportRunning = true; this.mfError = '';
          try {
            const r = await fetch(API + '/mf/import', { method: 'POST' }).then(r => r.json());
            if (r.error) { this.mfError = r.error; return; }
            await this.fetchMfHoldings();
          } catch(e) { this.mfError = e.message; }
          finally { this.mfImportRunning = false; }
        },
        async handleMfUpload(evt) {
          const file = evt.target.files[0]; if (!file) return;
          this.mfUploadRunning = true; this.mfError = '';
          try {
            const fd = new FormData(); fd.append('file', file);
            const r = await fetch(API + '/mf/upload', { method: 'POST', body: fd }).then(r => r.json());
            if (r.error) { this.mfError = r.error; return; }
            await this.fetchMfHoldings();
          } catch(e) { this.mfError = e.message; }
          finally { this.mfUploadRunning = false; evt.target.value = ''; }
        },
        mfGroupedHoldings() {
          const groups = {};
          for (const h of this.mfHoldings) {
            const key = h.scheme_name;
            if (!groups[key]) groups[key] = { scheme_name: h.scheme_name, amc: h.amc, category: h.category, sub_category: h.sub_category, folios: [] };
            groups[key].folios.push(h);
          }
          return Object.values(groups).map(g => ({
            ...g,
            total_units: g.folios.reduce((s, f) => s + f.units, 0),
            total_invested: g.folios.reduce((s, f) => s + f.invested_value, 0),
            total_current: g.folios.reduce((s, f) => s + f.current_value, 0),
            total_returns: g.folios.reduce((s, f) => s + f.returns, 0),
          }));
        },

        advisorData() {
          return {
            hasPortfolio: (this.personalIndexInputRows || []).length > 0,
            hasPrices: (this.personalIndexHoldingsRows || []).length > 0,
            policyAnalysis: this.policyAnalysis,
            policyAnalysisLoading: this.policyAnalysisLoading,
            policyAnalysisError: this.policyAnalysisError,
            gaps: this.policyAnalysis?.gaps || [],
            candidates: this.policyAnalysis?.candidates || [],
            concentrationFlags: this.policyAnalysis?.concentration_flags || [],
            scenarios: this.deploymentScenariosData || [],
            scenariosLoading: this.deploymentScenariosLoading,
          };
        },

        // ── Lens Library ─────────────────────────────────────────────────────
        async fetchLensLibrary() {
          const [comp, them, ideas, cust, fields] = await Promise.all([
            fetch(API + '/lenses/composite').then(r => r.json()),
            fetch(API + '/lenses/thematic').then(r => r.json()),
            fetch(API + '/lenses/ideas').then(r => r.json()),
            fetch(API + '/lenses/custom').then(r => r.json()),
            fetch(API + '/lenses/custom/fields').then(r => r.json()),
          ]);
          this.lensCompositeLenses = comp.lenses || [];
          this.lensThematics = them.themes || [];
          this.lensIdeas = ideas.ideas || [];
          this.lensCustom = cust.lenses || [];
          this.lensCustomFields = fields.fields || [];
        },
        async fetchScorecard(symbol) {
          if (!symbol) return;
          this.scorecardLoading = true;
          this.scorecardData = null;
          this.scorecardSymbol = symbol;
          try {
            const r = await fetch(API + '/scorecard/' + encodeURIComponent(symbol) + '?market=' + this.market).then(r => r.json());
            this.scorecardData = r;
          } catch(e) { console.error(e); }
          finally { this.scorecardLoading = false; }
        },
        scoreBarWidth(score) {
          return score != null ? Math.round(score) + '%' : '0%';
        },
        scoreColorClass(color) {
          const map = {
            emerald: 'bg-emerald-500', teal: 'bg-teal-500',
            amber: 'bg-amber-500', orange: 'bg-orange-500', red: 'bg-red-500', slate: 'bg-slate-600'
          };
          return map[color] || 'bg-slate-500';
        },
        scoreTextClass(color) {
          const map = {
            emerald: 'text-emerald-400', teal: 'text-teal-400',
            amber: 'text-amber-400', orange: 'text-orange-400', red: 'text-red-400', slate: 'text-slate-400'
          };
          return map[color] || 'text-slate-400';
        },
        dotBar(score) {
          if (score == null) return '○○○○○○○○○○';
          const filled = Math.round(score / 10);
          return '●'.repeat(filled) + '○'.repeat(10 - filled);
        },
        openLensForm(type, existing = null) {
          this.lensFormType = type;
          if (existing) {
            this.lensForm = JSON.parse(JSON.stringify(existing));
            // Normalise symbols array to newline-joined string for textarea
            if (Array.isArray(this.lensForm.symbols)) this.lensForm._symbolsText = this.lensForm.symbols.join('\n');
          } else {
            const defaults = {
              thematic: { name: '', emoji: '🏷️', description: '', source: '', symbols: [], _symbolsText: '', tags: [] },
              ideas: { title: '', hypothesis: '', source: '', source_type: 'article', status: 'raw', symbols: [], _symbolsText: '', notes: '' },
              custom: { name: '', emoji: '🔧', description: '', source: '', expression: '', type: 'filter' },
              composite: { name: '', emoji: '📐', description: '', source: '', components: [], thresholds: [] },
            };
            this.lensForm = defaults[type] || {};
          }
          this.lensFormOpen = true;
        },
        async saveLensForm() {
          const type = this.lensFormType;
          const form = { ...this.lensForm };
          // Convert _symbolsText back to symbols array
          if (form._symbolsText !== undefined) {
            form.symbols = form._symbolsText.split(/[\n,]+/).map(s => s.trim().toUpperCase()).filter(Boolean);
            delete form._symbolsText;
          }
          try {
            await fetch(API + '/lenses/' + type, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(form),
            }).then(r => r.json());
            this.lensFormOpen = false;
            this.fetchLensLibrary();
          } catch(e) { alert('Save failed: ' + e.message); }
        },
        async deleteLens(type, id) {
          if (!confirm('Delete this lens?')) return;
          await fetch(API + '/lenses/' + type + '/' + id, { method: 'DELETE' });
          this.fetchLensLibrary();
        },
        async updateIdeaStatus(id, status) {
          await fetch(API + '/lenses/ideas/' + id, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status }),
          });
          this.fetchLensLibrary();
        },
        ideaStatusColor(s) {
          return { raw: 'text-slate-400', exploring: 'text-amber-400', promoted: 'text-emerald-400', dismissed: 'text-slate-600' }[s] || 'text-slate-400';
        },
        lensIdeasFiltered() {
          if (this.lensIdeaFilter === 'all') return this.lensIdeas;
          return this.lensIdeas.filter(i => i.status === this.lensIdeaFilter);
        },

        // ── Trade Journal ────────────────────────────────────────────────────
        async fetchTrades() {
          this.tradesLoading = true;
          try {
            const r = await fetch(API + '/trades?limit=200').then(r => r.json());
            this.trades = r.trades || [];
          } catch(e) { console.error(e); }
          finally { this.tradesLoading = false; }
        },
        async fetchTradePositions() {
          try {
            const [pos, pnl] = await Promise.all([
              fetch(API + '/trades/positions?market=' + this.market).then(r => r.json()),
              fetch(API + '/trades/pnl').then(r => r.json()),
            ]);
            this.tradePositions = pos.positions || [];
            this.tradePnl = pnl;
          } catch(e) { console.error(e); }
        },
        async runPretradeCheck() {
          const sym = (this.tradeForm.symbol || '').trim().toUpperCase();
          const price = parseFloat(this.tradeForm.price);
          if (!sym || !price) return;
          this.tradeCheckRunning = true;
          this.tradeCheckResult = null;
          this.tradeCheckError = '';
          try {
            const r = await fetch(
              API + '/trades/pretrade-check?symbol=' + encodeURIComponent(sym) +
              '&action=' + encodeURIComponent(this.tradeForm.action) +
              '&price=' + price +
              '&market=' + this.market
            ).then(r => r.json());
            this.tradeCheckResult = r;
            // Auto-fill price vs 200 DMA
            if (r.vs_200dma_pct != null) {
              // visual only — already in result
            }
          } catch(e) {
            this.tradeCheckError = 'Check failed: ' + e.message;
          } finally { this.tradeCheckRunning = false; }
        },
        async submitTrade() {
          const form = this.tradeForm;
          if (!form.symbol || !form.units || !form.price) return;
          const payload = {
            symbol: form.symbol.trim().toUpperCase(),
            action: form.action,
            units: parseFloat(form.units),
            price: parseFloat(form.price),
            currency: form.currency,
            date: form.date || new Date().toISOString().slice(0, 10),
            status: form.status,
            conviction: form.conviction,
            reasoning: form.reasoning,
            thesis_section: form.thesis_section,
            risks_acknowledged: form.risks_acknowledged
              ? form.risks_acknowledged.split('\n').map(s => s.trim()).filter(Boolean)
              : [],
            emotion_check: form.emotion_check,
            exit_plan: {
              target_price: parseFloat(form.exit_target) || null,
              stop_loss: parseFloat(form.exit_stop) || null,
              horizon: form.exit_horizon || null,
              exit_trigger: form.exit_trigger || null,
            },
            pre_trade_check: this.tradeCheckResult || {},
          };
          try {
            const r = await fetch(API + '/trades?market=' + this.market, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload),
            }).then(r => r.json());
            this.trades.unshift(r.trade);
            this.tradeFormOpen = false;
            this.tradeCheckResult = null;
            this.resetTradeForm();
            // Refresh positions
            this.fetchTradePositions();
          } catch(e) { alert('Save failed: ' + e.message); }
        },
        async updateTradeStatus(id, status) {
          await fetch(API + '/trades/' + id, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status }),
          });
          const t = this.trades.find(t => t.id === id);
          if (t) { t.status = status; }
          this.fetchTradePositions();
        },
        async deleteTrade(id) {
          if (!confirm('Delete this trade record?')) return;
          await fetch(API + '/trades/' + id, { method: 'DELETE' });
          this.trades = this.trades.filter(t => t.id !== id);
          this.fetchTradePositions();
        },
        resetTradeForm() {
          this.tradeForm = {
            symbol: '', action: 'BUY', units: '', price: '',
            currency: 'INR', date: '', status: 'executed',
            conviction: 'medium', reasoning: '',
            risks_acknowledged: '', emotion_check: 'patient',
            exit_target: '', exit_stop: '', exit_horizon: '', exit_trigger: '',
            thesis_section: '',
          };
          this.tradeCheckResult = null;
          this.tradeCheckError = '';
          this.tradeEditId = null;
        },
        openTradeForm(prefill = {}) {
          this.resetTradeForm();
          Object.assign(this.tradeForm, prefill);
          this.tradeFormOpen = true;
          this.tradeFormMode = 'new';
        },
        filteredTrades() {
          return this.trades.filter(t => {
            if (this.tradeFilter === 'all') return true;
            if (this.tradeFilter === 'BUY') return t.action === 'BUY';
            if (this.tradeFilter === 'SELL') return ['SELL','PARTIAL_SELL'].includes(t.action);
            if (this.tradeFilter === 'planned') return t.status === 'planned';
            if (this.tradeFilter === 'executed') return t.status === 'executed';
            return true;
          });
        },
        tradeActionColor(action) {
          if (action === 'BUY') return 'text-emerald-400';
          if (action === 'PARTIAL_SELL') return 'text-amber-400';
          return 'text-red-400';
        },
        tradeStatusBadge(status) {
          if (status === 'executed') return 'bg-emerald-900/50 text-emerald-300 border-emerald-700';
          if (status === 'planned') return 'bg-amber-900/50 text-amber-300 border-amber-700';
          return 'bg-slate-700 text-slate-400 border-slate-600';
        },
        emotionEmoji(e) {
          return { fearful: '😰', greedy: '🤑', patient: '🧘', uncertain: '🤔' }[e] || '—';
        },
        convictionColor(c) {
          return { high: 'text-emerald-400', medium: 'text-amber-400', low: 'text-slate-400' }[c] || '';
        },
        // ── Broker import ────────────────────────────────────────────────────
        async openImportModal() {
          this.importModalOpen = true;
          this.importResult = null;
          this._importUploadFile = null;
          if (this.importRows.length === 0) await this.loadImportPreview();
        },
        async loadImportPreview() {
          this.importLoading = true;
          this.importError = null;
          this.importRows = [];
          try {
            const r = await fetch('/api/trades/import/preview');
            const d = await r.json();
            if (d.error) { this.importError = d.error; }
            else { this.importRows = d.rows || []; }
          } catch(e) { this.importError = 'Failed to load preview: ' + e.message; }
          this.importLoading = false;
        },
        importRowsFiltered() {
          if (this.importHideExisting) return this.importRows.filter(r => !r.already_imported);
          return this.importRows;
        },
        async handleImportFile(event) {
          const file = event.target.files[0];
          if (!file) return;
          this._importUploadFile = file;
          this.importLoading = true;
          this.importError = null;
          this.importRows = [];
          this.importResult = null;
          // Preview by uploading then fetching positions isn't direct — we upload in runImport
          // For preview, send to a temp preview endpoint
          const fd = new FormData();
          fd.append('file', file);
          try {
            const r = await fetch('/api/trades/import/upload', { method: 'POST', body: fd });
            const d = await r.json();
            this.importResult = d;
            await this.loadImportPreview(); // reload to show updated state
          } catch(e) { this.importError = 'Upload failed: ' + e.message; }
          this.importLoading = false;
        },
        async runImport() {
          this.importRunning = true;
          this.importError = null;
          try {
            let r, d;
            if (this._importUploadFile) {
              const fd = new FormData();
              fd.append('file', this._importUploadFile);
              r = await fetch('/api/trades/import/upload', { method: 'POST', body: fd });
            } else {
              r = await fetch('/api/trades/import/run', { method: 'POST' });
            }
            d = await r.json();
            this.importResult = d;
            // Refresh preview and trade list
            await this.loadImportPreview();
            await this.fetchTrades();
            await this.fetchTradePositions();
          } catch(e) { this.importError = 'Import failed: ' + e.message; }
          this.importRunning = false;
        },
        checkSignalColor(val, goodHigh, badLow) {
          // goodHigh: higher is better (e.g. quality score)
          if (val == null) return 'text-slate-500';
          if (goodHigh) return val >= badLow ? 'text-emerald-400' : 'text-red-400';
          return val <= badLow ? 'text-emerald-400' : 'text-red-400';
        },
        fmtPct(v, digits = 1) { return v == null || isNaN(v) ? '—' : (Number(v) * 100).toFixed(digits) + '%'; },
        fmtMoney(v) { return v == null || isNaN(v) ? '—' : '₹' + Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 }); },
        // ── Local storage helpers (persists across browser restarts) ────────
        sessionSet(key, val) { try { localStorage.setItem('inv_' + key, val == null ? '' : String(val)); } catch(_) {} },
        sessionGet(key) { try { return localStorage.getItem('inv_' + key) || ''; } catch(_) { return ''; } },
        lsSetJSON(key, val) { try { localStorage.setItem('inv_' + key, JSON.stringify(val)); } catch(_) {} },
        lsGetJSON(key, fallback) { try { const s = localStorage.getItem('inv_' + key); return s ? JSON.parse(s) : fallback; } catch(_) { return fallback; } },
        // Generic number formatter — trims trailing zeros, handles null/NaN/Inf
        fmtNum(v, decimals = 2) {
          if (v == null) return '—';
          const n = Number(v);
          if (!isFinite(n) || isNaN(n)) return '—';
          // For very small numbers that round to 0.00, show more precision
          if (n !== 0 && Math.abs(n) < Math.pow(10, -decimals)) {
            return n.toPrecision(2);
          }
          return n.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: decimals });
        },
        // Format a ratio as-is (like D/E = 0.05x)
        fmtRatio(v, decimals = 2) {
          if (v == null) return '—';
          const n = Number(v);
          if (!isFinite(n) || isNaN(n)) return '—';
          return n.toFixed(decimals) + 'x';
        },
        // Format percentage already in % form (not 0-1 scale)
        fmtPctRaw(v, decimals = 2) {
          if (v == null) return '—';
          const n = Number(v);
          if (!isFinite(n) || isNaN(n)) return '—';
          return n.toFixed(decimals) + '%';
        },
        parseSymbolsText(raw) {
          const seen = new Set();
          return (raw || '')
            .replace(/,/g, '\n')
            .split(/\s+/)
            .map(s => s.trim())
            .filter(Boolean)
            .filter(s => {
              const key = s.toUpperCase();
              if (seen.has(key)) return false;
              seen.add(key);
              return true;
            });
        },
        symbolSearchUniverse() {
          // Use the full universe from /api/universe.
          // Labels (company names) come from portfolioOptions.labels separately.
          return this.tickers || [];
        },
        symbolOptionLabel(sym) {
          return (this.portfolioOptions.labels || {})[sym] || sym;
        },
        symbolOptionSecondaryLabel(sym) {
          const label = this.symbolOptionLabel(sym);
          const prefix = sym + ' — ';
          return label.startsWith(prefix) ? label.slice(prefix.length) : label;
        },
        symbolPickerSelection(key) {
          if (key === 'comparison') return this.compareSymbolsList || [];
          if (key === 'portfolio') return (this.personalIndexInputRows || []).map(r => r.symbol).filter(Boolean);
          if (key === 'personal_index') return (this.personalIndexInputRows || []).map(row => row.symbol).filter(Boolean);
          if (key === 'per_stock') return this.perStockSymbol ? [this.perStockSymbol] : [];
          return [];
        },
        symbolPickerMatches(key) {
          const q = ((this.symbolPickerState[key] || {}).query || '').trim().toLowerCase();
          const selected = new Set(this.symbolPickerSelection(key).map(s => s.toUpperCase()));
          return this.symbolSearchUniverse().filter(sym => {
            if (selected.has(sym.toUpperCase())) return false;
            if (!q) return true;
            const label = this.symbolOptionLabel(sym).toLowerCase();
            return sym.toLowerCase().includes(q) || label.includes(q);
          }).slice(0, 15);
        },
        async resolveSymbolInput(raw) {
          const q = (raw || '').trim();
          if (!q) return '';
          const exact = this.symbolSearchUniverse().find(sym => sym.toUpperCase() === q.toUpperCase());
          if (exact) return exact;
          try {
            const r = await fetch(API + '/resolve?q=' + encodeURIComponent(q) + '&market=' + encodeURIComponent(this.market)).then(r => r.json());
            if (r.ticker) return r.ticker;
          } catch (_) {}
          return q.toUpperCase();
        },
        async openPerStockSymbol(raw, navigate = false) {
          const resolved = await this.resolveSymbolInput(raw);
          if (!resolved) return;
          this.perStockSymbol = resolved;
          this.sessionSet('perStockSymbol', resolved);
          this.perStockTab = 'overview';
          this.metricsHistory = null;
          this.priceHistory = null;
          this.symbolPickerState.home.query = '';
          this.symbolPickerState.home.open = false;
          this.symbolPickerState.per_stock.query = '';
          this.symbolPickerState.per_stock.open = false;
          if (navigate) this.go('per_stock');
          else await this.fetchPerStock();
        },
        async goToStock() {
          await this.symbolPickerCommit('home');
        },
        async symbolPickerCommit(key, explicitSymbol = null) {
          const query = (explicitSymbol || this.symbolPickerMatches(key)[0] || ((this.symbolPickerState[key] || {}).query || '')).trim();
          if (!query) return;
          if (key === 'home') {
            await this.openPerStockSymbol(query, true);
            return;
          }
          if (key === 'per_stock') {
            await this.openPerStockSymbol(query, false);
            return;
          }
          if (key === 'comparison') {
            this.addCompareSymbol(query);
          } else if (key === 'portfolio') {
            // addHoldingRow is async and clears picker state itself — just call it
            await this.addHoldingRow(query);
            return;
          }
          if (this.symbolPickerState[key]) {
            this.symbolPickerState[key].query = '';
            this.symbolPickerState[key].open = false;
          }
        },
        clearPerStockSymbol() {
          this.perStockSymbol = '';
          this.sessionSet('perStockSymbol', '');
          this.perStockRow = null;
          this.perStockPeriodRows = [];
          this.perStockQuality = null;
          this.symbolPickerState.per_stock.query = '';
          this.symbolPickerState.per_stock.open = false;
        },
        openResearchModal() {
          // Default: all Research (AI) sections pre-selected
          this.researchModalSelected = [...this.researchAISections];
          this.researchModalOpen = true;
        },
        selectAllResearch() {
          const extras = this.researchAISections.filter(s => !this.researchModalSelected.includes(s));
          this.researchModalSelected = [...this.researchModalSelected, ...extras];
        },
        deselectAllResearch() {
          this.researchModalSelected = this.researchModalSelected.filter(s => !this.researchAISections.includes(s));
        },
        selectAllMore() {
          const extras = this.moreAISections.filter(s => !this.researchModalSelected.includes(s));
          this.researchModalSelected = [...this.researchModalSelected, ...extras];
        },
        deselectAllMore() {
          this.researchModalSelected = this.researchModalSelected.filter(s => !this.moreAISections.includes(s));
        },
        confirmRunResearch() {
          if (!this.researchModalSelected.length) return;
          const sections = this.researchModalSelected.join(',');
          const cmd = `./cli.py research ${this.perStockSymbol} --sections ${sections}`;
          // Copy command to clipboard and show a toast
          navigator.clipboard.writeText(cmd).catch(() => {});
          this.researchModalOpen = false;
          // Show inline instruction banner
          this.researchRunSections = [...this.researchModalSelected];
          this.researchRunSymbol = this.perStockSymbol;
          this.researchRunBannerVisible = true;
          setTimeout(() => { this.researchRunBannerVisible = false; }, 12000);
        },
        parsePersonalIndexHoldingsText(raw) {
          return (raw || '').split(/\n+/).map(line => {
            const normalized = line.trim().replace(/,/g, ' ').replace(/:/g, ' ');
            const parts = normalized.split(/\s+/).filter(Boolean);
            if (parts.length < 2) return null;
            const symbol = parts[0].trim().toUpperCase();
            const units = Number(parts[1]);
            if (!symbol || !Number.isFinite(units) || units <= 0) return null;
            const price = parts.length >= 3 ? Number(parts[2]) : null;
            return {
              symbol,
              units,
              price: Number.isFinite(price) && price > 0 ? price : '',
              market: (this.holdingMarkets || {})[symbol] || 'IN',
            };
          }).filter(Boolean);
        },
        syncPersonalIndexRowsFromText(raw = this.personalIndexHoldingsText) {
          this.personalIndexInputRows = this.parsePersonalIndexHoldingsText(raw);
        },
        serializePersonalIndexRows(mode = 'units') {
          // mode 'units'      → omit price (backend uses live market price for weighting)
          // mode 'cost_basis' → include avg buy price as price_override (weights by cost basis)
          return (this.personalIndexInputRows || [])
            .map(row => {
              const symbol = (row.symbol || '').trim().toUpperCase();
              const units = Number(row.units);
              if (!symbol || !Number.isFinite(units) || units <= 0) return null;
              const price = row.price === '' || row.price == null ? null : Number(row.price);
              const includePrice = mode === 'cost_basis' && Number.isFinite(price) && price > 0;
              return `${symbol} ${units}${includePrice ? ' ' + price : ''}`;
            })
            .filter(Boolean)
            .join('\n');
        },
        /* --- Portfolio holding computed helpers --- */
        holdingCurrentPrice(sym) {
          const row = (this.personalIndexHoldingsRows || []).find(r => r.symbol === sym);
          return row?.current_price ?? null;
        },
        holdingSharia(sym) {
          const row = (this.personalIndexHoldingsRows || []).find(r => r.symbol === sym);
          return row?.Sharia ?? null;
        },
        holdingCurrentValue(row) {
          const price = this.holdingCurrentPrice(row.symbol);
          if (price == null) return null;
          return row.units * price;
        },
        holdingCostBasis(row) {
          const price = row.price === '' || row.price == null ? null : Number(row.price);
          if (!price || price <= 0) return null;
          return row.units * price;
        },
        holdingPnL(row) {
          const cv = this.holdingCurrentValue(row);
          const cb = this.holdingCostBasis(row);
          if (cv == null || cb == null) return null;
          return cv - cb;
        },
        holdingPnLPct(row) {
          const pnl = this.holdingPnL(row);
          const cb = this.holdingCostBasis(row);
          if (pnl == null || !cb) return '';
          return (pnl / cb * 100).toFixed(1) + '%';
        },
        holdingWeight(row) {
          const total = this.portfolioTotalCurrentValue();
          const cv = this.holdingCurrentValue(row);
          if (!total || cv == null) return '—';
          return (cv / total * 100).toFixed(1) + '%';
        },
        portfolioTotalCurrentValue() {
          return (this.personalIndexInputRows || []).reduce((sum, row) => {
            const v = this.holdingCurrentValue(row);
            return sum + (v ?? 0);
          }, 0);
        },
        portfolioTotalCostBasis() {
          return (this.personalIndexInputRows || []).reduce((sum, row) => {
            const v = this.holdingCostBasis(row);
            return sum + (v ?? 0);
          }, 0);
        },
        portfolioTotalPnL() {
          const tv = this.portfolioTotalCurrentValue();
          const tb = this.portfolioTotalCostBasis();
          if (!tv || !tb) return null;
          return tv - tb;
        },
        /* --- Add holding row from picker --- */
        async addHoldingRow(explicitSymbol = null) {
          const query = (explicitSymbol || this.symbolPickerState.portfolio.query || '').trim();
          if (!query) return;
          const units = Number(this.holdingDraftUnits);
          const price = this.holdingDraftAvgPrice === '' || this.holdingDraftAvgPrice == null ? null : Number(this.holdingDraftAvgPrice);
          if (!Number.isFinite(units) || units <= 0) {
            
            return;
          }
          const symbol = await this.resolveSymbolInput(query);
          if (!symbol) return;
          const market = this.holdingDraftMarket || 'IN';
          this.holdingMarkets = { ...this.holdingMarkets, [symbol]: market };
          const existing = this.personalIndexInputRows.findIndex(r => (r.symbol || '').toUpperCase() === symbol.toUpperCase());
          if (existing >= 0) {
            this.personalIndexInputRows[existing].units = Number(this.personalIndexInputRows[existing].units || 0) + units;
            if (Number.isFinite(price) && price > 0) this.personalIndexInputRows[existing].price = price;
            this.personalIndexInputRows[existing].market = market;
            this.personalIndexInputRows = [...this.personalIndexInputRows];
          } else {
            this.personalIndexInputRows = [
              ...this.personalIndexInputRows,
              { symbol, units, price: Number.isFinite(price) && price > 0 ? price : '', market }
            ];
          }
          this.holdingDraftUnits = 1;
          this.holdingDraftAvgPrice = '';
          this.symbolPickerState.portfolio.query = '';
          this.symbolPickerState.portfolio.open = false;
          
          this.syncPersonalIndexTextFromRows(true);
          this.fetchPortfolioData(); this.fetchPortfolioPrices();
        },
        filteredHoldingRows() {
          if (this.portfolioMarketFilter === 'all') return this.personalIndexInputRows;
          return this.personalIndexInputRows.filter(r => (r.market || 'IN') === this.portfolioMarketFilter);
        },
        portfolioINCount() {
          return this.personalIndexInputRows.filter(r => !r.market || r.market === 'IN').length;
        },
        portfolioUSCount() {
          return this.personalIndexInputRows.filter(r => r.market === 'US').length;
        },
        portfolioTotalCurrentValueByMarket(market) {
          return (this.personalIndexInputRows || [])
            .filter(r => (r.market || 'IN') === market)
            .reduce((sum, row) => {
              const val = this.holdingCurrentValue(row);
              return val != null ? sum + val : sum;
            }, 0);
        },
        // ---- Portfolio Analytics helpers ----
        _latestPortfolioRowBySymbol() {
          // One row per symbol — latest period from portfolioRows
          const map = {};
          for (const row of (this.portfolioRows || [])) {
            if (!map[row.symbol] || (row.report_period > map[row.symbol].report_period)) {
              map[row.symbol] = row;
            }
          }
          return map;
        },
        holdingUnits(symbol) {
          const r = (this.personalIndexInputRows || []).find(r => r.symbol === symbol);
          return r ? r.units : 0;
        },
        holdingAvgPrice(symbol) {
          const r = (this.personalIndexInputRows || []).find(r => r.symbol === symbol);
          return r ? r.price : '';
        },
        capTierBreakdown() {
          const rows = this._latestPortfolioRowBySymbol();
          const tiers = { 'Large Cap': 0, 'Mid Cap': 0, 'Small Cap': 0, 'Unknown': 0 };
          const counts = { 'Large Cap': 0, 'Mid Cap': 0, 'Small Cap': 0, 'Unknown': 0 };
          for (const row of (this.personalIndexInputRows || [])) {
            const meta = rows[row.symbol] || {};
            const mc = meta.market_cap;
            let tier = 'Unknown';
            if (mc) {
              // INR: Large >200B, Mid 50-200B, Small <50B (₹20,000Cr / ₹5,000Cr thresholds)
              if (mc > 200_000_000_000) tier = 'Large Cap';
              else if (mc > 50_000_000_000) tier = 'Mid Cap';
              else tier = 'Small Cap';
            }
            const val = this.holdingCurrentValue(row) || 0;
            tiers[tier] += val;
            counts[tier]++;
          }
          const total = Object.values(tiers).reduce((a, b) => a + b, 0) || 1;
          return Object.entries(tiers)
            .filter(([, v]) => v > 0 || counts[k => k] > 0)
            .map(([label, val]) => ({ label, pct: Math.round(val / total * 100), count: counts[label] }))
            .filter(t => t.count > 0);
        },
        sectorBreakdown() {
          const rows = this._latestPortfolioRowBySymbol();
          const map = {};
          for (const row of (this.personalIndexInputRows || [])) {
            const meta = rows[row.symbol] || {};
            const sector = meta.sector || 'Unknown';
            map[sector] = (map[sector] || 0) + (this.holdingCurrentValue(row) || 0);
          }
          const total = Object.values(map).reduce((a, b) => a + b, 0) || 1;
          return Object.entries(map)
            .map(([sector, val]) => ({ sector, pct: Math.round(val / total * 100) }))
            .sort((a, b) => b.pct - a.pct);
        },
        shariaBreakdown() {
          const rows = this._latestPortfolioRowBySymbol();
          const map = { 'Compliant': 0, 'Non-Compliant': 0, 'Unknown': 0 };
          const counts = { 'Compliant': 0, 'Non-Compliant': 0, 'Unknown': 0 };
          for (const row of (this.personalIndexInputRows || [])) {
            const meta = rows[row.symbol] || {};
            const s = meta.Sharia === 'Yes' ? 'Compliant' : meta.Sharia === 'No' ? 'Non-Compliant' : 'Unknown';
            map[s] += this.holdingCurrentValue(row) || 0;
            counts[s]++;
          }
          const total = Object.values(map).reduce((a, b) => a + b, 0) || 1;
          return Object.entries(map)
            .map(([label, val]) => ({ label, pct: Math.round(val / total * 100), count: counts[label] }))
            .filter(t => t.count > 0);
        },
        topHoldingsByWeight() {
          const total = this.portfolioTotalCurrentValue() || 1;
          return (this.personalIndexInputRows || [])
            .map(row => ({ symbol: row.symbol, weight: Math.round((this.holdingCurrentValue(row) || 0) / total * 1000) / 10 }))
            .filter(r => r.weight > 0)
            .sort((a, b) => b.weight - a.weight)
            .slice(0, 8);
        },
        portfolioConcentrationWarning() {
          const top = this.topHoldingsByWeight();
          if (!top.length) return null;
          const over = top.filter(h => h.weight > 8);
          if (over.length) return `⚠️ ${over.map(h => h.symbol.replace('.NS','') + ' (' + h.weight + '%)').join(', ')} exceed the 8% single-stock limit.`;
          const sectorBreak = this.sectorBreakdown().filter(s => s.pct > 15);
          if (sectorBreak.length) return `⚠️ ${sectorBreak.map(s => s.sector + ' (' + s.pct + '%)').join(', ')} exceed the 15% sector limit.`;
          return null;
        },
        diversificationScore() {
          const n = (this.personalIndexInputRows || []).length;
          const sectors = new Set((this.sectorBreakdown() || []).map(s => s.sector)).size;
          const top = this.topHoldingsByWeight()[0]?.weight || 100;
          let score = 0;
          if (n >= 15) score += 3; else if (n >= 10) score += 2; else if (n >= 5) score += 1;
          if (sectors >= 8) score += 3; else if (sectors >= 5) score += 2; else if (sectors >= 3) score += 1;
          if (top <= 8) score += 2; else if (top <= 12) score += 1;
          const sharia = this.shariaBreakdown().find(s => s.label === 'Compliant');
          if (sharia && sharia.pct >= 80) score += 2; else if (sharia && sharia.pct >= 50) score += 1;
          return Math.min(score, 10);
        },
        diversificationLabel() {
          const s = this.diversificationScore();
          if (s >= 8) return 'Well diversified';
          if (s >= 5) return 'Moderately diversified — room to improve';
          return 'Concentrated — consider spreading across more sectors';
        },
        nonShariaHoldings() {
          const rows = this._latestPortfolioRowBySymbol();
          return (this.personalIndexInputRows || [])
            .filter(row => { const m = rows[row.symbol] || {}; return m.Sharia === 'No'; })
            .map(row => {
              const meta = rows[row.symbol] || {};
              // Re-use cached state if already loaded
              const existing = (this._nonShariaCache || []).find(c => c.symbol === row.symbol);
              if (existing) return existing;
              const obj = { symbol: row.symbol, name: meta.name || row.symbol, sector: meta.sector || null, industry: meta.industry || null, _loaded: false, _loading: false, _replacements: [] };
              this._nonShariaCache = [...(this._nonShariaCache || []), obj];
              return obj;
            });
        },
        async loadReplacements(holding) {
          holding._loading = true;
          try {
            const r = await fetch(API + '/portfolio/replacements', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                symbol: holding.symbol,
                sector: holding.sector,
                industry: holding.industry,
                exclude_symbols: (this.personalIndexInputRows || []).map(r => r.symbol),
                market: this.market === 'us' ? 'us' : 'india',
                top_n: 5,
              })
            }).then(r => r.json());
            holding._replacements = r.replacements || [];
          } catch (_) { holding._replacements = []; }
          holding._loaded = true;
          holding._loading = false;
          // Force Alpine reactivity
          this.personalIndexInputRows = [...this.personalIndexInputRows];
        },
        beforeAfterRows() {
          const metaMap = this._latestPortfolioRowBySymbol();
          const total = this.portfolioTotalCurrentValue() || 1;
          const sectorCount = {};
          // Count sector usage
          for (const row of (this.personalIndexInputRows || [])) {
            const m = metaMap[row.symbol] || {};
            const s = m.sector || 'Unknown';
            sectorCount[s] = (sectorCount[s] || 0) + 1;
          }
          return (this.personalIndexInputRows || []).map(row => {
            const m = metaMap[row.symbol] || {};
            const weight = Math.round((this.holdingCurrentValue(row) || 0) / total * 1000) / 10;
            const mc = m.market_cap;
            let capTier = 'Unknown';
            if (mc > 200_000_000_000) capTier = 'Large Cap';
            else if (mc > 50_000_000_000) capTier = 'Mid Cap';
            else if (mc) capTier = 'Small Cap';
            const sharia = m.Sharia || '?';
            let action = 'Hold';
            let recommendation = 'Maintain current position.';
            if (sharia === 'No') {
              action = 'Replace';
              recommendation = 'Non-Sharia. Sell and redeploy into a compliant alternative in the same sector — see Replacement Suggestions above.';
            } else if (weight > 12) {
              action = 'Trim';
              recommendation = `Overweight at ${weight}% — target ≤8%. Trim ~₹${Math.round((weight - 8) / 100 * total / 1000)}K and redeploy into underweight sectors.`;
            } else if (weight > 8) {
              action = 'Trim';
              recommendation = `Above 8% single-stock limit. Monitor closely; trim on next rebalance.`;
            } else if (weight < 3 && (this.personalIndexInputRows || []).length > 12) {
              action = 'Add';
              recommendation = 'Underweight. Add on dips to bring towards 5–7% target weight.';
            }
            return { symbol: row.symbol, sector: m.sector || '—', weight, capTier, sharia, action, recommendation };
          }).sort((a, b) => b.weight - a.weight);
        },
        _getBestReplacement(symbol) {
          const cached = (this._nonShariaCache || []).find(c => c.symbol === symbol);
          if (cached && cached._replacements && cached._replacements.length) {
            // Pick the one not already in portfolio
            const existing = new Set((this.personalIndexInputRows || []).map(r => r.symbol));
            return cached._replacements.find(r => !existing.has(r.symbol)) || cached._replacements[0];
          }
          return null;
        },
        deploymentScenarios() {
          const amounts = [25000, 50000, 75000, 100000];
          const labels  = ['₹25,000', '₹50,000', '₹75,000', '₹1,00,000'];
          const meta    = this._latestPortfolioRowBySymbol();
          const currentTotal = this.portfolioTotalCurrentValue() || 0;
          const n = (this.personalIndexInputRows || []).length;
          const targetWeightPct = Math.min(8, 100 / Math.max(n, 12)); // target ~equal weight, max 8%

          // Identify non-Sharia sells (same for all scenarios)
          const sells = [];
          let saleProceeds = 0;
          for (const row of (this.personalIndexInputRows || [])) {
            const m = meta[row.symbol] || {};
            if (m.Sharia === 'No') {
              const val = this.holdingCurrentValue(row) || 0;
              sells.push({ symbol: row.symbol, amount: val, replacement: this._getBestReplacement(row.symbol) });
              saleProceeds += val;
            }
          }

          // Top compliant pick per gap from prescription (HIGH PRIORITY first)
          const gapCandidates = [];
          const candidatePriceMap = {}; // symbol → unit price
          if (this.policyAnalysis && this.policyAnalysis.candidates) {
            const sorted = [...this.policyAnalysis.candidates].sort((a, b) =>
              (a.priority === 'high' ? 0 : 1) - (b.priority === 'high' ? 0 : 1)
            );
            for (const gap of sorted) {
              const best = (gap.options || []).find(o => o.sharia_status === 'Yes');
              if (best) {
                gapCandidates.push({ symbol: best.symbol, sector: gap.sector_gap, priority: gap.priority });
                if (best.current_price) candidatePriceMap[best.symbol] = best.current_price;
              }
            }
          }

          return amounts.map((newAmount, idx) => {
            const deployable = newAmount + saleProceeds;
            const newTotal   = currentTotal + newAmount;
            let remaining    = deployable;
            const buys = [];

            // 1. Replace non-Sharia with best replacement (same value as sale proceeds)
            for (const sale of sells) {
              if (remaining <= 0) break;
              const rep = sale.replacement;
              if (!rep) continue;
              const repRow = (this.personalIndexInputRows || []).find(r => r.symbol === rep.symbol);
              const currentVal = repRow ? (this.holdingCurrentValue(repRow) || 0) : 0;
              const currentW = Math.round(currentVal / newTotal * 1000) / 10;
              const buyAmt = Math.min(sale.amount, remaining, newTotal * 0.08 - currentVal);
              const repUnitPrice = this.holdingCurrentPrice(rep.symbol);
              if (repUnitPrice && buyAmt < repUnitPrice) continue;
              if (buyAmt > 500) {
                const newW = Math.round((currentVal + buyAmt) / newTotal * 1000) / 10;
                buys.push({ symbol: rep.symbol, amount: Math.round(buyAmt), reason: `↔ Replace ${sale.symbol.replace('.NS','')}`, currentWeight: currentW, newWeight: newW });
                remaining -= buyAmt;
              }
            }

            // 2. Fill sector gaps using prescription candidates (HIGH PRIORITY first)
            if (remaining > 500) {
              for (const cand of gapCandidates) {
                if (remaining < 500) break;
                if (buys.find(b => b.symbol === cand.symbol)) continue;
                const existingRow = (this.personalIndexInputRows || []).find(r => r.symbol === cand.symbol);
                const currentVal = existingRow ? (this.holdingCurrentValue(existingRow) || 0) : 0;
                const currentW = Math.round(currentVal / newTotal * 1000) / 10;
                if (currentW >= 8) continue; // already at cap
                // Allocate proportional slice — gap fills split remaining equally
                const sliceAmt = Math.round(Math.min(remaining / Math.max(gapCandidates.length, 1), newTotal * 0.08 - currentVal, remaining));
                // Skip if we can't afford even one unit
                const unitPrice = candidatePriceMap[cand.symbol] || this.holdingCurrentPrice(cand.symbol);
                if (unitPrice && sliceAmt < unitPrice) continue;
                if (sliceAmt > 500) {
                  const newW = Math.round((currentVal + sliceAmt) / newTotal * 1000) / 10;
                  const label = cand.priority === 'high' ? `🎯 Gap fill — ${cand.sector}` : `↗ Gap fill — ${cand.sector}`;
                  buys.push({ symbol: cand.symbol.replace('.NS','').replace('.BO',''), amount: sliceAmt, reason: label, currentWeight: currentW, newWeight: newW });
                  remaining -= sliceAmt;
                }
              }
            }

            // 3. Top up underweight compliant existing holdings
            if (remaining > 500) {
              const compliant = (this.personalIndexInputRows || [])
                .filter(row => (meta[row.symbol] || {}).Sharia === 'Yes')
                .map(row => {
                  const val = this.holdingCurrentValue(row) || 0;
                  return { symbol: row.symbol, currentVal: val, currentWeight: Math.round(val / newTotal * 1000) / 10 };
                })
                .filter(h => !buys.find(b => b.symbol === h.symbol))
                .sort((a, b) => a.currentWeight - b.currentWeight);

              for (const h of compliant) {
                if (remaining < 500) break;
                if (h.currentWeight >= targetWeightPct) continue;
                const deficit = (targetWeightPct - h.currentWeight) / 100 * newTotal;
                const buyAmt = Math.round(Math.min(deficit, remaining, newTotal * 0.08 - h.currentVal));
                const hUnitPrice = this.holdingCurrentPrice(h.symbol);
                if (hUnitPrice && buyAmt < hUnitPrice) continue;
                if (buyAmt > 500) {
                  const newW = Math.round((h.currentVal + buyAmt) / newTotal * 1000) / 10;
                  buys.push({ symbol: h.symbol, amount: buyAmt, reason: `↑ Underweight (${h.currentWeight}%)`, currentWeight: h.currentWeight, newWeight: newW });
                  remaining -= buyAmt;
                }
              }
            }

            // 4. Any leftover: most underweight compliant existing holding
            if (remaining > 500) {
              const compliant = (this.personalIndexInputRows || [])
                .filter(row => (meta[row.symbol] || {}).Sharia === 'Yes' && !buys.find(b => b.symbol === row.symbol))
                .map(row => {
                  const val = this.holdingCurrentValue(row) || 0;
                  return { symbol: row.symbol, currentVal: val, currentWeight: Math.round(val / newTotal * 1000) / 10 };
                })
                .sort((a, b) => a.currentWeight - b.currentWeight);
              if (compliant.length) {
                const h = compliant[0];
                const newW = Math.round((h.currentVal + remaining) / newTotal * 1000) / 10;
                buys.push({ symbol: h.symbol, amount: Math.round(remaining), reason: `↑ Best underweight`, currentWeight: h.currentWeight, newWeight: newW });
                remaining = 0;
              }
            }

            return { idx, label: labels[idx], newAmount, deployable: Math.round(deployable), newTotal: Math.round(newTotal), sells, buys };
          });
        },
        // ---- Metric Explainer ----
        METRIC_EXPLAINERS: {
          // Market
          'current_price':      { title: 'Current Price', body: 'The latest traded price of the stock on the exchange. By itself it tells you nothing about value — a ₹10 stock can be more expensive than a ₹5,000 one if earnings are much lower.', good: null },
          '52w_high':           { title: '52-Week High', body: 'The highest price the stock reached over the past 52 weeks. If the stock is trading near its 52W high it shows strong momentum; far below it may indicate a beaten-down company or a bargain — context matters.', good: 'Context-dependent' },
          '52w_low':            { title: '52-Week Low', body: 'The lowest price in the past year. Trading near a 52W low can mean distress or a deep-value opportunity. Always pair with fundamentals before concluding.', good: 'Context-dependent' },
          'beta':               { title: 'Beta', body: 'Measures how much the stock moves relative to the overall market. Beta 1 = moves with the market. Beta 1.5 = 50% more volatile. Beta 0.5 = half as volatile. Defensive investors prefer β < 1; growth investors may tolerate higher.', good: 'Defensive: < 0.8 | Balanced: 0.8–1.2' },
          'dividend_yield':     { title: 'Dividend Yield', body: 'Annual dividend paid as a % of the current stock price. A 3% yield means you earn ₹3 per year for every ₹100 invested. Higher yield is nice, but unsustainably high yield (>8-10%) can be a warning — check if the company can afford it.', good: 'Sustainable: 1–5%' },
          'vs_200dma':          { title: 'VS 200 DMA', body: 'How far the current price is above or below the 200-day moving average. Trading above +20% may signal overbought conditions; trading below −20% may indicate oversold. Widely used by institutional investors as a trend filter.', good: '−10% to +15% = normal range' },
          'market_cap':         { title: 'Market Capitalisation', body: 'Total market value of all outstanding shares (Price × Shares). In India: Large Cap > ₹20,000 Cr, Mid Cap ₹5,000–20,000 Cr, Small Cap < ₹5,000 Cr. Larger companies are generally more stable; smaller ones offer higher growth potential with more risk.', good: 'Depends on your risk tolerance' },
          // Valuation
          'trailing_pe':        { title: 'P/E Ratio (Trailing)', body: 'Price divided by the last 12 months of actual earnings per share. The most common valuation metric. A P/E of 20 means you\'re paying ₹20 for every ₹1 of earnings. Compare within the same sector — a 30x P/E might be cheap for a fast-growing tech company but expensive for a utility.', good: 'India avg ~20–25x | Lower is cheaper, but growth commands a premium' },
          'forward_pe':         { title: 'P/E Ratio (Forward)', body: 'Price divided by next 12 months\' estimated earnings. If forward P/E is significantly lower than trailing P/E, analysts expect earnings to grow — a positive sign. Relies on analyst forecasts so treat with some scepticism.', good: 'Lower than trailing P/E = earnings growth expected' },
          'price_to_book':      { title: 'Price to Book (P/B)', body: 'Price divided by book value per share (assets minus liabilities). P/B < 1 means the market values the company below its net assets — often a value signal but can also mean the assets are overvalued or the business is declining. Best used for asset-heavy sectors like banks and real estate.', good: 'Value: < 1.5x | Growth: 2–5x is normal' },
          'ev_to_ebitda':       { title: 'EV / EBITDA', body: 'Enterprise Value divided by Earnings Before Interest, Tax, Depreciation & Amortisation. More complete than P/E as it accounts for debt. Under 10x is generally considered cheap; tech companies often trade 20x+. Use same-sector comparisons.', good: 'Value: < 10x | Growth: 15–25x is common' },
          'peg_ratio':          { title: 'PEG Ratio', body: 'P/E divided by earnings growth rate. Adjusts the P/E for growth. A PEG < 1 is traditionally considered undervalued — you\'re paying less than the growth rate justifies. PEG > 2 suggests you\'re paying a hefty premium for growth.', good: 'Undervalued: < 1 | Fair: ~1 | Expensive: > 2' },
          'price_to_sales':     { title: 'Price to Sales (P/S)', body: 'Market cap divided by annual revenue. Useful for companies with no earnings yet (startups, turnarounds). Under 1x is cheap; SaaS and tech companies can sustain high multiples due to recurring revenue.', good: 'Value: < 1x | Tech: 3–10x is common' },
          // Profitability
          'profit_margin':      { title: 'Profit Margin (Net)', body: 'Net profit as a % of revenue. A 15% margin means the company keeps ₹15 as profit from every ₹100 it earns. Higher is better. Compare within industry — grocery retail at 2-3% is fine, software at 20%+ is expected.', good: 'Good: > 10% | Excellent: > 20%' },
          'roe':                { title: 'Return on Equity (ROE)', body: 'Net profit divided by shareholders\' equity, expressed as %. Measures how efficiently management uses shareholder money. A 20% ROE means ₹20 earned for every ₹100 of equity. Consistently high ROE (>15%) over many years is a hallmark of quality businesses.', good: 'Good: > 15% | Excellent: > 25%' },
          'roa':                { title: 'Return on Assets (ROA)', body: 'Net profit divided by total assets. Shows how efficiently the company uses all its assets (including debt-funded ones) to generate profit. Less affected by leverage than ROE.', good: 'Good: > 8% | Excellent: > 15%' },
          'revenue_growth':     { title: 'Revenue Growth', body: 'Year-over-year increase in total sales. The top-line driver of long-term value. Consistent double-digit growth is a strong positive; declining revenues are a red flag. Always check if growth is organic or acquisition-driven.', good: 'Good: > 10% YoY | Excellent: > 20% YoY' },
          'earnings_growth':    { title: 'Earnings Growth', body: 'Year-over-year increase in net profit. Ideally should grow faster than revenue (improving margins). Volatile earnings (up one year, down next) are harder to value and riskier.', good: 'Good: > 15% YoY | Consistent growth > 3 years = strong signal' },
          // Health
          'debt_to_equity':     { title: 'Debt to Equity (D/E)', body: 'Total debt divided by shareholders\' equity. Shows how much the company relies on borrowed money vs. owner funds. For Sharia compliance the threshold is 33% (0.33x). In general, D/E < 1x is conservative; > 2x is leveraged. Capital-intensive industries like telecom & utilities naturally carry more debt.', good: 'Sharia limit: < 0.33 | Conservative: < 1x' },
          'current_ratio':      { title: 'Current Ratio', body: 'Current assets divided by current liabilities. A measure of short-term financial health. Ratio > 1 means the company can cover its near-term obligations. < 1 is a liquidity warning. Too high (> 3) may mean idle cash is being underutilised.', good: 'Healthy: 1.5–3x | Below 1 = watch closely' },
          'cash_to_assets':     { title: 'Cash / Total Assets %', body: 'Cash and equivalents as a % of total assets. For Sharia compliance this must be < 33% — too much cash in interest-bearing accounts is non-compliant. In general, high cash holdings can be a strength (buffer) or a weakness (management not deploying capital).', good: 'Sharia limit: < 33%' },
          'receivables_to_assets': { title: 'Receivables / Assets %', body: 'Trade receivables as a % of total assets. For Sharia compliance must be < 50%. High receivables can indicate aggressive revenue recognition, collection problems, or businesses with long payment cycles (e.g. infrastructure).', good: 'Sharia limit: < 50%' },
          'other_rev_pct':      { title: 'Non-Halal Revenue %', body: 'Revenue from non-permissible sources (interest income, alcohol, gambling, etc.) as a % of total revenue. For Sharia compliance this must be < 5%. Any amount > 0 requires purification of that proportion of your income (see Purification Calculator).', good: 'Sharia limit: < 5% | Ideal: 0%' },
          // Research sections
          'section_thesis':     { title: 'Investment Thesis', body: 'The core bull/bear case for the stock. Includes a verdict (Buy/Hold/Sell), a 12-month price target range, and the key drivers. This is the starting point — does the overall story make sense before digging into details?', good: null },
          'section_industry':   { title: 'Industry Analysis', body: 'Examines the competitive landscape, industry growth rate, Porter\'s Five Forces (supplier power, buyer power, rivalry, new entrants, substitutes), and macro tailwinds/headwinds. A good business in a bad industry rarely stays good.', good: null },
          'section_business':   { title: 'Business Model', body: 'How the company makes money — revenue streams, pricing power, switching costs, economies of scale, and competitive moat. A wide moat (strong defensible advantage) is the most durable source of long-term returns.', good: null },
          'section_management': { title: 'Management Quality', body: 'Quality and track record of promoters, CEO, and board. Looks at capital allocation decisions (acquisitions, dividends, buybacks), insider ownership, and red flags like related-party transactions. Management quality is often underweighted by retail investors.', good: null },
          'section_esg':        { title: 'ESG & Governance', body: 'Environmental, Social, and Governance factors. For Islamic investors governance overlap is significant — poor governance often correlates with Sharia violations. Environmental risk (climate, pollution fines) can become material financial risk.', good: null },
          'section_estimates':  { title: 'Analyst Estimates', body: 'Consensus revenue and EPS forecasts for the next 1–2 years, with bull/bear scenarios. Useful to understand what\'s already "priced in" — a stock that trades at consensus is fairly priced; one trading below suggests the market expects earnings misses.', good: null },
          'section_revenue':    { title: 'Revenue Deep-Dive', body: 'Breaks revenue into segments, geographies, and growth drivers. Helps identify which parts of the business are growing vs. stagnating. Segment mix shifts can be early signals of both opportunity and risk.', good: null },
          'section_catalysts':  { title: 'Catalysts & Risks', body: 'Near-term events that could cause the stock to re-rate up or down: product launches, regulatory decisions, contract wins, management changes, macro events. Catalysts give timing context to an otherwise solid thesis.', good: null },
          'section_cyclical':   { title: 'Cyclicality', body: 'How much the business\'s earnings fluctuate with economic cycles. Cyclical businesses (auto, steel, cement) swing heavily; defensive ones (pharma, FMCG) are more stable. Knowing where we are in the cycle helps time entries/exits.', good: null },
          'section_ma':         { title: 'M&A & Corporate Actions', body: 'History and pipeline of mergers, acquisitions, demergers, and fundraising. Acquisitions create value when synergies are real and price paid is fair; they destroy value when management overpays or diversifies into unrelated areas.', good: null },
          'section_value':      { title: 'Valuation Deep-Dive', body: 'Multi-model valuation: DCF (intrinsic value based on future cash flows), comparables (peer multiples), and historical mean reversion. No single model is definitive — the range of outputs gives a margin of safety estimate.', good: null },
          'section_faq':        { title: 'Investor FAQ', body: 'Common questions and concerns investors typically raise about this stock, with direct answers. Good for stress-testing your thesis against the bear case without confirmation bias.', good: null },
          'section_credit':     { title: 'Credit & Balance Sheet', body: 'Deep dive into debt structure, maturity profile, covenants, credit ratings, and liquidity. A company with great earnings but fragile balance sheet (short-term debt, covenant risk) can face sudden distress.', good: null },
          'section_geofx':      { title: 'Geography & FX Risk', body: 'Revenue and cost exposure by country/currency. Indian companies with USD revenues benefit when INR weakens; those with USD costs are hurt. Political risk in export markets is also considered here.', good: null },
          'section_capital':    { title: 'Capital Allocation', body: 'How management reinvests profits: capex intensity, R&D, dividends, buybacks, acquisitions. The best compounders allocate capital at high incremental returns. A company that can\'t find good uses for cash should return it to shareholders.', good: null },
          'section_forensic':   { title: 'Forensic Accounting', body: 'Red flags in financial statements: revenue recognition issues, aggressive capitalisation of expenses, rising receivables without matching revenue growth, related-party transactions, and auditor changes. The 8 most-common accounting tricks that precede blow-ups.', good: null },
          'section_iprd':       { title: 'IP & R&D', body: 'Intangible assets, patent portfolio, R&D spend, and technology moat. Critical for pharma, tech, and specialty chemicals. A company with expiring patents and no pipeline is a risk; one with a growing IP portfolio has durable pricing power.', good: null },
          'section_supply_chain': { title: 'Supply Chain', body: 'Key raw material dependencies, supplier concentration, logistics risk, and PLI/China+1 opportunities. Post-COVID supply chain resilience has become a key competitive differentiator. Single-source dependencies are a hidden risk.', good: null },
        },
        showExplainer(key, event) {
          const content = this.METRIC_EXPLAINERS[key];
          if (!content) return;
          const rect = event.currentTarget.getBoundingClientRect();
          this.explainer = {
            open: true,
            pinned: false,
            key,
            content,
            x: Math.min(rect.left + window.scrollX, window.innerWidth - 340),
            y: rect.bottom + window.scrollY + 6,
          };
        },
        pinExplainer() { this.explainer.pinned = true; },
        hideExplainer() { if (!this.explainer.pinned) this.explainer.open = false; },
        closeExplainer() { this.explainer = { ...this.explainer, open: false, pinned: false }; },
        // ---- Purification Calculator ----
        async purificationLookup(sym) {
          const symbol = (sym || this.purificationSymbol || '').trim().toUpperCase();
          if (!symbol) return;
          this.purificationLoading = true;
          this.purificationSharia = null;
          this.purificationNonHalalPct = null;
          try {
            // Detect market from holdingMarkets or default to india
            const mkt = (this.holdingMarkets[symbol] === 'US') ? 'us' : 'india';
            // Resolve to full ticker if needed (e.g. MARUTI → MARUTI.NS)
            let ticker = symbol;
            if (mkt === 'india' && !symbol.includes('.')) {
              for (const suffix of ['.NS', '.BO']) {
                const candidate = symbol + suffix;
                const r = await fetch(`/api/symbol/${encodeURIComponent(candidate)}?market=${mkt}`);
                if (r.ok) { ticker = candidate; break; }
              }
            }
            const res = await fetch(`/api/symbol/${encodeURIComponent(ticker)}?market=${mkt}`);
            if (res.ok) {
              const data = await res.json();
              this.purificationSharia = data;
              this.purificationNonHalalPct = data.other_revenue_to_revenue_pct ?? null;
            }
          } catch(e) { /* ignore */ }
          this.purificationLoading = false;
        },
        purificationSelectHolding(symbol) {
          this.purificationSymbol = symbol;
          // Pre-fill buy price from holdings avg price
          const row = (this.personalIndexInputRows || []).find(r => r.symbol === symbol || r.symbol.startsWith(symbol));
          if (row) this.purificationBuyPrice = row.price || '';
          this.purificationLookup(row ? row.symbol : symbol);
        },
        purificationEffectivePct() {
          if (this.purificationNonHalalOverride !== '') return parseFloat(this.purificationNonHalalOverride) || 0;
          return this.purificationNonHalalPct ?? 0;
        },
        purificationAmount() {
          const pct = this.purificationEffectivePct();
          if (this.purificationMode === 'dividends') {
            const d = parseFloat(this.purificationDividends);
            if (!d || d <= 0) return null;
            return d * (pct / 100);
          } else {
            const buy = parseFloat(this.purificationBuyPrice);
            const sell = parseFloat(this.purificationSellPrice);
            const units = parseFloat(this.purificationUnits);
            if (!buy || !sell || !units) return null;
            const gain = (sell - buy) * units;
            if (gain <= 0) return null;
            return gain * (pct / 100);
          }
        },
        purificationCurrency() {
          const sym = this.purificationSymbol.toUpperCase();
          return (this.holdingMarkets[sym] === 'US') ? '$' : '₹';
        },
        purificationIsFullyNonCompliant() {
          return this.purificationSharia && this.purificationSharia.Sharia === 'No';
        },
        // ---- End Portfolio Analytics ----
        syncPersonalIndexTextFromRows(save = false) {
          // Always persist prices so they survive page reloads.
          // 'cost_basis' mode includes price when present; analysis mode is chosen at run time.
          this.personalIndexHoldingsText = this.serializePersonalIndexRows('cost_basis');
          if (save) this.saveSettings();
        },
        resetPersonalIndexDraft() {
          this.symbolPickerState.personal_index.query = '';
          this.symbolPickerState.personal_index.open = false;
          this.personalIndexDraftUnits = 1;
          this.personalIndexDraftPrice = '';
        },
        async selectPersonalIndexDraftSymbol(explicitSymbol = null) {
          const query = (explicitSymbol || this.symbolPickerMatches('personal_index')[0] || this.symbolPickerState.personal_index.query || '').trim();
          if (!query) return;
          const resolved = await this.resolveSymbolInput(query);
          if (!resolved) return;
          this.symbolPickerState.personal_index.query = resolved;
          this.symbolPickerState.personal_index.open = false;
        },
        async addPersonalIndexHolding() {
          const rawSymbol = (this.symbolPickerState.personal_index.query || '').trim();
          const units = Number(this.personalIndexDraftUnits);
          const price = this.personalIndexDraftPrice === '' || this.personalIndexDraftPrice == null ? null : Number(this.personalIndexDraftPrice);
          if (!rawSymbol) {
            
            return;
          }
          if (!Number.isFinite(units) || units <= 0) {
            
            return;
          }
          const symbol = await this.resolveSymbolInput(rawSymbol);
          if (!symbol) {
            
            return;
          }
          const existingIndex = this.personalIndexInputRows.findIndex(row => (row.symbol || '').toUpperCase() === symbol.toUpperCase());
          if (existingIndex >= 0) {
            const existing = this.personalIndexInputRows[existingIndex];
            existing.units = Number(existing.units || 0) + units;
            if (Number.isFinite(price) && price > 0) existing.price = price;
            this.personalIndexInputRows = [...this.personalIndexInputRows];
          } else {
            this.personalIndexInputRows = [
              ...this.personalIndexInputRows,
              { symbol, units, price: Number.isFinite(price) && price > 0 ? price : '' }
            ];
          }
          
          this.syncPersonalIndexTextFromRows(true);
          this.resetPersonalIndexDraft();
        },
        updatePersonalIndexHolding(index, field, value) {
          const row = this.personalIndexInputRows[index];
          if (!row) return;
          if (field === 'units') {
            const units = Number(value);
            row.units = Number.isFinite(units) && units > 0 ? units : '';
          } else if (field === 'price') {
            const price = value === '' || value == null ? null : Number(value);
            row.price = Number.isFinite(price) && price > 0 ? price : '';
          }
          this.personalIndexInputRows = [...this.personalIndexInputRows];
          
          this.syncPersonalIndexTextFromRows(true);
        },
        removePersonalIndexHolding(index) {
          const removed = this.personalIndexInputRows[index];
          if (removed?.symbol) {
            const { [removed.symbol]: _, ...rest } = this.holdingMarkets;
            this.holdingMarkets = rest;
          }
          this.personalIndexInputRows = this.personalIndexInputRows.filter((_, idx) => idx !== index);
          
          this.syncPersonalIndexTextFromRows(true);
        },
        async fetchPortfolioPerformance() {
          const text = this.serializePersonalIndexRows('cost_basis');
          if (!text.trim()) {
            this.performanceData = null;
            this.performanceError = '';
            return;
          }
          // Auto-derive anchor date from first trade in ledger if not manually set
          if (!this.portfolioInvestedSince) {
            try {
              const r = await fetch('/api/trades?limit=1000');
              const d = await r.json();
              const dates = (d.trades || []).map(t => t.date).filter(Boolean).sort();
              if (dates.length) this.portfolioInvestedSince = dates[0];
            } catch(_) {}
          }
          this.performanceLoading = true;
          this.performanceError = '';
          try {
            const r = await fetch(API + '/portfolio/performance', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                holdings_text: text,
                holding_markets: this.holdingMarkets || {},
                anchor_date: this.portfolioInvestedSince || null,
              }),
            });
            const data = await r.json();
            if (!r.ok) {
              this.performanceData = null;
              this.performanceError = data.detail || data.error || 'Performance calculation failed';
              return;
            }
            this.performanceData = data;
          } catch (e) {
            this.performanceData = null;
            this.performanceError = 'Could not reach performance API';
          } finally {
            this.performanceLoading = false;
          }
        },
        async fetchUsdInrRate() {
          try {
            // Use yfinance via our backend: USDINR=X ticker
            const r = await fetch(API + '/symbol/USDINR=X/section/overview').then(r => r.json()).catch(() => null);
            const price = r?.current_price ?? r?.regularMarketPrice ?? r?.price ?? r?.previousClose;
            if (price && price > 1) {
              this.usdInrRate = Number(price);
              this.usdInrUpdated = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
              return;
            }
          } catch (_) {}
          // Fallback: fetch from open exchange rates (no key needed for USD/INR)
          try {
            const r = await fetch('https://open.er-api.com/v6/latest/USD').then(r => r.json());
            if (r?.rates?.INR) {
              this.usdInrRate = Number(r.rates.INR);
              this.usdInrUpdated = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
            }
          } catch (_) {}
        },
        async onMarketChange() {
          await this.saveSettings();
          await this.fetchUniverse();
          await this.fetchReportPeriods();
          await this.fetchCounts();
          await this.fetchSymbolsMissing();
          this.onPageChange();
          this.fetchPolicyAnalysis();
        },
        async fetchReportPeriods() { const r = await fetch(API + '/report-periods').then(r => r.json()); this.reportPeriods = r && r.length ? r : ['All periods', '31st March 2025']; if (!this.reportPeriods.includes(this.period)) this.period = this.reportPeriods[0]; },
        async fetchUniverse() { const r = await fetch(API + '/universe?market=' + encodeURIComponent(this.market)).then(r => r.json()); this.tickers = r.tickers || []; },
        async fetchCounts() { this.loading = true; try { const r = await fetch(API + '/counts?period=' + encodeURIComponent(this.period) + '&market=' + encodeURIComponent(this.market)).then(r => r.json()); this.counts = r; } finally { this.loading = false; } },
        async fetchAllStocks() {
          this.loading = true;
          try {
            const r = await fetch(API + '/sharia?period=' + encodeURIComponent(this.period) + '&market=' + encodeURIComponent(this.market)).then(r => r.json());
            this.allStocksRows = r.rows || [];
            // Merge any already-loaded quality scores back in
            if (this.qualityLoaded) this._mergeQualityIntoRows();
            if (this.allStocksRows.length && !this.tableColumns.all_stocks)
              this.tableColumns.all_stocks = Object.fromEntries(Object.keys(this.allStocksRows[0]).map(k => [k, true]));
            this.$nextTick(() => {
              if (this.page === 'all_stocks' && this.allStocksRows.length)
                this.initTableWithColumns('all_stocks', 'all-stocks-table', this.allStocksRows);
            });
          } finally { this.loading = false; }
        },
        async fetchQualityScores() {
          this.qualityLoading = true;
          try {
            const r = await fetch(API + '/screener?sharia_only=false&market=' + encodeURIComponent(this.market)).then(r => r.json());
            const scoreMap = {};
            (r.rows || []).forEach(row => { scoreMap[row.symbol] = row; });
            this._qualityScoreMap = scoreMap;
            this._mergeQualityIntoRows();
            this.qualityLoaded = true;
            this.$nextTick(() => {
              if (this.page === 'all_stocks' && this.allStocksRows.length)
                this.initTableWithColumns('all_stocks', 'all-stocks-table', this.allStocksRows);
            });
          } catch(e) { console.error('Quality scores failed:', e); }
          finally { this.qualityLoading = false; }
        },
        _mergeQualityIntoRows() {
          const scoreMap = this._qualityScoreMap || {};
          this.allStocksRows = this.allStocksRows.map(row => {
            const q = scoreMap[row.symbol];
            if (!q) return row;
            return {
              ...row,
              total_score: q.total_score ?? null,
              quality_label: q.label ?? null,
              profitability_score: q.profitability_score ?? null,
              cash_generation_score: q.cash_generation_score ?? null,
              financial_strength_score: q.financial_strength_score ?? null,
              valuation_score: q.valuation_score ?? null,
              // Profitability
              roe: q.roe ?? null,
              roa: q.roa ?? null,
              operating_margin: q.operating_margin ?? null,
              gross_margin: q.gross_margin ?? null,
              net_margin: q.net_margin ?? null,
              ebitda_margin: q.ebitda_margin ?? null,
              roce: q.roce ?? null,
              // Growth
              revenue_growth: q.revenue_growth ?? null,
              earnings_growth: q.earnings_growth ?? null,
              // Financial health
              fcf_conversion: q.fcf_conversion ?? null,
              debt_to_equity: q.debt_to_equity ?? null,
              current_ratio: q.current_ratio ?? null,
              quick_ratio: q.quick_ratio ?? null,
              interest_coverage: q.interest_coverage ?? null,
              // Valuation
              peg_ratio: q.peg_ratio ?? null,
              trailing_pe: q.trailing_pe ?? null,
              forward_pe: q.forward_pe ?? null,
              price_to_book: q.price_to_book ?? null,
              ev_to_ebitda: q.ev_to_ebitda ?? null,
              price_to_sales: q.price_to_sales ?? null,
              ev_to_revenue: q.ev_to_revenue ?? null,
              // Market
              beta: q.beta ?? null,
              dividend_yield: q.dividend_yield ?? null,
              payout_ratio: q.payout_ratio ?? null,
              vs_200dma: q.vs_200dma ?? null,
            };
          });
        },
        async fetchQualityScore(symbol) {
          const sym = symbol || this.perStockSymbol;
          if (!sym) return;
          this.perStockQualityLoading = true;
          try {
            const r = await fetch(API + '/symbol/' + encodeURIComponent(sym) + '/quality').then(r => r.json());
            this.perStockQuality = r.error ? null : r;
          } catch(e) { this.perStockQuality = null; }
          finally { this.perStockQualityLoading = false; }
        },
        /* --- Reusable table + column selection system --- */
        tableRegistry: {
          all_stocks:                { elId: 'all-stocks-table',               dataKey: 'allStocksRows' },
          compare:                   { elId: 'compare-table',                  dataKey: 'compareRows' },
          per_stock_periods:         { elId: 'per-stock-periods-table',        dataKey: 'perStockPeriodRows',         opts: { pagination: false } },
          watchlist:                 { elId: 'watchlist-table',                 dataKey: 'watchlistRows' },
        },
        getTableData(tableKey) {
          const reg = this.tableRegistry[tableKey];
          return reg ? this[reg.dataKey] : [];
        },
        getTableOpts(tableKey) {
          const reg = this.tableRegistry[tableKey];
          const opts = { ...(reg?.opts || {}) };
          if (this.tableColumns[tableKey]) opts.visibleColumns = this.tableColumns[tableKey];
          if (tableKey === 'all_stocks') {
            opts.minWidth = 130;
            opts.rowFormatter = (row) => {
              const d = row.getData();
              if ((d.Sharia || d.sharia) === 'Yes') {
                const el = row.getElement();
                el.classList.add('sharia-compliant-row');
                el.style.backgroundColor = '#ecfdf5';
              }
            };
          }
          return opts;
        },
        initTableWithColumns(tableKey, elId, data, extraOpts = {}) {
          const opts = { ...this.getTableOpts(tableKey), ...extraOpts };
          elId = elId || this.tableRegistry[tableKey]?.elId;
          data = data || this.getTableData(tableKey);
          if (!data || !data.length) return;
          // Auto-init column visibility if not set
          if (!this.tableColumns[tableKey]) {
            this.tableColumns[tableKey] = Object.fromEntries(Object.keys(data[0]).map(k => [k, true]));
          }
          this.initTable(tableKey, elId, data, opts);
        },
        toggleTableColumn(tableKey, field) {
          if (!this.tableColumns[tableKey]) return;
          this.tableColumns[tableKey][field] = !this.tableColumns[tableKey][field];
          const data = this.getTableData(tableKey);
          if (data && data.length) {
            const reg = this.tableRegistry[tableKey];
            if (reg) this.initTableWithColumns(tableKey, reg.elId, data);
          }
          this.saveSettings();
        },
        getColumnDefs(tableKey) {
          const data = this.getTableData(tableKey);
          if (!data || !data[0]) return [];
          return Object.keys(data[0]).map(field => ({ field, title: field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) }));
        },
        COLUMN_GROUPS: {
          all_stocks: [
            { label: 'Identity', icon: '🏷️', fields: ['symbol', 'name', 'exchange', 'industry', 'sector'] },
            { label: 'Sharia', icon: '☪️', fields: ['Sharia', 'industry_compliant'] },
            { label: 'Sharia Ratios', icon: '📐', fields: ['debt_to_equity_ratio', 'cash_to_assets_pct', 'other_revenue_to_revenue_pct', 'receivables_to_assets_pct'] },
            { label: 'Financials', icon: '💰', fields: ['total_assets', 'total_revenue', 'total_receivables', 'cash_and_short_term_investments', 'other_revenue', 'market_cap'] },
            { label: 'Reporting', icon: '📅', fields: ['report_period', 'period_type'] },
          ],
          per_stock_periods: [
            { label: 'Period', icon: '📅', fields: ['report_period', 'period_type'] },
            { label: 'Sharia', icon: '☪️', fields: ['Sharia'] },
            { label: 'Ratios', icon: '📐', fields: ['debt_to_equity_ratio', 'cash_to_assets_pct', 'other_revenue_to_revenue_pct', 'receivables_to_assets_pct'] },
            { label: 'Financials', icon: '💰', fields: ['total_assets', 'total_revenue', 'market_cap'] },
          ],
          watchlist: [
            { label: 'Identity', icon: '🏷️', fields: ['symbol', 'name', 'industry', 'sector'] },
            { label: 'Sharia', icon: '☪️', fields: ['Sharia'] },
            { label: 'Ratios', icon: '📐', fields: ['debt_to_equity_ratio', 'cash_to_assets_pct', 'other_revenue_to_revenue_pct', 'receivables_to_assets_pct'] },
            { label: 'Market', icon: '📈', fields: ['market_cap', 'report_period'] },
          ],
          compare: [
            { label: 'Identity', icon: '🏷️', fields: ['symbol', 'name', 'industry', 'sector'] },
            { label: 'Sharia', icon: '☪️', fields: ['Sharia', 'debt_to_equity_ratio', 'cash_to_assets_pct'] },
            { label: 'Market', icon: '📈', fields: ['market_cap'] },
          ],
        },
        getColumnGroups(tableKey) {
          const allFields = this.getColumnDefs(tableKey).map(c => c.field);
          const groups = this.COLUMN_GROUPS[tableKey];
          if (!groups) {
            // fallback: single group
            return [{ label: 'Columns', icon: '📋', fields: allFields }];
          }
          // Collect known fields
          const knownFields = new Set(groups.flatMap(g => g.fields));
          // Any fields not in a group → "Other"
          const other = allFields.filter(f => !knownFields.has(f));
          const result = groups.map(g => ({ ...g, fields: g.fields.filter(f => allFields.includes(f)) })).filter(g => g.fields.length);
          if (other.length) result.push({ label: 'Other', icon: '⋯', fields: other });
          return result;
        },
        columnGroupAllChecked(tableKey, fields) {
          return fields.every(f => (this.tableColumns[tableKey] || {})[f] !== false);
        },
        toggleColumnGroup(tableKey, fields, forceOn) {
          const allOn = forceOn ?? !this.columnGroupAllChecked(tableKey, fields);
          if (!this.tableColumns[tableKey]) return;
          fields.forEach(f => { this.tableColumns[tableKey][f] = allOn; });
          const data = this.getTableData(tableKey);
          if (data && data.length) {
            const reg = this.tableRegistry[tableKey];
            if (reg) this.initTableWithColumns(tableKey, reg.elId, data);
          }
          this.saveSettings();
        },
        columnModalSelectAll(on) {
          const key = this.columnModalTable;
          if (!key || !this.tableColumns[key]) return;
          Object.keys(this.tableColumns[key]).forEach(f => { this.tableColumns[key][f] = on; });
          const data = this.getTableData(key);
          if (data && data.length) {
            const reg = this.tableRegistry[key];
            if (reg) this.initTableWithColumns(key, reg.elId, data);
          }
          this.saveSettings();
        },
        async fetchPerStock() {
          if (!this.perStockSymbol) return;
          this.loading = true;
          try {
            const sym = this.perStockSymbol;
            this._perStockLoadedSym = sym;
            this.fieldGaps = {};  // reset for new symbol
            this.fetchFieldGaps(sym);  // non-blocking
            this.perStockRow = await fetch(API + '/symbol/' + encodeURIComponent(sym)).then(r => r.ok ? r.json() : null);
            // Fetch all period rows for the periods table
            const pr = await fetch(API + '/symbol/' + encodeURIComponent(sym) + '/periods').then(r => r.ok ? r.json() : { rows: [] });
            this.perStockPeriodRows = pr.rows || [];
            // Pre-load all research section envelopes so pills light up immediately
            fetch(API + '/symbol/' + encodeURIComponent(sym) + '/research').then(r => r.ok ? r.json() : null).then(res => {
              if (!res || !res.sections) return;
              if (!this.perStockSectionData[sym]) this.perStockSectionData[sym] = {};
              for (const [sec, envelope] of Object.entries(res.sections)) {
                if (envelope && envelope.data) {
                  this.perStockSectionData[sym][sec] = envelope;
                }
              }
              this.perStockSectionData = { ...this.perStockSectionData };
            });
            this.$nextTick(() => {
              this.fetchSectionDataIfNeeded(this.perStockTab);
              if (this.perStockPeriodRows.length) this.initTableWithColumns('per_stock_periods');
              // Pre-populate DCF inputs once valuation data is available
              this.fetchSectionData('valuation').then(() => this.initDcf());
            });
          } catch { this.perStockRow = null; this.perStockPeriodRows = []; }
          finally { this.loading = false; }
        },
        getSectionData(section) { const sym = this.perStockSymbol; if (!sym) return null; return (this.perStockSectionData[sym] || {})[section] || null; },
        hasResearchData(section) { const d = this.getSectionData(section); return d && d.data && !d.error; },
        formatMajorHolder(h) {
          const labelMap = { insidersPercentHeld: 'Insiders held', institutionsPercentHeld: 'Institutions held', institutionsFloatPercentHeld: 'Float held by inst.', institutionsCount: 'Institution count' };
          const label = labelMap[h.label] || h.label;
          const isCount = h.label === 'institutionsCount';
          let val;
          if (isCount) {
            val = typeof h.value === 'number' ? Math.round(h.value).toLocaleString() : (h.value ?? '—');
          } else if (typeof h.value === 'number') {
            const pct = h.value > 0 && h.value <= 1 ? h.value * 100 : h.value;
            val = pct.toFixed(2) + '%';
          } else {
            val = h.value ?? '—';
          }
          return label + ': ' + val;
        },
        formatPct(val) { if (val == null) return '—'; const n = parseFloat(val); return isNaN(n) ? val : n.toFixed(2) + '%'; },
        researchVersionKey(section) { return (this.perStockSymbol || '') + '_' + section; },
        async fetchResearchVersions(section) {
          const sym = this.perStockSymbol; if (!sym) return;
          const key = this.researchVersionKey(section);
          const r = await fetch(API + '/symbol/' + encodeURIComponent(sym) + '/research/' + section + '/versions').catch(() => null);
          if (!r || !r.ok) return;
          const data = await r.json();
          this.researchVersions = { ...this.researchVersions, [key]: data.versions || [] };
        },
        toggleResearchVersions(section) {
          const key = this.researchVersionKey(section);
          if (this.researchVersionOpen === key) { this.researchVersionOpen = null; return; }
          this.researchVersionOpen = key;
          this.fetchResearchVersions(section);
        },
        async deleteResearchVersion(section, idx) {
          const sym = this.perStockSymbol; if (!sym) return;
          await fetch(API + '/symbol/' + encodeURIComponent(sym) + '/research/' + section + '/versions/' + idx, { method: 'DELETE' });
          this.fetchResearchVersions(section);
        },
        async restoreResearchVersion(section, idx) {
          const sym = this.perStockSymbol; if (!sym) return;
          const r = await fetch(API + '/symbol/' + encodeURIComponent(sym) + '/research/' + section + '/versions/' + idx + '/restore', { method: 'POST' });
          if (r.ok) {
            const data = await r.json();
            if (!this.perStockSectionData[sym]) this.perStockSectionData[sym] = {};
            this.perStockSectionData[sym][section] = data.envelope;
            this.researchVersionOpen = null;
            this.fetchResearchVersions(section);
          }
        },
        // ── DCF Calculator methods ────────────────────────────────────────
        get dcfCurrSym() { return this.market === 'us' ? '$' : '₹'; },
        dcfCalc(g1, g2, gT, wacc) {
          const fcfCr = parseFloat(this.dcfFcfInput) || 0;
          const shares = parseFloat(this.dcfSharesInput) || 1;
          const cash = parseFloat(this.dcfCashInput) || 0;
          const debt = parseFloat(this.dcfDebtInput) || 0;
          if (!fcfCr || !shares) return null;
          const r = wacc / 100, gRate1 = g1 / 100, gRate2 = g2 / 100, gTerm = gT / 100;
          if (r <= gTerm) return null;
          let pv = 0, fcfNow = fcfCr;
          for (let t = 1; t <= this.dcf.years1; t++) { fcfNow *= (1 + gRate1); pv += fcfNow / Math.pow(1 + r, t); }
          for (let t = 1; t <= this.dcf.years2; t++) { fcfNow *= (1 + gRate2); pv += fcfNow / Math.pow(1 + r, this.dcf.years1 + t); }
          const tv = (fcfNow * (1 + gTerm)) / (r - gTerm);
          const pvTv = tv / Math.pow(1 + r, this.dcf.years1 + this.dcf.years2);
          return (pv + pvTv + cash - debt) / shares;
        },
        get dcfBase() { return this.dcfCalc(this.dcf.g1, this.dcf.g2, this.dcf.gT, this.dcf.wacc); },
        get dcfBear() { return this.dcfCalc(Math.max(0, this.dcf.g1-7), Math.max(0, this.dcf.g2-5), Math.max(1, this.dcf.gT-1), this.dcf.wacc+2); },
        get dcfBull() { return this.dcfCalc(this.dcf.g1+5, this.dcf.g2+3, Math.min(6, this.dcf.gT+1), Math.max(8, this.dcf.wacc-2)); },
        dcfMos(iv) { const p = parseFloat(this.dcf.price); if (!iv || !p) return null; return (iv - p) / p * 100; },
        dcfFmt(v) { if (v == null || !isFinite(v)) return '—'; return this.dcfCurrSym + Math.round(v).toLocaleString(); },
        dcfMosFmt(iv) { const m = this.dcfMos(iv); if (m == null) return ''; return (m > 0 ? '+' : '') + m.toFixed(1) + '%'; },
        dcfMosColor(iv) { const m = this.dcfMos(iv); if (m == null) return 'text-slate-400'; return m > 20 ? 'text-emerald-400' : m > 0 ? 'text-amber-400' : 'text-rose-400'; },
        sensWaccs() { const w = this.dcf.wacc; return [w-3, w-1.5, w, w+1.5, w+3]; },
        sensGrowths() { const g = this.dcf.g1; return [g-6, g-3, g, g+3, g+6]; },
        sensVal(w, g) { return this.dcfCalc(g, this.dcf.g2, this.dcf.gT, w); },
        sensColor(iv) {
          const m = this.dcfMos(iv);
          if (m == null) return 'bg-slate-800 text-slate-400';
          if (m > 30) return 'bg-emerald-900/60 text-emerald-300';
          if (m > 15) return 'bg-emerald-900/30 text-emerald-400';
          if (m > 0)  return 'bg-amber-900/30 text-amber-300';
          if (m > -15) return 'bg-rose-900/20 text-rose-400';
          return 'bg-rose-900/50 text-rose-300';
        },
        initDcf() {
          try {
            const vSec = this.getSectionData('valuation') || {};
            const fSec = this.getSectionData('financials') || {};
            const rawFcf = vSec.freeCashflow || fSec.freeCashFlow;
            const rawShares = vSec.sharesOutstanding;
            const rawCash = vSec.totalCash;
            const rawDebt = vSec.totalDebt;
            const rawPrice = vSec.currentPrice;
            const rawGrowth = vSec.revenueGrowth || vSec.earningsGrowth;
            if (rawFcf) this.dcfFcfInput = String(+(rawFcf / 1e7).toFixed(1));
            if (rawShares) this.dcfSharesInput = String(+(rawShares / 1e5).toFixed(2));
            if (rawCash) this.dcfCashInput = String(+(rawCash / 1e7).toFixed(1));
            if (rawDebt) this.dcfDebtInput = String(+(rawDebt / 1e7).toFixed(1));
            if (rawPrice) this.dcf.price = rawPrice;
            if (rawGrowth && rawGrowth > 0) this.dcf.g1 = Math.min(40, +(rawGrowth * 100).toFixed(1));
          } catch(_) {}
        },
        // ── Field gap system ──────────────────────────────────────────────
        fieldGaps: {},  // {section: {field: gap_info}} for current symbol
        // ── DCF Calculator state ─────────────────────────────────────────
        dcf: { g1: 15, g2: 8, gT: 4, wacc: 12, years1: 7, years2: 5, price: null },
        dcfFcfInput: '', dcfSharesInput: '', dcfCashInput: '', dcfDebtInput: '',
        async fetchFieldGaps(sym) {
          if (!sym) return;
          try {
            const r = await fetch(API + '/symbol/' + encodeURIComponent(sym) + '/field-gaps').then(r => r.ok ? r.json() : null);
            if (r && r.gaps) this.fieldGaps = r.gaps;
          } catch (_) {}
        },
        isFieldGap(section, field) {
          return this.fieldGaps?.[section]?.[field]?.status === 'not_found_in_api' && !this.fieldGaps?.[section]?.[field]?.filled_by;
        },
        // ── More (AI) generic renderer ────────────────────────────────────
        _escHtml(s) {
          return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
        },
        _fmtKey(k) {
          return String(k).replace(/_/g,' ').replace(/\b\w/g, l => l.toUpperCase());
        },
        renderMoreAISection(section) {
          const d = this.getSectionData(section)?.data;
          if (!d) return '<p class="text-slate-400 text-sm">No data.</p>';
          let html = '';

          // 1. Summary banner
          if (d.summary) {
            html += `<div class="bg-slate-50 border border-slate-200 rounded-lg px-4 py-3 mb-5">
              <p class="text-sm text-slate-700 leading-relaxed">${this._escHtml(d.summary)}</p></div>`;
          }

          // 2. Special: FAQ questions
          if (d.questions && Array.isArray(d.questions)) {
            html += '<div class="space-y-3 mb-4">';
            for (const q of d.questions) {
              html += `<div class="rounded-lg border border-slate-200 p-4">
                <p class="text-sm font-semibold text-slate-800 mb-1.5">${this._escHtml(q.question || q.q || '')}</p>
                <p class="text-sm text-slate-600 leading-relaxed">${this._escHtml(q.answer || q.a || '')}</p>
              </div>`;
            }
            html += '</div>';
          }

          // 3. Special: red_flags / green_flags lists
          if (d.red_flags || d.green_flags) {
            html += '<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">';
            if (d.red_flags && d.red_flags.length) {
              html += '<div><h4 class="text-xs font-semibold text-rose-600 uppercase tracking-wider mb-2">⚠ Red Flags</h4><ul class="space-y-1">';
              for (const f of d.red_flags) html += `<li class="text-sm text-slate-700 flex gap-2"><span class="text-rose-400 mt-0.5">●</span>${this._escHtml(f)}</li>`;
              html += '</ul></div>';
            }
            if (d.green_flags && d.green_flags.length) {
              html += '<div><h4 class="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-2">✓ Green Flags</h4><ul class="space-y-1">';
              for (const f of d.green_flags) html += `<li class="text-sm text-slate-700 flex gap-2"><span class="text-emerald-400 mt-0.5">●</span>${this._escHtml(f)}</li>`;
              html += '</ul></div>';
            }
            html += '</div>';
          }

          // 4. Scalar fields as metric cards (exclude already-shown or internal fields)
          const skipKeys = new Set(['summary','questions','red_flags','green_flags','recent_deals','capex_history','dividend_history','revenue_by_geography','key_suppliers','key_patents','technology_partnerships','innovation_areas','key_currencies','key_covenants','management_changes']);
          const scalars = Object.entries(d).filter(([k,v]) => !skipKeys.has(k) && !Array.isArray(v) && (typeof v !== 'object' || v === null));
          if (scalars.length) {
            html += '<div class="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-5">';
            for (const [k,v] of scalars) {
              const badge = k === 'valuation_verdict' ? `bg-emerald-50 border-emerald-200 text-emerald-700`
                          : k.includes('rating') || k.includes('score') ? 'bg-blue-50 border-blue-200 text-blue-700'
                          : 'bg-slate-50 border-slate-200 text-slate-800';
              html += `<div class="rounded-lg border ${badge} p-3">
                <p class="text-[10px] font-semibold uppercase tracking-wider text-slate-500 mb-1">${this._fmtKey(k)}</p>
                <p class="text-sm font-bold">${this._escHtml(String(v ?? '—'))}</p>
              </div>`;
            }
            html += '</div>';
          }

          // 5. Object fields as KV grids
          for (const [k,v] of Object.entries(d)) {
            if (skipKeys.has(k) || Array.isArray(v) || typeof v !== 'object' || v === null) continue;
            const entries = Object.entries(v);
            if (!entries.length) continue;
            html += `<div class="mb-4"><h4 class="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">${this._fmtKey(k)}</h4>
              <div class="bg-slate-50 rounded-lg p-3 grid grid-cols-2 gap-x-6 gap-y-1">`;
            for (const [ek,ev] of entries) {
              html += `<div class="flex justify-between border-b border-slate-100 py-1 col-span-1">
                <span class="text-xs text-slate-500">${this._fmtKey(ek)}</span>
                <span class="text-xs font-medium text-slate-800">${this._escHtml(String(ev ?? '—'))}</span>
              </div>`;
            }
            html += '</div></div>';
          }

          // 6. Array fields as tables (non-questions/flags)
          for (const [k,v] of Object.entries(d)) {
            if (skipKeys.has(k) || !Array.isArray(v) || !v.length) continue;
            if (typeof v[0] !== 'object') {
              // Array of strings → bullet list
              html += `<div class="mb-4"><h4 class="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">${this._fmtKey(k)}</h4>
                <ul class="list-disc list-inside space-y-1">`;
              for (const item of v) html += `<li class="text-sm text-slate-700">${this._escHtml(String(item))}</li>`;
              html += '</ul></div>';
            } else {
              // Array of objects → table
              const cols = Object.keys(v[0]);
              html += `<div class="mb-4 overflow-x-auto">
                <h4 class="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">${this._fmtKey(k)}</h4>
                <table class="w-full text-sm border-collapse">
                  <thead><tr class="text-left">`;
              for (const c of cols) html += `<th class="text-xs font-semibold text-slate-500 pb-2 pr-4 whitespace-nowrap border-b border-slate-200">${this._fmtKey(c)}</th>`;
              html += '</tr></thead><tbody>';
              for (const row of v) {
                html += '<tr class="border-b border-slate-100 hover:bg-slate-50 transition">';
                for (const c of cols) html += `<td class="py-2 pr-4 text-slate-700 align-top">${this._escHtml(String(row[c] ?? '—'))}</td>`;
                html += '</tr>';
              }
              html += '</tbody></table></div>';
            }
          }
          return html || '<p class="text-slate-400 text-sm">No structured data available.</p>';
        },
        formatResearchDate(iso) {
          if (!iso) return '—';
          try {
            const d = new Date(iso);
            return d.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }) + ' ' + d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
          } catch { return iso; }
        },
        finCurrencySymbol() { const s={INR:'₹',USD:'$',EUR:'€',GBP:'£',JPY:'¥',CNY:'¥',HKD:'HK$',SGD:'S$',AUD:'A$',CAD:'C$'}; const c=this.getSectionData('financials')?.financialCurrency; return s[c]||(c?c+' ':''); },
        isSectionLoading(section) { return !!this.perStockSectionLoading[section]; },
        fetchSectionDataIfNeeded(section) {
          if (!this.perStockSymbol) return;
          const isYf = this.yfSections.includes(section);
          const isResearch = this.researchSections.includes(section);
          if (!isYf && !isResearch) return;
          const sym = this.perStockSymbol;
          const cached = (this.perStockSectionData[sym] || {})[section];
          if (cached && !cached.error && !cached.error_not_found) return;
          this.fetchSectionData(section, false);
        },
        async fetchSectionData(section, force) {
          if (!this.perStockSymbol) return;
          const isYf = this.yfSections.includes(section);
          const isResearch = this.researchSections.includes(section);
          if (!isYf && !isResearch) return;
          const sym = this.perStockSymbol;
          if (!force && (this.perStockSectionData[sym] || {})[section] && !(this.perStockSectionData[sym][section].error)) return;
          this.perStockSectionLoading = { ...this.perStockSectionLoading, [section]: true };
          try {
            let url;
            const symMarket = (this.holdingMarkets || {})[sym] === 'US' ? 'us' : 'india';
            if (isResearch) {
              url = API + '/symbol/' + encodeURIComponent(sym) + '/research/' + section;
            } else {
              const params = new URLSearchParams({ market: symMarket });
              if (force) params.set('force', 'true');
              url = API + '/symbol/' + encodeURIComponent(sym) + '/section/' + section + '?' + params.toString();
            }
            const r = await fetch(url).then(x => x.json());
            if (!this.perStockSectionData[sym]) this.perStockSectionData[sym] = {};
            this.perStockSectionData[sym][section] = r;
          } catch (e) {
            if (!this.perStockSectionData[sym]) this.perStockSectionData[sym] = {};
            this.perStockSectionData[sym][section] = { error: e.message };
          } finally {
            this.perStockSectionLoading = { ...this.perStockSectionLoading, [section]: false };
          }
        },
        fetchMetricsHistoryIfNeeded() {
          if (!this.perStockSymbol) return;
          if (this.metricsHistory && this.metricsHistory.symbol === this.perStockSymbol) return;
          this.fetchMetricsHistory();
        },
        async fetchPriceHistory() {
          if (!this.perStockSymbol) return;
          const sym = this.perStockSymbol;
          this.priceHistory = null;
          this.priceHistoryLoading = true;
          try {
            const r = await fetch(API + '/symbol/' + encodeURIComponent(sym) + '/price/history?market=' + encodeURIComponent(this.market)).then(x => x.json());
            if (this.perStockSymbol === sym) {
              this.priceHistory = r;
              this.$nextTick(() => this.renderPriceCharts(r));
            }
          } catch(e) {
            if (this.perStockSymbol === sym) this.priceHistory = { error: e.message };
          } finally {
            this.priceHistoryLoading = false;
          }
        },
        async fetchMetricsHistory() {
          if (!this.perStockSymbol) return;
          const sym = this.perStockSymbol;
          this.metricsHistory = null;
          this.metricsHistoryLoading = true;
          try {
            const r = await fetch(API + '/symbol/' + encodeURIComponent(sym) + '/metrics/history?market=' + encodeURIComponent(this.market)).then(x => x.json());
            if (this.perStockSymbol === sym) {
              this.metricsHistory = r;
              this.$nextTick(() => this.renderMetricCharts(r));
            }
          } catch(e) {
            if (this.perStockSymbol === sym) this.metricsHistory = { error: e.message };
          } finally {
            this.metricsHistoryLoading = false;
          }
        },
        destroyChart(id) {
          const existing = Chart.getChart(id);
          if (existing) existing.destroy();
        },
        renderMetricCharts(data) {
          if (!data || data.error || !data.years) return;
          const years = data.years;
          const COLORS = {
            teal:   '#0d9488', blue: '#3b82f6', indigo: '#6366f1',
            violet: '#7c3aed', rose: '#f43f5e', amber: '#f59e0b',
            emerald:'#10b981', slate: '#64748b', sky: '#0ea5e9',
          };
          const makeLineChart = (id, datasets, opts = {}) => {
            this.destroyChart(id);
            const el = document.getElementById(id);
            if (!el) return;
            new Chart(el, {
              type: 'line',
              data: { labels: years, datasets },
              options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } }, tooltip: { mode: 'index', intersect: false } },
                scales: {
                  x: { grid: { display: false }, ticks: { font: { size: 11 } } },
                  y: { grid: { color: '#f1f5f9' }, ticks: { font: { size: 11 }, callback: opts.yFmt || (v => v != null ? v + (opts.pct ? '%' : '') : '') } }
                },
                interaction: { mode: 'nearest', axis: 'x', intersect: false },
                ...( opts.extra || {} )
              }
            });
          };
          const makeBarChart = (id, datasets, opts = {}) => {
            this.destroyChart(id);
            const el = document.getElementById(id);
            if (!el) return;
            new Chart(el, {
              type: 'bar',
              data: { labels: years, datasets },
              options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } }, tooltip: { mode: 'index', intersect: false } },
                scales: {
                  x: { grid: { display: false }, ticks: { font: { size: 11 } } },
                  y: { grid: { color: '#f1f5f9' }, ticks: { font: { size: 11 }, callback: opts.yFmt || (v => v) } }
                },
              }
            });
          };
          const ds = (label, color, data, extra = {}) => ({
            label, data,
            borderColor: color, backgroundColor: color + '22',
            borderWidth: 2, pointRadius: 4, pointHoverRadius: 6,
            tension: 0.3, fill: false,
            ...extra
          });

          // 1. Margins
          makeLineChart('chart-margins', [
            ds('Gross Margin', COLORS.teal,    data.margins?.gross),
            ds('Operating Margin', COLORS.blue, data.margins?.operating),
            ds('Net Margin', COLORS.indigo,    data.margins?.net),
          ], { pct: true });

          // 2. Returns
          makeLineChart('chart-returns', [
            ds('ROE', COLORS.violet,   data.returns?.roe),
            ds('ROA', COLORS.sky,      data.returns?.roa),
            ds('ROIC', COLORS.emerald, data.returns?.roic),
          ], { pct: true });

          // 3. Revenue & Net Income (bar)
          const scaleRev = v => v != null ? +(v / 1e9).toFixed(2) : null;
          makeBarChart('chart-revenue', [
            { label: 'Revenue (B)', data: data.revenue?.map(scaleRev), backgroundColor: COLORS.teal + 'cc', borderColor: COLORS.teal, borderWidth: 1 },
            { label: 'Net Income (B)', data: data.net_income?.map(scaleRev), backgroundColor: COLORS.indigo + 'cc', borderColor: COLORS.indigo, borderWidth: 1 },
          ], { yFmt: v => v != null ? v + 'B' : '' });

          // 4. FCF Quality
          makeLineChart('chart-fcf', [
            ds('FCF Conversion %', COLORS.emerald, data.cash_quality?.fcf_conversion),
            ds('Capex / Revenue %', COLORS.rose,   data.cash_quality?.capex_to_revenue),
            ds('R&D / Revenue %',   COLORS.amber,  data.cash_quality?.rd_to_revenue),
          ], { pct: true });

          // 5. Leverage
          makeLineChart('chart-leverage', [
            ds('Debt / Equity',       COLORS.rose,   data.leverage?.debt_to_equity),
            ds('Net Debt / EBITDA',   COLORS.amber,  data.leverage?.net_debt_to_ebitda),
            ds('Interest Coverage',   COLORS.slate,  data.leverage?.interest_coverage),
          ]);

          // 6. Valuation History
          makeLineChart('chart-valuation-hist', [
            ds('P/E',  COLORS.indigo, data.valuation_history?.pe),
            ds('P/B',  COLORS.teal,   data.valuation_history?.pb),
            ds('P/S',  COLORS.amber,  data.valuation_history?.ps),
          ], { yFmt: v => v != null ? v + 'x' : '' });
        },
        renderPriceCharts(data) {
          if (!data || data.error || !data.dates) return;
          const dates  = data.dates;
          const COLORS = { teal: '#0d9488', amber: '#f59e0b', slate: '#94a3b8', indigo: '#6366f1', rose: '#f43f5e' };

          // Thin out labels so x-axis isn't crowded — show ~12 labels
          const step = Math.max(1, Math.floor(dates.length / 12));
          const tickCallback = (val, i) => i % step === 0 ? dates[i]?.slice(0, 7) : '';

          // Chart 1: Price + 50 DMA + 200 DMA
          this.destroyChart('chart-price-dma');
          const el1 = document.getElementById('chart-price-dma');
          if (el1) {
            new Chart(el1, {
              type: 'line',
              data: {
                labels: dates,
                datasets: [
                  { label: 'Price', data: data.price, borderColor: COLORS.slate, backgroundColor: COLORS.slate + '18',
                    borderWidth: 1.5, pointRadius: 0, fill: true, tension: 0.1, order: 3 },
                  { label: '50 DMA', data: data.sma50,  borderColor: COLORS.amber, borderWidth: 2,
                    pointRadius: 0, fill: false, tension: 0.3, borderDash: [4,3], order: 2 },
                  { label: '200 DMA', data: data.sma200, borderColor: COLORS.teal,  borderWidth: 2.5,
                    pointRadius: 0, fill: false, tension: 0.3, order: 1 },
                ],
              },
              options: {
                responsive: true, maintainAspectRatio: false,
                plugins: {
                  legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } },
                  tooltip: { mode: 'index', intersect: false, callbacks: {
                    label: ctx => ctx.dataset.label + ': ' + (ctx.parsed.y != null ? ctx.parsed.y.toFixed(2) : '—')
                  }}
                },
                scales: {
                  x: { grid: { display: false }, ticks: { font: { size: 10 }, maxTicksLimit: 12, callback: tickCallback } },
                  y: { position: 'left', grid: { color: '#f1f5f9' }, ticks: { font: { size: 11 }, callback: v => v != null ? v.toFixed(0) : '' } },
                },
                interaction: { mode: 'nearest', axis: 'x', intersect: false },
              }
            });
          }

          // Chart 2: Volume bars
          this.destroyChart('chart-volume');
          const el2 = document.getElementById('chart-volume');
          if (el2) {
            // Colour volume bars: green if price up, red if down
            const volColors = data.price.map((p, i) =>
              i === 0 ? COLORS.slate + '99' : (p >= data.price[i-1] ? '#10b98166' : '#f43f5e66')
            );
            new Chart(el2, {
              type: 'bar',
              data: {
                labels: dates,
                datasets: [{
                  label: 'Volume',
                  data: data.volume,
                  backgroundColor: volColors,
                  borderWidth: 0,
                  barPercentage: 1.0,
                  categoryPercentage: 1.0,
                }],
              },
              options: {
                responsive: true, maintainAspectRatio: false,
                plugins: {
                  legend: { display: false },
                  tooltip: { mode: 'index', intersect: false, callbacks: {
                    label: ctx => 'Vol: ' + (ctx.parsed.y != null ? (ctx.parsed.y / 1e6).toFixed(2) + 'M' : '—')
                  }}
                },
                scales: {
                  x: { grid: { display: false }, ticks: { font: { size: 10 }, maxTicksLimit: 12, callback: tickCallback } },
                  y: { grid: { color: '#f1f5f9' }, ticks: { font: { size: 10 }, callback: v => v != null ? (v/1e6).toFixed(0)+'M' : '' } },
                },
              }
            });
          }
        },
        async fetchCompare() {
          if (this.compareSymbols.length < 2) { this.compareRows = []; return; }
          const syms = this.compareSymbols;
          this.loading = true;
          try {
            const r = await fetch(API + '/compare?symbols=' + encodeURIComponent(syms.join(',')) + '&market=' + encodeURIComponent(this.market)).then(r => r.json());
            this.compareRows = r.rows || [];
            if (this.compareRows.length >= 2) {
              const tryRender = (attempts) => {
                const el = document.getElementById('cmp-radar');
                if (el && el.offsetParent !== null) {
                  this.renderCmpCharts();
                } else if (attempts > 0) {
                  setTimeout(() => tryRender(attempts - 1), 200);
                }
              };
              setTimeout(() => tryRender(10), 100);
            }
          } finally { this.loading = false; }
        },
        comparePickerCommit(side, explicitSym) {
          // legacy method kept for any remaining references
          const key = side === 'A' ? 'compareA' : 'compareB';
          const query = (explicitSym || this.symbolPickerMatches(key)[0] || this.symbolPickerState[key].query || '').trim();
          if (!query) return;
          this.addCompareStock(query);
          this.symbolPickerState[key].query = query.replace('.NS','').replace('.BO','');
          this.symbolPickerState[key].open = false;
        },
        addCompareStock(sym) {
          const s = (sym || '').trim().toUpperCase();
          if (!s || this.compareSymbols.some(x => x.toUpperCase() === s)) return;
          if (this.compareSymbols.length >= 5) return;
          this.compareSymbols = [...this.compareSymbols, sym.trim()];
          this.fetchCompare();
        },
        removeCompareStock(sym) {
          this.compareSymbols = this.compareSymbols.filter(x => x.toUpperCase() !== sym.toUpperCase());
          this.fetchCompare();
        },
        _cmpCharts: {},
        renderCmpCharts() {
          if (this.compareRows.length < 2) return;
          const rows = this.compareRows;
          const COLORS = [
            'rgba(45,212,191,0.85)',
            'rgba(167,139,250,0.85)',
            'rgba(251,191,36,0.85)',
            'rgba(249,115,22,0.85)',
            'rgba(236,72,153,0.85)',
          ];
          const COLORS_BG = [
            'rgba(45,212,191,0.15)',
            'rgba(167,139,250,0.15)',
            'rgba(251,191,36,0.15)',
            'rgba(249,115,22,0.15)',
            'rgba(236,72,153,0.15)',
          ];
          const sym = row => (row.symbol||'').replace('.NS','').replace('.BO','');
          const grid = { color: 'rgba(148,163,184,0.12)' };
          const tick = { color: '#94a3b8', font: { size: 11 } };
          const legend = { labels: { color: '#cbd5e1', font: { size: 12 }, boxWidth: 12 } };
          // yfinance returns ratios as 0-1 (e.g. 0.19 = 19%); dividend_yield already in %
          const pctVal = v => v == null ? 0 : Math.abs(v) <= 1.5 ? +(v*100).toFixed(1) : +Number(v).toFixed(1);

          const destroyAll = () => {
            Object.values(this._cmpCharts).forEach(c => { try { c.destroy(); } catch(_) {} });
            this._cmpCharts = {};
            // Force-release canvas contexts so getContext('2d') doesn't return null on re-render
            ['cmp-radar','cmp-valuation','cmp-profit','cmp-growth','cmp-health'].forEach(id => {
              const c = document.getElementById(id);
              if (c && c.tagName === 'CANVAS') { c.width = c.width; }
            });
          };
          destroyAll();

          const mkBar = (id, labels, datasets, opts = {}) => {
            const el = document.getElementById(id);
            if (!el) return;
            const ctx = el.getContext('2d');
            if (!ctx) return;
            return new Chart(ctx, {
              type: 'bar',
              data: { labels, datasets },
              options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { ...legend, position: 'top' }, tooltip: { callbacks: { label: ctx => ctx.dataset.label + ': ' + ctx.parsed.y + (opts.suffix||'') } } },
                scales: {
                  x: { ticks: tick, grid },
                  y: { ticks: { ...tick, callback: v => v + (opts.suffix||'') }, grid, beginAtZero: opts.beginAtZero !== false },
                }
              }
            });
          };

          // 1. Radar — normalised 0-10 scoring on 6 dimensions
          const radarEl = document.getElementById('cmp-radar');
          if (radarEl && radarEl.getContext('2d')) {
            const norm = (v, lo, hi) => v == null ? 0 : Math.min(10, Math.max(0, (v - lo) / (hi - lo) * 10));
            const dims = ['Profitability', 'Valuation', 'Growth', 'Health', 'Momentum', 'Quality'];
            const radarDatasets = rows.map((row, i) => ({
              label: sym(row),
              data: [
                norm(pctVal(row.roe), 0, 30),
                norm(30 - (row.trailing_pe||30), 0, 30),
                norm(pctVal(row.revenue_growth), -10, 30),
                norm(row.current_ratio, 0, 3),
                norm(row['52w_change_pct']||0, -30, 50),
                norm(row.total_score||0, 0, 100),
              ],
              backgroundColor: COLORS_BG[i],
              borderColor: COLORS[i],
              borderWidth: 2,
              pointBackgroundColor: COLORS[i],
            }));
            this._cmpCharts['radar'] = new Chart(radarEl.getContext('2d'), {
              type: 'radar',
              data: { labels: dims, datasets: radarDatasets },
              options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend },
                scales: { r: { min: 0, max: 10, ticks: { stepSize: 2, color: '#64748b', font: { size: 9 }, backdropColor: 'transparent' }, grid: { color: 'rgba(148,163,184,0.15)' }, angleLines: { color: 'rgba(148,163,184,0.15)' }, pointLabels: { color: '#94a3b8', font: { size: 11 } } } }
              }
            });
          }

          // 2. Valuation multiples
          this._cmpCharts['val'] = mkBar('cmp-valuation',
            ['P/E TTM', 'P/E Fwd', 'EV/EBITDA', 'P/B', 'P/S'],
            rows.map((row, i) => ({
              label: sym(row),
              data: [row.trailing_pe, row.forward_pe, row.ev_to_ebitda, row.price_to_book, row.price_to_sales].map(v => v != null ? +v.toFixed(1) : 0),
              backgroundColor: COLORS[i], borderRadius: 4,
            })),
            { suffix: 'x' }
          );

          // 3. Profitability
          this._cmpCharts['prof'] = mkBar('cmp-profit',
            ['Gross Margin', 'EBIT Margin', 'Net Margin', 'ROE', 'ROA'],
            rows.map((row, i) => ({
              label: sym(row),
              data: [row.gross_margin, row.operating_margin, row.profit_margin||row.net_margin, row.roe, row.roa].map(pctVal),
              backgroundColor: COLORS[i], borderRadius: 4,
            })),
            { suffix: '%' }
          );

          // 4. Growth — dividend_yield already in %, others are 0-1 ratios
          const growthVal = (v, alreadyPct) => v == null ? 0 : alreadyPct ? +Number(v).toFixed(1) : +(v*100).toFixed(1);
          this._cmpCharts['growth'] = mkBar('cmp-growth',
            ['Revenue Growth', 'Earnings Growth', 'Dividend Yield', '52W Return'],
            rows.map((row, i) => ({
              label: sym(row),
              data: [growthVal(row.revenue_growth,false), growthVal(row.earnings_growth,false), growthVal(row.dividend_yield,true), growthVal(row['52w_change_pct'],false)],
              backgroundColor: COLORS[i], borderRadius: 4,
            })),
            { suffix: '%', beginAtZero: false }
          );

          // 5. Health & Market — horizontal grouped bar
          const healthEl = document.getElementById('cmp-health');
          if (healthEl && healthEl.getContext('2d')) {
            const labels = ['Current Ratio', 'Quick Ratio', 'Interest Coverage', 'Beta', 'D/E Ratio'];
            this._cmpCharts['health'] = new Chart(healthEl.getContext('2d'), {
              type: 'bar',
              data: { labels, datasets: rows.map((row, i) => ({
                label: sym(row),
                data: [row.current_ratio, row.quick_ratio, row.interest_coverage, row.beta, row.debt_to_equity||row.debt_to_equity_live].map(v => v != null ? +Number(v).toFixed(2) : 0),
                backgroundColor: COLORS[i], borderRadius: 4,
              }))},
              options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { ...legend, position: 'top' } },
                scales: { x: { ticks: tick, grid, beginAtZero: true }, y: { ticks: tick, grid } }
              }
            });
          }
        },
        compareMetricGroups() {
          return [
            { label: 'Price & Market', metrics: [
              { key: 'current_price', label: 'Current Price', fmt: 'price', dir: 'none' },
              { key: 'market_cap', label: 'Market Cap', fmt: 'cap', dir: 'none' },
              { key: '52w_change_pct', label: '52W Return', fmt: 'pct', dir: 'higher' },
              { key: 'beta', label: 'Beta', fmt: 'x2', dir: 'none' },
              { key: 'dividend_yield', label: 'Dividend Yield', fmt: 'pct', dir: 'higher' },
            ]},
            { label: 'Valuation', metrics: [
              { key: 'trailing_pe', label: 'P/E (Trailing)', fmt: 'x1', dir: 'lower' },
              { key: 'forward_pe', label: 'P/E (Forward)', fmt: 'x1', dir: 'lower' },
              { key: 'price_to_book', label: 'Price / Book', fmt: 'x2', dir: 'lower' },
              { key: 'ev_to_ebitda', label: 'EV / EBITDA', fmt: 'x1', dir: 'lower' },
            ]},
            { label: 'Profitability & Growth', metrics: [
              { key: 'profit_margin', label: 'Profit Margin', fmt: 'pct', dir: 'higher' },
              { key: 'roe', label: 'Return on Equity', fmt: 'pct', dir: 'higher' },
              { key: 'roa', label: 'Return on Assets', fmt: 'pct', dir: 'higher' },
              { key: 'revenue_growth', label: 'Revenue Growth', fmt: 'pct', dir: 'higher' },
              { key: 'earnings_growth', label: 'Earnings Growth', fmt: 'pct', dir: 'higher' },
            ]},
            { label: 'Financial Health', metrics: [
              { key: 'debt_to_equity_live', label: 'Debt / Equity', fmt: 'x2', dir: 'lower' },
              { key: 'current_ratio', label: 'Current Ratio', fmt: 'x2', dir: 'higher' },
            ]},
          ];
        },
        compareWinnerIdx(metric, rows) {
          if (!metric.better && metric.dir === 'none') return -1;
          const dir = metric.better || metric.dir;
          if (dir === 'none') return -1;
          if (!rows || rows.length < 2) return -1;
          const vals = rows.map(r => r[metric.key]);
          if (vals.every(v => v == null)) return -1;
          const defined = vals.filter(v => v != null);
          const best = dir === 'higher' ? Math.max(...defined) : Math.min(...defined);
          const winnerIdxs = vals.reduce((acc, v, i) => v === best ? [...acc, i] : acc, []);
          return winnerIdxs.length === 1 ? winnerIdxs[0] : -1; // -1 = tie or multiple equal
        },
        compareWinner(metric, a, b) {
          if (metric.dir === 'none') return 'tie';
          const va = a[metric.key]; const vb = b[metric.key];
          if (va == null && vb == null) return 'tie';
          if (va == null) return 'b';
          if (vb == null) return 'a';
          if (metric.dir === 'higher') return va > vb ? 'a' : (vb > va ? 'b' : 'tie');
          if (metric.dir === 'lower')  return va < vb ? 'a' : (vb < va ? 'b' : 'tie');
          return 'tie';
        },
        compareFormatVal(metric, row) {
          const v = row[metric.key];
          if (v == null) return '—';
          const fmt = metric.fmt;
          if (fmt === 'pct') return (v * (Math.abs(v) < 2 ? 100 : 1)).toFixed(1) + '%';
          if (fmt === 'price') return '₹' + Number(v).toLocaleString(undefined, {maximumFractionDigits: 2});
          if (fmt === 'cap') {
            if (v >= 1e12) return '₹' + (v/1e12).toFixed(1) + 'T';
            if (v >= 1e9)  return '₹' + (v/1e9).toFixed(1) + 'B';
            if (v >= 1e7)  return '₹' + (v/1e7).toFixed(0) + 'Cr';
            return '₹' + Number(v).toLocaleString();
          }
          if (fmt === 'x1') return Number(v).toFixed(1) + 'x';
          if (fmt === 'x2') return Number(v).toFixed(2);
          return String(v);
        },
        async fetchSymbolOptions() {
          const r = await fetch(API + '/portfolio-options?market=' + encodeURIComponent(this.market)).then(r => r.json());
          this.portfolioOptions = r;
        },
        syncCompareTextFromList() { this.compareSymbolsText = (this.compareSymbolsList || []).join('\n'); },
        addCompareSymbol(sym) {
          const s = (sym || '').trim();
          if (!s) return;
          const key = s.toUpperCase();
          if (this.compareSymbolsList.some(x => x.toUpperCase() === key)) return;
          this.compareSymbolsList = [...this.compareSymbolsList, s].slice(0, 10);
          this.syncCompareTextFromList();
          this.saveSettings();
          this.fetchCompare();
        },
        removeCompareSymbol(sym) {
          const key = (sym || '').toUpperCase();
          this.compareSymbolsList = this.compareSymbolsList.filter(x => x.toUpperCase() !== key);
          this.syncCompareTextFromList();
          this.saveSettings();
          this.fetchCompare();
        },
        debouncedFetchPortfolio() {
          clearTimeout(this._portfolioTimer);
          this._portfolioTimer = setTimeout(() => this.fetchPortfolioData(), 300);
        },
        async computePortfolioMissing() {
          if (!this.portfolioMissing.length) return;
          this.computeRunning = true;
          try {
            const res = await fetch(API + '/compute-sharia', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ symbols: this.portfolioMissing, max_workers: this.computeWorkers, market: this.market })
            });
            if (res.ok) {
              await this.fetchPortfolioData(); this.fetchPortfolioPrices();
              await this.fetchCounts();
              await this.fetchCacheStatus();
            }
          } catch (_) {}
          finally { this.computeRunning = false; }
        },
        async computePortfolioAll(force = false) {
          const syms = (this.personalIndexInputRows || []).map(r => r.symbol).filter(Boolean);
          if (!syms.length) return;
          this.computeRunning = true;
          try {
            const res = await fetch(API + '/compute-sharia', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ symbols: syms, max_workers: this.computeWorkers, force, market: this.market })
            });
            if (res.ok) {
              await this.fetchPortfolioData(); this.fetchPortfolioPrices();
              await this.fetchCounts();
              await this.fetchCacheStatus();
            }
          } catch (_) {}
          finally { this.computeRunning = false; }
        },
        async syncPortfolioFromTrades() {
          // Populate personalIndexInputRows from open trade positions (AVCO units + avg cost)
          try {
            const r = await fetch('/api/trades/positions');
            const d = await r.json();
            const positions = d.positions || [];
            if (!positions.length) return;
            this.personalIndexInputRows = positions.map(pos => ({
              symbol: pos.symbol,
              units: pos.units,
              price: pos.avg_cost ? Math.round(pos.avg_cost * 100) / 100 : '',
              market: (this.holdingMarkets || {})[pos.symbol] || 'IN',
            }));
            // Also update the text backing store
            this.personalIndexHoldingsText = positions
              .map(pos => `${pos.symbol} ${pos.units} ${pos.avg_cost ? Math.round(pos.avg_cost * 100) / 100 : ''}`)
              .join('\n');
          } catch(_) {}
        },
        async fetchPortfolioPrices() {
          // Silently fetch live prices via the analyze endpoint — populates personalIndexHoldingsRows
          const text = this.serializePersonalIndexRows('units');
          if (!text.trim()) return;
          this.portfolioPricesLoading = true;
          try {
            const res = await fetch(API + '/personal-index/analyze', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ holdings_text: text, benchmark: 'nifty50', sip_amount: 0, strict_no_sell: true, max_buy_suggestions: 0 })
            });
            if (res.ok) {
              const data = await res.json();
              const rows = data.holdings || [];
              // Fetch prices for US symbols not handled by the India-only analyze endpoint
              const usSymbols = (this.personalIndexInputRows || [])
                .filter(r => (this.holdingMarkets || {})[r.symbol] === 'US')
                .map(r => r.symbol);
              if (usSymbols.length) {
                const priceResults = await Promise.allSettled(
                  usSymbols.map(sym =>
                    fetch(`${API}/symbol/${encodeURIComponent(sym)}/section/market?market=us`)
                      .then(r => r.json())
                      .then(d => ({ symbol: sym, current_price: d.currentPrice ?? null }))
                      .catch(() => ({ symbol: sym, current_price: null }))
                  )
                );
                for (const result of priceResults) {
                  if (result.status === 'fulfilled' && result.value.current_price != null) {
                    const existing = rows.find(r => r.symbol === result.value.symbol);
                    if (existing) {
                      existing.current_price = result.value.current_price;
                    } else {
                      const inputRow = (this.personalIndexInputRows || []).find(r => r.symbol === result.value.symbol);
                      rows.push({ symbol: result.value.symbol, current_price: result.value.current_price, units: inputRow?.units ?? 0 });
                    }
                  }
                }
              }
              this.personalIndexHoldingsRows = rows;
              // Auto-load replacements for non-Sharia holdings
              this.$nextTick(() => this.autoLoadReplacements());
            }
          } catch (_) {}
          finally { this.portfolioPricesLoading = false; }
          // Run policy gap analysis in parallel — powers Diagnosis + Prescription sections
          this.fetchPolicyAnalysis();
        },
        async fetchPolicyAnalysis() {
          const holdings = (this.personalIndexInputRows || [])
            .filter(r => r.symbol)
            .map(r => ({ symbol: r.symbol, units: parseFloat(r.units) || 0, price: parseFloat(r.price) || null }));
          if (!holdings.length) return;
          this.policyAnalysisLoading = true;
          this.policyAnalysisError = '';
          try {
            const res = await fetch(API + '/portfolio/policy-analysis', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ holdings, market: this.market || 'india' })
            });
            const data = await res.json();
            if (data.error) { this.policyAnalysisError = data.error; return; }
            this.policyAnalysis = data;
            this.fetchDeploymentScenarios();
          } catch(e) { this.policyAnalysisError = e.message; }
          finally { this.policyAnalysisLoading = false; }
        },
        async fetchDeploymentScenarios() {
          const holdings = (this.personalIndexInputRows || [])
            .filter(r => r.symbol)
            .map(r => ({ symbol: r.symbol, units: parseFloat(r.units) || 0, price: parseFloat(r.price) || null }));
          if (!holdings.length) return;
          this.deploymentScenariosLoading = true;
          try {
            const res = await fetch(API + '/portfolio/deployment-scenarios', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ holdings, market: this.market || 'india' })
            });
            const data = await res.json();
            if (!data.error) this.deploymentScenariosData = data.scenarios || [];
          } catch(_) {}
          finally { this.deploymentScenariosLoading = false; }
        },
        async autoLoadReplacements() {
          const nonSharia = this.nonShariaHoldings();
          for (const h of nonSharia) {
            if (!h._loaded && !h._loading) await this.loadReplacements(h);
          }
        },
        async fetchPortfolioData() {
          const raw = (this.personalIndexInputRows || []).map(r => r.symbol).filter(Boolean);
          if (!raw.length) return;
          this.loading = true;
          try {
            const r = await fetch(API + '/portfolio-data', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ symbols: raw, period: 'All periods' }) }).then(r => r.json());
            this.portfolioPivot = r.pivot || [];
            this.portfolioRows = r.rows || [];
            this.portfolioMissing = r.missing || [];
            // Group rows by symbol
            const bySymbol = {};
            for (const row of this.portfolioRows) {
              const sym = row.symbol || 'Unknown';
              if (!bySymbol[sym]) bySymbol[sym] = [];
              bySymbol[sym].push(row);
            }
            this.portfolioRowsBySymbol = bySymbol;
            const pivotColOrder = r.pivot_columns ? ['symbol'].concat(r.pivot_columns) : null;
            // Exclude symbol/name from per-symbol tables since they're in the header
            const symTableCols = (this.portfolioRows[0] ? Object.keys(this.portfolioRows[0]) : []).filter(k => k !== 'symbol' && k !== 'name');
            this.$nextTick(() => {
              if (this.page === 'portfolio') {
                if (this.portfolioPivot.length) this.initTable('portfolio_pivot', 'portfolio-pivot-table', this.portfolioPivot, { columnOrder: pivotColOrder });
                for (const sym of Object.keys(bySymbol)) {
                  const elId = 'portfolio-sym-table-' + sym.replace(/\./g, '-');
                  this.initTable('portfolio_sym_' + sym, elId, bySymbol[sym], {
                    columnOrder: symTableCols,
                    pagination: false,
                  });
                }
              }
            });
          } finally { this.loading = false; }
        },
        async fetchWatchlist() { const syms = (this.watchlistText || '').split(/[\s,]+/).filter(Boolean); if (!syms.length) { this.watchlistRows = []; return; } this.loading = true; try { const r = await fetch(API + '/compare?symbols=' + encodeURIComponent(syms.join(',')) + '&market=' + encodeURIComponent(this.market)).then(r => r.json()); this.watchlistRows = r.rows || []; this.$nextTick(() => { if (this.page === 'watchlist' && this.watchlistRows.length) this.initTableWithColumns('watchlist'); }); } finally { this.loading = false; } },
        async runCompute() {
          const r = await fetch(API + '/symbols-missing?limit=' + (this.computeN || 0)).then(r => r.json());
          const toFetch = (this.computeN && this.computeN > 0) ? (r.symbols || []).slice(0, this.computeN) : (r.symbols || []);
          if (!toFetch.length) { this.computeMessage = 'Choose N > 0.'; this.computeError = true; return; }
          this.computeRunning = true; this.computeMessage = ''; this.computeError = false;
          try {
            const res = await fetch(API + '/compute-sharia', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ symbols: toFetch, max_workers: this.computeWorkers, market: this.market }) });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) { this.computeMessage = data.detail || res.statusText; this.computeError = true; return; }
            this.computeMessage = 'Computed ' + (data.computed || 0) + ' symbols.';
            await this.fetchReportPeriods(); await this.fetchCounts(); await this.fetchSymbolsMissing();
          } catch (e) { this.computeMessage = e.message || 'Failed'; this.computeError = true; }
          finally { this.computeRunning = false; }
        },
        async fetchSymbolsMissing() { const r = await fetch(API + '/symbols-missing?limit=5000&period=' + encodeURIComponent(this.period) + '&market=' + encodeURIComponent(this.market)).then(r => r.json()); this.symbolsMissing = r; },
        async fetchCacheStatus() {
          try {
            const r = await fetch(API + '/cache-status?market=' + encodeURIComponent(this.market)).then(x => x.json());
            this.cacheStatus = r;
          } catch (_) { this.cacheStatus = null; }
        }
      };
    }
  </script>
