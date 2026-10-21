import { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement> & { size?: number };

function Icon({ size = 18, children, ...rest }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...rest}
    >
      {children}
    </svg>
  );
}

export const IconDashboard = (p: IconProps) => <Icon {...p}><rect x="3" y="3" width="7" height="9" rx="1" /><rect x="14" y="3" width="7" height="5" rx="1" /><rect x="14" y="12" width="7" height="9" rx="1" /><rect x="3" y="16" width="7" height="5" rx="1" /></Icon>;
export const IconUsers = (p: IconProps) => <Icon {...p}><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20c.6-3.4 3.2-5.5 6.5-5.5s5.9 2.1 6.5 5.5" /><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8" /><path d="M18.5 14.9c1.7.7 2.8 2.4 3 5.1" /></Icon>;
export const IconDocument = (p: IconProps) => <Icon {...p}><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5" /><path d="M9 13h6M9 17h4" /></Icon>;
export const IconInbox = (p: IconProps) => <Icon {...p}><path d="M3 13l2.5-8h13L21 13" /><path d="M3 13v6a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1v-6h-5.5a2.5 2.5 0 0 1-5 0z" /></Icon>;
export const IconClock = (p: IconProps) => <Icon {...p}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></Icon>;
export const IconShield = (p: IconProps) => <Icon {...p}><path d="M12 3l8 3v6c0 4.5-3.2 7.8-8 9-4.8-1.2-8-4.5-8-9V6z" /><path d="M9 12l2 2 4-4" /></Icon>;
export const IconGear = (p: IconProps) => <Icon {...p}><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" /></Icon>;
export const IconChat = (p: IconProps) => <Icon {...p}><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.5-4.6A8 8 0 1 1 21 12z" /></Icon>;
export const IconChevronDown = (p: IconProps) => <Icon {...p}><path d="M6 9l6 6 6-6" /></Icon>;
export const IconLock = (p: IconProps) => <Icon {...p}><rect x="4.5" y="10.5" width="15" height="10" rx="2" /><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3" /></Icon>;
export const IconX = (p: IconProps) => <Icon {...p}><path d="M6 6l12 12M18 6L6 18" /></Icon>;
export const IconMinus = (p: IconProps) => <Icon {...p}><path d="M6 12h12" /></Icon>;
export const IconPlus = (p: IconProps) => <Icon {...p}><path d="M12 5v14M5 12h14" /></Icon>;
export const IconSend = (p: IconProps) => <Icon {...p}><path d="M4 12l16-8-6 16-2.5-6.5z" /><path d="M11.5 13.5L20 4" /></Icon>;
export const IconDownload = (p: IconProps) => <Icon {...p}><path d="M12 4v11" /><path d="M7 11l5 5 5-5" /><path d="M5 20h14" /></Icon>;
export const IconEye = (p: IconProps) => <Icon {...p}><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></Icon>;
export const IconTrash = (p: IconProps) => <Icon {...p}><path d="M4 7h16" /><path d="M9 7V4h6v3" /><path d="M6 7l1 13h10l1-13" /><path d="M10 11v6M14 11v6" /></Icon>;
export const IconSearch = (p: IconProps) => <Icon {...p}><circle cx="11" cy="11" r="6.5" /><path d="M20 20l-4.2-4.2" /></Icon>;
export const IconLogout = (p: IconProps) => <Icon {...p}><path d="M10 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h4" /><path d="M16 8l4 4-4 4" /><path d="M20 12H9" /></Icon>;
export const IconMenu = (p: IconProps) => <Icon {...p}><path d="M4 7h16M4 12h16M4 17h16" /></Icon>;
export const IconCheck = (p: IconProps) => <Icon {...p}><path d="M5 12.5l4.5 4.5L19 7" /></Icon>;
export const IconAlert = (p: IconProps) => <Icon {...p}><path d="M12 3l10 18H2z" /><path d="M12 10v5M12 18v.01" /></Icon>;
export const IconUpload = (p: IconProps) => <Icon {...p}><path d="M12 16V5" /><path d="M7 9l5-5 5 5" /><path d="M5 20h14" /></Icon>;
export const IconRefresh = (p: IconProps) => <Icon {...p}><path d="M20 11a8 8 0 0 0-14.5-4M4 4v4h4" /><path d="M4 13a8 8 0 0 0 14.5 4M20 20v-4h-4" /></Icon>;
export const IconNewChat = (p: IconProps) => <Icon {...p}><path d="M12 20H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v6" /><path d="M16 18h6M19 15v6" /></Icon>;
export const IconChevronLeft = (p: IconProps) => <Icon {...p}><path d="M15 6l-6 6 6 6" /></Icon>;
export const IconHistory = (p: IconProps) => <Icon {...p}><path d="M3.5 12a8.5 8.5 0 1 0 2.6-6.1L3.5 8.5" /><path d="M3.5 4v4.5H8" /><path d="M12 8v4.2l2.8 1.8" /></Icon>;
export const IconSidebar = (p: IconProps) => <Icon {...p}><rect x="3" y="4" width="18" height="16" rx="3" /><path d="M9 4v16" /></Icon>;
export const IconBuilding = (p: IconProps) => <Icon {...p}><rect x="5" y="3" width="14" height="18" rx="2" /><path d="M9 7.5h2M13 7.5h2M9 11.5h2M13 11.5h2M9 15.5h2M13 15.5h2" /></Icon>;
export const IconSpark = (p: IconProps) => <Icon {...p}><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" /><path d="M18.5 16.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z" /></Icon>;
export const IconMaximize = (p: IconProps) => <Icon {...p}><path d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7" /></Icon>;
export const IconSun = (p: IconProps) => <Icon {...p}><circle cx="12" cy="12" r="4" /><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M18.7 5.3l-1.6 1.6M6.9 17.1l-1.6 1.6" /></Icon>;
export const IconMoon = (p: IconProps) => <Icon {...p}><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" /></Icon>;
export const IconCalendar = (p: IconProps) => <Icon {...p}><rect x="3.5" y="5" width="17" height="15.5" rx="3" /><path d="M3.5 10h17M8 3v4M16 3v4" /></Icon>;
export const IconPencil = (p: IconProps) => <Icon {...p}><path d="M4 20l1-4.5L16.5 4a2 2 0 0 1 2.8 0l.7.7a2 2 0 0 1 0 2.8L8.5 19z" /><path d="M14.5 6l3.5 3.5" /></Icon>;
export const IconMail = (p: IconProps) => <Icon {...p}><rect x="3" y="5" width="18" height="14" rx="3" /><path d="M3.5 7.5l8.5 6 8.5-6" /></Icon>;
export const IconArrowRight = (p: IconProps) => <Icon {...p}><path d="M5 12h14M13 6l6 6-6 6" /></Icon>;
export const IconStop = (p: IconProps) => <Icon {...p}><rect x="6.5" y="6.5" width="11" height="11" rx="2.5" fill="currentColor" stroke="none" /></Icon>;
export const IconBarChart = (p: IconProps) => <Icon {...p}><path d="M5 20V11M12 20V4M19 20v-6" /></Icon>;
export const IconLineChart = (p: IconProps) => <Icon {...p}><path d="M3.5 17l5-6 4 3.5L20.5 6" /><path d="M16 6h4.5v4.5" /></Icon>;
