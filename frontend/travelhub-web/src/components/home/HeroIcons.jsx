export function IconMapPin({ className }) {
  return (
    <svg className={className} width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#e11d48"
        d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5A2.5 2.5 0 1 1 12 6a2.5 2.5 0 0 1 0 5.5z"
      />
    </svg>
  );
}

export function IconCalendar({ className }) {
  return (
    <svg className={className} width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <rect x="3" y="5" width="18" height="16" rx="2" fill="#fff" stroke="#e2e8f0" strokeWidth="1" />
      <rect x="3" y="5" width="18" height="6" rx="2" fill="#e11d48" />
      <path stroke="#cbd5e1" strokeWidth="1" d="M3 11h18M8 5v4M16 5v4" />
      <circle cx="9" cy="15" r="1" fill="#94a3b8" />
      <circle cx="15" cy="15" r="1" fill="#94a3b8" />
    </svg>
  );
}

export function IconUsers({ className }) {
  return (
    <svg className={className} width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#2563eb"
        d="M16 11a3 3 0 1 0-3-3 3 3 0 0 0 3 3zm-8 0a3 3 0 1 0-3-3 3 3 0 0 0 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97H23v-2.5c0-2.33-4.67-3.5-7-3.5z"
      />
    </svg>
  );
}

export function IconSearch({ className }) {
  return (
    <svg className={className} width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="11" cy="11" r="7" fill="none" stroke="#fff" strokeWidth="2.2" />
      <path
        fill="none"
        stroke="#fff"
        strokeWidth="2.2"
        strokeLinecap="round"
        d="M16 16l5 5"
      />
    </svg>
  );
}
