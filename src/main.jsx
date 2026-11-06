import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Button, Card, Chip, Spinner } from "@heroui/react";
import "./styles.css";

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
const KIND = {
  public: "公共假期",
  bank: "银行假期",
  government: "政府机关假期",
  optional: "可选假期",
};
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
const weekday = (date) =>
  new Intl.DateTimeFormat("zh-CN", { weekday: "long", timeZone: "UTC" }).format(
    new Date(`${date}T00:00:00Z`),
  );
const englishMonth = (month) =>
  new Intl.DateTimeFormat("en", { month: "long", timeZone: "UTC" }).format(
    new Date(Date.UTC(2026, month - 1, 1)),
  );
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

function HolidayCalendar({ data }) {
  const [view, setView] = useState(CURRENT);
  const [selected, setSelected] = useState(
    () => new Set(data.regions.map((r) => r.id)),
  );
  const [selectedDay, setSelectedDay] = useState(null);
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
  const unavailable = active.filter((r) => !r.years.includes(year));
  const years = useMemo(() => {
    const values = data.regions.flatMap((r) => r.years);
    const min = Math.min(...values, CURRENT.year),
      max = Math.max(...values, CURRENT.year + 1);
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
  const updated = new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Singapore",
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(data.updated_at));
  const stale = Date.now() - Date.parse(data.updated_at) > 48 * 3600000;
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
      else next.add(id);
      return next;
    });
    setSelectedDay(null);
  }
  function preset(ids) {
    setSelected(new Set(ids));
    setSelectedDay(null);
  }
  let emptyMessage = "已收录地区在此期间没有假期记录。";
  if (!active.length)
    emptyMessage = "选择上方地区，即可在同一张月历中查看假期。";
  else if (unavailable.length === active.length)
    emptyMessage = "该年份的官方数据尚未收录，不代表没有假期。";
  else if (unavailable.length)
    emptyMessage = "已收录地区无假期记录；尚未收录的地区不计入此结论。";
  return (
    <main className="app-shell">
      <header className="page-header">
        <div className="brand">
          <span className="brand-mark">
            <Icon name="calendar" width="23" height="23" />
          </span>
          <span>
            HOLIDAY ATLAS<small>跨地区协作 · 官方假期月历</small>
          </span>
        </div>
        <Chip
          color="success"
          variant="soft"
          size="sm"
          className="official-chip"
        >
          <span className="live-dot" />
          <Chip.Label>官方来源</Chip.Label>
        </Chip>
      </header>
      <section className="intro">
        <div className="eyebrow">ONE CALENDAR, EVERY REGION</div>
        <h1>
          看见假期，<span>从容协作。</span>
        </h1>
        <p>把不同地区的休假节奏，放进同一张日历。</p>
      </section>
      <Card className="filter-card">
        <Card.Header className="filter-heading">
          <div className="section-heading">
            <Icon name="filter" />
            <h2>地区筛选</h2>
            <span className="muted">
              已选 {selected.size}/{regions.length}
            </span>
          </div>
          <div className="presets">
            <Button
              size="sm"
              variant="ghost"
              onPress={() => preset(regions.map((r) => r.id))}
            >
              全部
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onPress={() => preset(["MY", "MY-KUL", "HK"])}
            >
              马来西亚 / 香港
            </Button>
            <Button size="sm" variant="ghost" onPress={() => preset([])}>
              清空
            </Button>
          </div>
        </Card.Header>
        <Card.Content>
          <div className="region-options" aria-label="筛选地区，可多选">
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
                {region.name}
                {selected.has(region.id) && (
                  <Icon name="check" width="12" height="12" />
                )}
              </Button>
            ))}
          </div>
        </Card.Content>
        <Card.Footer className="filter-hint">
          可多选 · 同色标记对应同一地区 · KL 为吉隆坡，MY 为全国适用范围
        </Card.Footer>
      </Card>
      <div className="workspace">
        <Card className="calendar-card">
          <Card.Header className="calendar-toolbar">
            <div>
              <div className="eyebrow">
                {englishMonth(month).toUpperCase()} {year}
              </div>
              <h2>
                {year}
                <span>年</span> {month}
                <span>月</span>
              </h2>
            </div>
            <div className="month-actions">
              <Button
                isIconOnly
                size="sm"
                variant="ghost"
                aria-label="上个月"
                isDisabled={year === years[0] && month === 1}
                onPress={() => navigate(-1)}
              >
                <Icon name="left" />
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onPress={() => changeView(CURRENT)}
              >
                本月
              </Button>
              <Button
                isIconOnly
                size="sm"
                variant="ghost"
                aria-label="下个月"
                isDisabled={year === years.at(-1) && month === 12}
                onPress={() => navigate(1)}
              >
                <Icon name="right" />
              </Button>
            </div>
          </Card.Header>
          <Card.Content className="calendar-content">
            <div className="calendar-subnav">
              <div className="date-selects">
                <label>
                  <span className="sr-only">年份</span>
                  <select
                    aria-label="年份"
                    value={year}
                    onChange={(e) =>
                      changeView({ year: +e.target.value, month })
                    }
                  >
                    {years.map((y) => (
                      <option key={y} value={y}>
                        {y} 年
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span className="sr-only">月份</span>
                  <select
                    aria-label="月份"
                    value={month}
                    onChange={(e) =>
                      changeView({ year, month: +e.target.value })
                    }
                  >
                    {Array.from({ length: 12 }, (_, i) => (
                      <option key={i} value={i + 1}>
                        {i + 1} 月
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <span>
                {byDay.size} 个假期日 <span className="subnav-dot">·</span>{" "}
                {events.length} 项地区安排
              </span>
            </div>
            <table
              className="month-grid"
              aria-label={`${year}年${month}月地区假期`}
            >
              <thead>
                <tr>
                  {["一", "二", "三", "四", "五", "六", "日"].map((d, i) => (
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
                      const key = keyFor(year, month, day),
                        items = byDay.get(key) || [];
                      return (
                        <td key={key}>
                          <button
                            className={`calendar-day ${items.length ? "has-holidays" : ""} ${selectedDay === key ? "selected-day" : ""} ${TODAY === key ? "today" : ""}`}
                            aria-label={`${key} ${weekday(key)}，${items.length} 项地区假期，查看明细`}
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
                            <span className="cell-events">
                              {items.slice(0, 2).map((item, i) => (
                                <span
                                  className="calendar-event"
                                  style={{
                                    "--region-color": item.region.color,
                                  }}
                                  key={i}
                                >
                                  <b>
                                    {SHORT[item.region.id] || item.region.id}
                                  </b>
                                  <span>{item.name}</span>
                                </span>
                              ))}
                              {items.length > 2 && (
                                <span className="more-events">
                                  +{items.length - 2} 项
                                </span>
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
              今天
            </span>
            <span>
              <i className="holiday-key" />
              假期安排
            </span>
            <span className="legend-tip">点击日期查看明细</span>
          </Card.Footer>
        </Card>
        <section className="agenda" aria-label="假期明细">
          <div className="agenda-heading">
            <div>
              <div className="eyebrow">HOLIDAY NOTES</div>
              <h2>
                {selectedDay
                  ? `${month} 月 ${Number(selectedDay.slice(-2))} 日`
                  : "本月假期"}
                <Chip size="sm" variant="soft">
                  {visible.length}
                </Chip>
              </h2>
            </div>
            {selectedDay && (
              <Button
                size="sm"
                variant="ghost"
                onPress={() => setSelectedDay(null)}
              >
                查看整月
              </Button>
            )}
          </div>
          <div className="data-notices" role="status">
            {!active.length && <p>尚未选择地区。</p>}
            {unavailable.length > 0 && (
              <p>
                <Icon name="info" /> {unavailable.map((r) => r.name).join("、")}
                ：{year} 年官方数据尚未收录。请查阅官方来源，不能视为无假期。
              </p>
            )}
            {stale && <p>数据构建已超过 48 小时，请查阅官方最新公告。</p>}
            {(data.errors || []).map((error, i) => (
              <p key={i}>
                {error.region}：同步失败，{error.error}
              </p>
            ))}
          </div>
          {!visible.length && (
            <Card className="empty-state">
              <Icon name="calendar" width="30" height="30" />
              <h3>{active.length ? "暂无可展示的记录" : "从一个地区开始"}</h3>
              <p>{emptyMessage}</p>
            </Card>
          )}
          <div className="agenda-days">
            {[...grouped].map(([date, items]) => (
              <section key={date} className="agenda-day">
                <div className="agenda-date">
                  <strong>{Number(date.slice(-2))}</strong>
                  <span>
                    {month} 月 / {weekday(date)}
                  </span>
                  <i />
                </div>
                {items.map((event, index) => (
                  <Card
                    key={`${event.region.id}-${index}`}
                    className="holiday-card"
                    style={{ "--region-color": event.region.color }}
                  >
                    <Card.Content>
                      <div className="event-top">
                        <span className="event-region">
                          <span className="region-dot" />
                          {event.region.name}
                        </span>
                        {event.kind !== "public" && (
                          <Chip size="sm" color="warning" variant="soft">
                            {KIND[event.kind]}
                          </Chip>
                        )}
                      </div>
                      <h3>{event.name}</h3>
                      {event.name_en && event.name_en !== event.name && (
                        <p className="event-english">{event.name_en}</p>
                      )}
                      <p className="event-scope">{event.scope}</p>
                      {event.note && <p className="event-note">{event.note}</p>}
                      <SourceLink url={event.source_url}>官方依据</SourceLink>
                    </Card.Content>
                  </Card>
                ))}
              </section>
            ))}
          </div>
        </section>
      </div>
      <section className="scope-note">
        <Icon name="info" />
        <div>
          <strong>为协作计划提供参考，不替代公司休假制度。</strong>
          <p>
            各地适用人群、邦州、补休规则可能不同；银行、政府机关与可选假期已单独标注。宗教节日及临时假期以当地政府最终公告为准。
          </p>
          <p>
            可读取的官方接口自动获取；部分 PDF / 公告为人工核对快照，核对日期见下方来源说明。页面构建时间不代表所有公告已重新核对。
          </p>
        </div>
      </section>
      <details className="sources">
        <summary>
          <span>
            <Icon name="globe" />
            官方来源与收录范围
          </span>
          <span>
            {active.length} 个地区 <span className="summary-plus">＋</span>
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
                {region.name}
                <span>{region.name_en}</span>
              </h3>
              <p>{region.scope}</p>
              <p>收录年份：{region.years.join("、")}</p>
              {region.sources.map((source, i) => (
                <SourceLink key={i} url={source.url}>
                  {source.name} · {source.format}
                </SourceLink>
              ))}
              <ul>
                {(region.notes || []).map((note, i) => (
                  <li key={i}>{note}</li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      </details>
      <footer>
        <span>
          HOLIDAY ATLAS <span className="footer-divider">/</span> OFFICIAL
          SOURCES ONLY
        </span>
        <span>页面构建 {updated} · UTC+8</span>
      </footer>
    </main>
  );
}

function App() {
  const [state, setState] = useState({ data: null, error: null });
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
          throw new Error("官方假期数据格式异常");
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
      <main className="loading-screen">
        <Card className="load-card">
          <Icon name="info" width="30" height="30" />
          <h1>暂时无法载入假期</h1>
          <p>无法载入不代表没有假期，请稍后重试。</p>
          <p className="muted">{state.error}</p>
          <Button onPress={() => window.location.reload()}>重新载入</Button>
        </Card>
      </main>
    );
  if (!state.data)
    return (
      <main className="loading-screen" role="status">
        <Spinner />
        <p>正在载入官方假期月历…</p>
      </main>
    );
  return <HolidayCalendar data={state.data} />;
}

createRoot(document.getElementById("root")).render(<App />);
