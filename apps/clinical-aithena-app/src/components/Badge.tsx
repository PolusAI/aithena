import React from "react";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "destructive" | "outline";
  className?: string;
}

export const Badge = ({
  children,
  variant = "default",
  className = "",
}: BadgeProps) => {
  const baseStyles =
    "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2";

  const variants = {
    default:
      "border-transparent bg-[var(--color-primary)] text-[var(--color-primary-foreground)] hover:bg-[var(--color-primary)]/80",
    success:
      "border-transparent bg-green-500 text-white hover:bg-green-600",
    warning:
      "border-transparent bg-[var(--color-accent)] text-white hover:bg-[var(--color-accent)]/80",
    destructive:
      "border-transparent bg-red-500 text-white hover:bg-red-600",
    outline: "text-[var(--color-foreground)] border-[var(--color-border)]",
  };

  return (
    <div className={`${baseStyles} ${variants[variant]} ${className}`}>
      {children}
    </div>
  );
};

