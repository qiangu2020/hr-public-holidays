import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Button, Card, Chip, Spinner } from "@heroui/react";
import "./styles.css";
import {
  copy,
  dataText,
  eventName,
  formatDate,
  initialLanguage,
  regionName,
  saveLanguage,
} from "./i18n";

const PALETTE = [
  "#6761c5",
  "#8b63b7",
  "#dc8054",
  "#518ba1",
  "#4e967e",
  "#b56683",
  "#a7833d",
  "#62814e",
  "#9a6c55",
  "#5173bb",
  "#857547",
  "#b36565",
  "#6b7b8e",
  "#8a6dab",
  "#488c87",
];
const SHORT = { "MY-KUL": "KL" };
const dateParts = Object.fromEntries(
  new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Singapore",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  })
    .formatToParts(new Date())
    .map((p) => [p.type, p.value]),
);
const TODAY = `${dateParts.year}-${dateParts.month}-${dateParts.day}`;
const CURRENT = { year: +dateParts.year, month: +dateParts.month };
const keyFor = (year, month, day) =>
  `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
const safeUrl = (url) => (/^https?:\/\//.test(url) ? url : undefined);

function Icon({ name, ...props }) {
  const paths = {
    calendar: (
      <>
        <rect x="3" y="5" width="18" height="16" rx="4" />
        <path d="M7 3v4m10-4v4M3 11h18m-13 4h1m6 0h1m-8 3h1" />
      </>
    ),
    globe: (
      <>
        <circle cx="12" cy="12" r="9" />
        <ellipse cx="12" cy="12" rx="4" ry="9" />
        <path d="M3 12h18" />
      </>
    ),
    left: <path d="m14 6-6 6 6 6" />,
    right: <path d="m10 6 6 6-6 6" />,
    check: <path d="m5 12 4 4L19 6" />,
    filter: (
      <>
        <path d="M4 7h16M7 12h10m-7 5h4" />
        <circle cx="8" cy="7" r="2" fill="currentColor" />
      </>
    ),
    arrow: (
      <>
        <path d="M7 17 17 7M7 7h10v10" />
      </>
    ),
    info: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 11v6m0-10v1" />
      </>
    ),
  };
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {paths[name]}
    </svg>
  );
}

function SourceLink({ url, children }) {
  return (
    <a href={safeUrl(url)} target="_blank" rel="noopener noreferrer">
      {children}
      <Icon name="arrow" width="12" height="12" />
    </a>
  );
}

function PageHeader({ language, onLanguageChange }) {
  const t = (key) => copy(language, key);
  const fullPage = new URL(window.location.href);
  fullPage.searchParams.set("lang", language);
  return (
    <header className="page-header">
      <div className="brand">
        <span className="brand-mark">
          <Icon name="calendar" width="21" height="21" />
        </span>
        <span>
          HOLIDAY ATLAS<small>{t("subtitle")}</small>
        </span>
      </div>
      <div className="header-actions">
        <Chip
          color="success"
          variant="soft"
          size="sm"
          className="official-chip"
        >
          <span className="live-dot" />
          <Chip.Label>{t("official")}</Chip.Label>
        </Chip>
        <select
          className="language-select"
          aria-label={t("language")}
          value={language}
          onChange={(event) => onLanguageChange(event.target.value)}
        >
          <option value="zh-CN">中文</option>
          <option value="en">English</option>
        </select>
        <a
          className="full-page"
          href={fullPage.href}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={t("fullPage")}
          title={t("fullPage")}
        >
          <Icon name="arrow" />
        </a>
      </div>
    </header>
  );
}

function HolidayCalendar({ data, language, onLanguageChange }) {
  const [view, setView] = useState(CURRENT);
  const [selected, setSelected] = useState(
    () => new Set(data.regions.filter((r) => r.id !== "MY").map((r) => r.id)),
  );
  const [selectedDay, setSelectedDay] = useState(null);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const t = (key, values) => copy(language, key, values);
  const nameOf = (region) =>
    region.id === "MY"
      ? t("malaysiaReference")
      : region.id === "MY-KUL"
        ? t("kualaLumpur")
        : regionName(region, language);
  const { year, month } = view;
  const regions = useMemo(
    () =>
      data.regions.map((r, i) => ({
        ...r,
        color: PALETTE[i % PALETTE.length],
      })),
    [data],
  );
  const active = regions.filter((r) => selected.has(r.id));
  const locationCount = regions.filter((r) => r.id !== "MY").length;
  const unavailable = active.filter((r) => !r.years.includes(year));
  const years = useMemo(() => {
    const values = data.regions.flatMap((r) => r.years);
    const min = Math.min(...values, CURRENT.year);
    const max = Math.max(...values, CURRENT.year + 1);
    return Array.from({ length: max - min + 1 }, (_, i) => min + i);
  }, [data]);
  const events = useMemo(
    () =>
      regions
        .filter((r) => selected.has(r.id) && r.years.includes(year))
        .flatMap((region) =>
          region.events
            .filter((e) =>
              e.date.startsWith(`${year}-${String(month).padStart(2, "0")}-`),
            )
            .map((e) => ({ ...e, region })),
        )
        .sort(
          (a, b) =>
            a.date.localeCompare(b.date) ||
            a.region.id.localeCompare(b.region.id),
        ),
    [regions, selected, year, month],
  );
  const byDay = useMemo(() => {
    const map = new Map();
    for (const event of events) {
      if (!map.has(event.date)) map.set(event.date, []);
      map.get(event.date).push(event);
    }
    return map;
  }, [events]);
  const visible = selectedDay
    ? events.filter((e) => e.date === selectedDay)
    : events;
  const grouped = new Map();
  for (const event of visible) {
    if (!grouped.has(event.date)) grouped.set(event.date, []);
    grouped.get(event.date).push(event);
  }
  const offset = (new Date(Date.UTC(year, month - 1, 1)).getUTCDay() + 6) % 7;
  const days = new Date(Date.UTC(year, month, 0)).getUTCDate();
  const cells = Array.from(
    { length: Math.ceil((offset + days) / 7) * 7 },
    (_, index) =>
      index >= offset && index < offset + days ? index - offset + 1 : null,
  );
  const monthTitle = formatDate(keyFor(year, month, 1), language, {
    year: "numeric",
    month: "long",
  });
  const updated = new Intl.DateTimeFormat(
    language === "en" ? "en-GB" : "zh-CN",
    {
      timeZone: "Asia/Singapore",
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(new Date(data.updated_at));
  const stale = Date.now() - Date.parse(data.updated_at) > 48 * 3600000;
  const selectionPreview =
    active.length === locationCount
      ? t("allRegions")
      : active.slice(0, 2).map(nameOf).join(" / ") +
        (active.length > 2 ? ` +${active.length - 2}` : "");
  function changeView(next) {
    setView(next);
    setSelectedDay(null);
  }
  function navigate(delta) {
    const next = new Date(Date.UTC(year, month - 1 + delta, 1));
    const nextYear = next.getUTCFullYear();
    if (nextYear >= years[0] && nextYear <= years.at(-1))
      changeView({ year: nextYear, month: next.getUTCMonth() + 1 });
  }
  function toggle(id) {
    setSelected((previous) => {
      const next = new Set(previous);
      if (next.has(id)) next.delete(id);
      else {
        if (id === "MY") next.delete("MY-KUL");
        if (id === "MY-KUL") next.delete("MY");
        next.add(id);
      }
      return next;
    });
    setSelectedDay(null);
  }
  function preset(ids) {
    const next = new Set(ids);
    if (next.has("MY-KUL")) next.delete("MY");
    setSelected(next);
    setSelectedDay(null);
  }
  let emptyMessage = t("empty");
  if (!active.length) emptyMessage = t("emptySelection");
  else if (unavailable.length === active.length) emptyMessage = t("emptyYear");
  else if (unavailable.length) emptyMessage = t("emptyPartial");
  return (
    <main className="app-shell">
      <PageHeader language={language} onLanguageChange={onLanguageChange} />
      <section className="intro">
        <div className="eyebrow">ONE CALENDAR, EVERY REGION</div>
        <h1>{t("heroTitle")}</h1>
        <p>{t("heroText")}</p>
      </section>
      <details
        className="region-filter"
        open={filtersOpen}
        onToggle={(event) => setFiltersOpen(event.currentTarget.open)}
      >
        <summary>
          <Icon name="filter" />
          <strong>{t("regions")}</strong>
          <span className="selection-count">
            {t("selected", { count: selected.size, total: locationCount })}
          </span>
          <span className="selection-preview">{selectionPreview}</span>
          <Icon
            name="right"
            className="filter-chevron"
            width="15"
            height="15"
          />
        </summary>
        <div className="filter-body">
          <div className="presets">
            <Button
              size="sm"
              variant="ghost"
              onPress={() => preset(regions.map((r) => r.id))}
            >
              {t("all")}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onPress={() => preset(["MY-KUL", "HK"])}
            >
              {t("focus")}
            </Button>
            <Button size="sm" variant="ghost" onPress={() => preset([])}>
              {t("clear")}
            </Button>
          </div>
          <div className="region-options" aria-label={t("filterLabel")}>
            {regions.map((region) => (
              <Button
                key={region.id}
                size="sm"
                variant={selected.has(region.id) ? "secondary" : "outline"}
                className={`region-option ${selected.has(region.id) ? "is-active" : ""}`}
                style={{ "--region-color": region.color }}
                aria-pressed={selected.has(region.id)}
                onPress={() => toggle(region.id)}
              >
                <span className="region-dot" />
                {nameOf(region)}
                {selected.has(region.id) && (
                  <Icon name="check" width="13" height="13" />
                )}
              </Button>
            ))}
          </div>
          <div className="filter-footer">
            <p className="filter-hint">{t("filterHint")}</p>
            <Button
              size="sm"
              variant="primary"
              onPress={() => setFiltersOpen(false)}
            >
              {t("done")}
            </Button>
          </div>
        </div>
      </details>
      <div className="data-notices" role="status">
        {!active.length && <p>{t("noRegions")}</p>}
        {unavailable.length > 0 && (
          <p>
            <Icon name="info" />
            {t("unavailable", {
              regions: unavailable.map(nameOf).join(", "),
              year,
            })}
          </p>
        )}
        {stale && <p>{t("stale")}</p>}
        {(data.errors || []).map((error, i) => (
          <p key={i}>{t("syncFailed", error)}</p>
        ))}
      </div>
      <div className="workspace">
        <Card className="calendar-card">
          <Card.Header className="calendar-toolbar">
            <h2 className="sr-only">{monthTitle}</h2>
            <div className="date-selects">
              <select
                aria-label={t("year")}
                value={year}
                onChange={(e) => changeView({ year: +e.target.value, month })}
              >
                {years.map((y) => (
                  <option key={y} value={y}>
                    {t("yearOption", { year: y })}
                  </option>
                ))}
              </select>
              <select
                aria-label={t("month")}
                value={month}
                onChange={(e) => changeView({ year, month: +e.target.value })}
              >
                {Array.from({ length: 12 }, (_, i) => (
                  <option key={i} value={i + 1}>
                    {language === "en"
                      ? formatDate(keyFor(year, i + 1, 1), language, {
                          month: "long",
                        })
                      : t("monthOption", { month: i + 1 })}
                  </option>
                ))}
              </select>
            </div>
            <div className="month-actions">
              <Button
                isIconOnly
                size="sm"
                variant="ghost"
                aria-label={t("previous")}
                isDisabled={year === years[0] && month === 1}
                onPress={() => navigate(-1)}
              >
                <Icon name="left" />
              </Button>
              <Button
                isIconOnly
                size="sm"
                variant="ghost"
                aria-label={t("next")}
                isDisabled={year === years.at(-1) && month === 12}
                onPress={() => navigate(1)}
              >
                <Icon name="right" />
              </Button>
            </div>
          </Card.Header>
          <Card.Content className="calendar-content">
            <div className="calendar-subnav">
              <span>
                {t("stats", { days: byDay.size, events: events.length })}
              </span>
              <Button
                size="sm"
                variant="ghost"
                onPress={() => changeView(CURRENT)}
              >
                {t("thisMonth")}
              </Button>
            </div>
            <table
              className="month-grid"
              aria-label={t("calendarLabel", { month: monthTitle })}
            >
              <thead>
                <tr>
                  {t("weekdays").map((d, i) => (
                    <th key={d} scope="col" className={i > 4 ? "weekend" : ""}>
                      {d}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Array.from({ length: cells.length / 7 }, (_, row) => (
                  <tr key={row}>
                    {cells.slice(row * 7, row * 7 + 7).map((day, col) => {
                      if (!day)
                        return (
                          <td key={`blank-${col}`} className="blank-day" />
                        );
                      const key = keyFor(year, month, day);
                      const items = byDay.get(key) || [];
                      const dayRegions = [
                        ...new Map(
                          items.map((e) => [e.region.id, e.region]),
                        ).values(),
                      ];
                      const label = t("dayLabel", {
                        date: key,
                        weekday: formatDate(key, language, { weekday: "long" }),
                        count: items.length,
                        regions: dayRegions.map(nameOf).join(", "),
                      });
                      return (
                        <td key={key}>
                          <button
                            className={`calendar-day ${items.length ? "has-holidays" : ""} ${selectedDay === key ? "selected-day" : ""} ${TODAY === key ? "today" : ""}`}
                            aria-label={label}
                            title={label}
                            aria-pressed={selectedDay === key}
                            aria-current={TODAY === key ? "date" : undefined}
                            onClick={() =>
                              setSelectedDay(selectedDay === key ? null : key)
                            }
                          >
                            <span
                              className={`day-number ${col > 4 ? "weekend" : ""}`}
                            >
                              {day}
                            </span>
                            <span className="cell-codes" aria-hidden="true">
                              {dayRegions
                                .slice(0, dayRegions.length > 3 ? 2 : 3)
                                .map((region) => (
                                  <b
                                    key={region.id}
                                    style={{ "--region-color": region.color }}
                                  >
                                    {SHORT[region.id] || region.id}
                                  </b>
                                ))}
                              {dayRegions.length > 3 && (
                                <small>+{dayRegions.length - 2}</small>
                              )}
                            </span>
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </Card.Content>
          <Card.Footer className="calendar-legend">
            <span>
              <i className="today-key" />
              {t("today")}
            </span>
            <span>
              <i className="holiday-key" />
              {t("holidays")}
            </span>
            <span className="legend-tip">{t("dayHint")}</span>
          </Card.Footer>
        </Card>
        <section className="agenda" aria-label={t("agenda")}>
          <div className="agenda-heading">
            <h2>
              {selectedDay
                ? formatDate(selectedDay, language, {
                    month: "long",
                    day: "numeric",
                  })
                : t("monthHolidays")}
              <Chip size="sm" variant="soft">
                {visible.length}
              </Chip>
            </h2>
            {selectedDay && (
              <Button
                size="sm"
                variant="ghost"
                onPress={() => setSelectedDay(null)}
              >
                {t("wholeMonth")}
              </Button>
            )}
          </div>
          {!visible.length && (
            <Card className="empty-state">
              <Icon name="calendar" width="26" height="26" />
              <h3>{active.length ? t("noRecords") : t("startRegion")}</h3>
              <p>{emptyMessage}</p>
            </Card>
          )}
          <div className="agenda-days">
            {[...grouped].map(([date, items]) => (
              <section key={date} className="agenda-day">
                <div className="agenda-date">
                  <strong>
                    {formatDate(date, language, {
                      month: "short",
                      day: "numeric",
                    })}
                  </strong>
                  <span>{formatDate(date, language, { weekday: "long" })}</span>
                  <i />
                </div>
                {items.map((event, index) => (
                  <details
                    key={`${event.region.id}-${index}`}
                    className="holiday-card"
                    style={{ "--region-color": event.region.color }}
                  >
                    <summary>
                      <div className="event-heading">
                        <div className="event-top">
                          <span className="event-region">
                            <span className="region-dot" />
                            {nameOf(event.region)}
                          </span>
                          {event.kind !== "public" && (
                            <Chip size="sm" color="warning" variant="soft">
                              {t(event.kind)}
                            </Chip>
                          )}
                        </div>
                        <h3>{eventName(event, language)}</h3>
                      </div>
                      <Icon
                        name="right"
                        className="event-chevron"
                        width="15"
                        height="15"
                      />
                    </summary>
                    <div className="event-details">
                      {language !== "en" &&
                        event.name_en &&
                        event.name_en !== event.name && (
                          <p className="event-english">{event.name_en}</p>
                        )}
                      <p className="event-scope">
                        {dataText(event.scope, language)}
                      </p>
                      {event.note && (
                        <p className="event-note">
                          {dataText(event.note, language)}
                        </p>
                      )}
                      <SourceLink url={event.source_url}>
                        {t("source")}
                      </SourceLink>
                    </div>
                  </details>
                ))}
              </section>
            ))}
          </div>
        </section>
      </div>
      <details className="scope-note">
        <summary>
          <Icon name="info" />
          <strong>{t("scopeTitle")}</strong>
          <span>+</span>
        </summary>
        <div>
          <strong>{t("scopeIntro")}</strong>
          <p>{t("scopeBody")}</p>
          <p>{t("snapshotBody")}</p>
        </div>
      </details>
      <details className="sources">
        <summary>
          <span>
            <Icon name="globe" />
            {t("sources")}
          </span>
          <span>
            {t("sourceCount", { count: active.length })}
            <span className="summary-plus">+</span>
          </span>
        </summary>
        <div className="source-grid">
          {active.map((region) => (
            <section key={region.id} className="source-region">
              <h3>
                <span
                  className="region-dot"
                  style={{ "--region-color": region.color }}
                />
                {nameOf(region)}
              </h3>
              <p>{dataText(region.scope, language)}</p>
              <p>{t("coverage", { years: region.years.join(", ") })}</p>
              {region.sources.map((source, i) => (
                <SourceLink key={i} url={source.url}>
                  {dataText(source.name, language)} ·{" "}
                  {dataText(source.format, language)}
                </SourceLink>
              ))}
              <ul>
                {(region.notes || []).map((note, i) => (
                  <li key={i}>{dataText(note, language)}</li>
                ))}
              </ul>
            </section>
          ))}
        </div>
        {language === "en" && (
          <p className="source-translation">{t("sourceTranslation")}</p>
        )}
      </details>
      <footer>
        <span>{t("standalone")}</span>
        <span>{t("built", { date: updated })}</span>
      </footer>
    </main>
  );
}

function App() {
  const [state, setState] = useState({ data: null, error: null });
  const [language, setLanguage] = useState(initialLanguage);
  const t = (key) => copy(language, key);
  useEffect(() => {
    document.documentElement.lang = language;
    document.title = t("title");
    saveLanguage(language);
    const url = new URL(window.location.href);
    if (
      url.searchParams.has("lang") &&
      url.searchParams.get("lang") !== language
    ) {
      url.searchParams.set("lang", language);
      window.history.replaceState(null, "", url.href);
    }
  }, [language]);
  useEffect(() => {
    const controller = new AbortController();
    fetch(`${import.meta.env.BASE_URL}data/holidays.json`, {
      cache: "no-cache",
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((data) => {
        if (
          !Array.isArray(data.regions) ||
          !data.regions.length ||
          !Number.isFinite(Date.parse(data.updated_at))
        )
          throw new Error("DATA_FORMAT");
        setState({ data, error: null });
      })
      .catch((error) => {
        if (error.name !== "AbortError")
          setState({ data: null, error: error.message });
      });
    return () => controller.abort();
  }, []);
  if (state.error)
    return (
      <main className="app-shell">
        <PageHeader language={language} onLanguageChange={setLanguage} />
        <div className="loading-screen">
          <Card className="load-card">
            <Icon name="info" width="30" height="30" />
            <h1>{t("loadTitle")}</h1>
            <p>{t("loadBody")}</p>
            <p className="muted">
              {state.error === "DATA_FORMAT" ? t("formatError") : state.error}
            </p>
            <Button onPress={() => window.location.reload()}>
              {t("reload")}
            </Button>
          </Card>
        </div>
      </main>
    );
  if (!state.data)
    return (
      <main className="app-shell">
        <PageHeader language={language} onLanguageChange={setLanguage} />
        <div className="loading-screen" role="status">
          <Spinner />
          <p>{t("loading")}</p>
        </div>
      </main>
    );
  return (
    <HolidayCalendar
      data={state.data}
      language={language}
      onLanguageChange={setLanguage}
    />
  );
}

createRoot(document.getElementById("root")).render(<App />);
