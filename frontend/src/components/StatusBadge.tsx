import clsx from "clsx";

export function StatusBadge({
  status,
  className,
}: {
  status: "MEETS" | "PARTIALLY_MEETS" | "DOES_NOT_MEET" | "UNKNOWN" | string;
  className?: string;
}) {
  const map: Record<string, string> = {
    MEETS: "badge badge-green",
    PARTIALLY_MEETS: "badge badge-amber",
    DOES_NOT_MEET: "badge badge-red",
    UNKNOWN: "badge badge-gray",
    LOW: "badge badge-gray",
    MEDIUM: "badge badge-amber",
    HIGH: "badge badge-red",
    CRITICAL: "badge badge-red",
    ELIGIBLE: "badge badge-green",
    INELIGIBLE: "badge badge-red",
    RECOMMENDED: "badge badge-green",
    ACCEPTABLE_WITH_CAVEATS: "badge badge-amber",
    COMPLETED: "badge badge-green",
    FAILED: "badge badge-red",
    PROCESSING: "badge badge-blue",
    UPLOADED: "badge badge-gray",
    QUEUED: "badge badge-gray",
    ACTIVE: "badge badge-blue",
    DRAFT: "badge badge-gray",
    EVALUATION: "badge badge-blue",
    CANCELLED: "badge badge-gray",
    SUBMITTED: "badge badge-blue",
    SHORTLISTED: "badge badge-purple",
    REJECTED: "badge badge-red",
    SELECTED: "badge badge-green",
    INVITED: "badge badge-gray",
  };
  return <span className={clsx(map[status] || "badge badge-gray", className)}>{status.replace(/_/g, " ")}</span>;
}
