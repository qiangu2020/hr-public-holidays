import asia from "./locales/asia-en.json";
import asean from "./locales/asean-en.json";
import global from "./locales/global-en.json";

const ENGLISH_DATA = { ...asia, ...asean, ...global };
const STORAGE_KEY = "holiday-atlas.language";
const COPY = {
  "zh-CN": {
    title: "Holiday Atlas · 地区假期月历",
    subtitle: "官方假期月历",
    language: "界面语言",
    official: "官方来源",
    fullPage: "打开完整页面",
    heroTitle: "一个月历，协调各地休假。",
    heroText: "筛选地区、切换月份，按需查看假期与官方依据。",
    regions: "地区筛选",
    selected: "已选 {count}/{total}",
    allRegions: "全部地区",
    all: "全选",
    focus: "吉隆坡 / 香港",
    clear: "清空",
    done: "完成筛选",
    filterLabel: "筛选地区，可多选",
    filterHint:
      "KL 为吉隆坡适用假期；MY 为联邦／跨州参考。两种马来西亚范围互斥选择，避免重复计数。",
    malaysiaReference: "马来西亚·参考 (MY)",
    kualaLumpur: "马来西亚·吉隆坡 (KL)",
    previous: "上个月",
    next: "下个月",
    thisMonth: "本月",
    year: "年份",
    month: "月份",
    yearOption: "{year} 年",
    monthOption: "{month} 月",
    stats: "{days} 个假期日 · {events} 项安排",
    calendarLabel: "{month}地区假期",
    dayLabel: "{date}，{weekday}，{count} 项地区假期。{regions}。查看明细",
    weekdays: ["一", "二", "三", "四", "五", "六", "日"],
    today: "今天",
    holidays: "假期",
    dayHint: "点日期看明细",
    agenda: "假期明细",
    monthHolidays: "本月假期",
    wholeMonth: "查看整月",
    noRegions: "尚未选择地区。",
    unavailable: "{regions}：{year} 年官方数据尚未收录，不能视为无假期。",
    stale: "页面构建已超过 48 小时，请查阅官方最新公告。",
    syncFailed: "{region}：同步失败，{error}",
    noRecords: "暂无可展示的记录",
    startRegion: "从一个地区开始",
    empty: "已收录地区在此期间没有假期记录。",
    emptySelection: "展开地区筛选，选择想查看的地区。",
    emptyYear: "该年份的官方数据尚未收录，不代表没有假期。",
    emptyPartial: "已收录地区无假期记录；尚未收录的地区不计入此结论。",
    source: "官方依据",
    public: "公共假期",
    bank: "银行假期",
    government: "政府机关假期",
    optional: "可选假期",
    scopeTitle: "适用范围与数据说明",
    scopeIntro: "为协作计划提供参考，不替代公司休假制度。",
    scopeBody:
      "各地适用人群、邦州和补休规则可能不同。银行、政府机关与可选假期单独标注；宗教节日和临时假期以当地政府最终公告为准。",
    snapshotBody:
      "可读取的官方接口自动获取；部分 PDF / 公告为人工核对快照，核对日期见来源说明。页面构建时间不代表所有公告已重新核对。",
    sources: "官方来源与收录范围",
    sourceCount: "{count} 个地区",
    coverage: "收录年份：{years}",
    sourceTranslation: "英文说明为界面翻译，原始官方文件以链接内容为准。",
    built: "页面构建 {date} · UTC+8",
    standalone: "独立静态站点 · 无需 HR 服务器",
    loadTitle: "暂时无法载入假期",
    loadBody: "无法载入不代表没有假期，请稍后重试。",
    reload: "重新载入",
    loading: "正在载入官方假期月历…",
    formatError: "官方假期数据格式异常",
  },
  en: {
    title: "Holiday Atlas · Regional holiday calendar",
    subtitle: "Official holiday calendar",
    language: "Interface language",
    official: "Official sources",
    fullPage: "Open full page",
    heroTitle: "Every region, one calendar.",
    heroText:
      "Filter regions, browse months, and check holidays against official sources.",
    regions: "Regions",
    selected: "Selected {count}/{total}",
    allRegions: "All regions",
    all: "Select all",
    focus: "Kuala Lumpur / Hong Kong",
    clear: "Clear",
    done: "Done",
    filterLabel: "Filter regions; select more than one",
    filterHint:
      "KL covers Kuala Lumpur; MY is a federal/cross-state reference. Choose one Malaysian scope at a time to avoid duplicates.",
    malaysiaReference: "Malaysia · reference (MY)",
    kualaLumpur: "Malaysia · Kuala Lumpur (KL)",
    previous: "Previous month",
    next: "Next month",
    thisMonth: "This month",
    year: "Year",
    month: "Month",
    yearOption: "{year}",
    monthOption: "{month}",
    stats: "Holiday dates: {days} · Entries: {events}",
    calendarLabel: "{month} regional holidays",
    dayLabel:
      "{date}, {weekday}, {count} regional holiday entries. {regions}. View details",
    weekdays: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    today: "Today",
    holidays: "Holidays",
    dayHint: "Select a date for details",
    agenda: "Holiday details",
    monthHolidays: "This month's holidays",
    wholeMonth: "Whole month",
    noRegions: "No regions selected.",
    unavailable:
      "{year} official dates are not yet included for {regions}. This does not mean there are no holidays.",
    stale:
      "This page was built over 48 hours ago. Check the latest official notices.",
    syncFailed: "{region}: sync failed, {error}",
    noRecords: "No records to show",
    startRegion: "Start with a region",
    empty: "No holiday records for covered regions in this period.",
    emptySelection: "Open Regions and select the places you want to see.",
    emptyYear:
      "Official data for this year is not yet included. This does not mean there are no holidays.",
    emptyPartial:
      "No records for covered regions; regions with unavailable data are excluded from this conclusion.",
    source: "Official source",
    public: "Public holiday",
    bank: "Bank holiday",
    government: "Government offices",
    optional: "Optional holiday",
    scopeTitle: "Scope & data notes",
    scopeIntro:
      "For coordination, not a replacement for your company's leave policy.",
    scopeBody:
      "Coverage, state rules and substitute-day rules vary. Bank, government-office and optional holidays are marked separately. Religious and ad hoc dates remain subject to final government notices.",
    snapshotBody:
      "Readable official interfaces are fetched automatically. Some PDFs and notices are manually checked snapshots; see their verification dates below. The page build time is not a recheck date for every notice.",
    sources: "Official sources & coverage",
    sourceCount: "Regions: {count}",
    coverage: "Years included: {years}",
    sourceTranslation:
      "English descriptions are interface translations. Linked official documents remain the authoritative originals.",
    built: "Built {date} · UTC+8",
    standalone: "Standalone static site · No HR server required",
    loadTitle: "Holidays are temporarily unavailable",
    loadBody:
      "A loading failure does not mean there are no holidays. Please try again.",
    reload: "Reload",
    loading: "Loading the official holiday calendar…",
    formatError: "Invalid official holiday dataset",
  },
};

export function initialLanguage() {
  const fromUrl = new URLSearchParams(window.location.search).get("lang");
  if (fromUrl === "en" || fromUrl === "zh-CN") return fromUrl;
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "en" || saved === "zh-CN") return saved;
  } catch {
    // Embedded clients may disable storage; switching still works in this session.
  }
  return "zh-CN";
}

export function saveLanguage(language) {
  try {
    localStorage.setItem(STORAGE_KEY, language);
  } catch {
    // A restricted webview must not prevent the interface from switching.
  }
}

export function copy(language, key, values = {}) {
  const text = COPY[language][key];
  return typeof text === "string"
    ? text.replace(/\{(\w+)\}/g, (_, name) => String(values[name]))
    : text;
}

export function dataText(text, language) {
  return language === "en" ? (ENGLISH_DATA[text] ?? text) : text;
}

export function regionName(region, language) {
  return language === "en" ? region.name_en : region.name;
}

export function eventName(event, language) {
  return language === "en"
    ? event.name_en || dataText(event.name, language)
    : event.name;
}

export function formatDate(date, language, options) {
  return new Intl.DateTimeFormat(language === "en" ? "en-GB" : "zh-CN", {
    ...options,
    timeZone: "UTC",
  }).format(new Date(`${date}T00:00:00Z`));
}
