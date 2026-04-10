import { useId, useState } from "react";
import { IconChevronDown, IconStar } from "../home/HeroIcons";
import "./ResultsToolbar.css";

const FILTER_ITEMS = [
  { id: "price", labelKey: "filterPrice", icon: "money" },
  { id: "rating", labelKey: "filterRating", icon: "star" },
  { id: "amenities", labelKey: "filterAmenities", icon: null },
  { id: "map", labelKey: "filterMap", icon: null },
];

function ResultsToolbar({ copy }) {
  const sortId = useId();
  const [activeFilter, setActiveFilter] = useState("price");

  return (
    <div className="results-toolbar">
      <div className="results-toolbar__summary">
        <p className="results-toolbar__summary-lead">{copy.summaryLead}</p>
        <p className="results-toolbar__summary-meta">{copy.summaryMeta}</p>
      </div>

      <div
        className="results-toolbar__actions"
        role="toolbar"
        aria-label={copy.filtersToolbarLabel}
      >
        {FILTER_ITEMS.map(({ id, labelKey, icon }) => {
          const isActive = activeFilter === id;
          const isPriceActive = isActive && id === "price";
          const label = copy[labelKey];
          return (
            <button
              key={id}
              type="button"
              className={
                "results-toolbar__filter" +
                (isPriceActive
                  ? " results-toolbar__filter--active-solid"
                  : isActive
                    ? " results-toolbar__filter--active"
                    : "")
              }
              aria-pressed={isActive}
              onClick={() => setActiveFilter(id)}
            >
              {icon === "money" && (
                <span
                  className="results-toolbar__filter-badge results-toolbar__filter-badge--money"
                  aria-hidden="true"
                >
                  <svg
                    className="results-toolbar__money-bag"
                    viewBox="0 0 24 24"
                    width="13"
                    height="13"
                    aria-hidden="true"
                  >
                    <path
                      fill="currentColor"
                      d="M12 3C9.5 3 7.5 4.8 7 7H5c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V9c0-1.1-.9-2-2-2h-2c-.5-2.2-2.5-4-5-4zm0 2c1.66 0 3 1.34 3 3v1H9V8c0-1.66 1.34-3 3-3z"
                    />
                  </svg>
                  <span className="results-toolbar__money-sign">$</span>
                </span>
              )}
              {icon === "star" && (
                <span
                  className="results-toolbar__filter-badge results-toolbar__filter-badge--star"
                  aria-hidden="true"
                >
                  <IconStar className="results-toolbar__star-icon" />
                </span>
              )}
              <span className="results-toolbar__filter-text">{label}</span>
            </button>
          );
        })}
      </div>

      <div className="results-toolbar__sort">
        <label htmlFor={sortId} className="results-toolbar__visually-hidden">
          {copy.sortLabel}
        </label>
        <div className="results-toolbar__select-wrap">
          <select
            id={sortId}
            className="results-toolbar__select"
            name="sort"
            defaultValue="best"
          >
            <option value="best">{copy.sortBestMatch}</option>
            <option value="price-asc">{copy.sortPriceLow}</option>
            <option value="price-desc">{copy.sortPriceHigh}</option>
            <option value="rating">{copy.sortRating}</option>
          </select>
          <span className="results-toolbar__chevron" aria-hidden="true">
            <IconChevronDown className="results-toolbar__chevron-icon" />
          </span>
        </div>
      </div>
    </div>
  );
}

export default ResultsToolbar;
